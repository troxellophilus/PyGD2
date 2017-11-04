#!/usr/bin/python3
"""MIT License

Copyright (c) 2017 Drew Troxell

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

PyGD2
"""

from collections import OrderedDict
import datetime
import logging
import os.path
import random
import re
import sqlite3
import time
import defusedxml.ElementTree as ElementTree

from bs4 import BeautifulSoup
from pytz import timezone
import requests
import yaml

from pygd2 import db
from pygd2 import linescore
from pygd2 import inning
from pygd2 import gamefeed

# Configure logger
LOG_FMT = '%(levelname)s %(asctime)s %(module)s <%(lineno)d> %(message)s'
logging.basicConfig(format=LOG_FMT)
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

# Define MLB URL formatting strings
GD_URL_PRE = "http://gd2.mlb.com/components/game/mlb/"
GD_DATE_FMT = "year_{}/month_{:02}/day_{:02d}/"

M_URL_PRE = "http://m.mlb.com/lookup/json/"
M_STAT_FMT = "named.sport_{}_composed.bam?player_id={}&game_type=%27R%27&league_list_id=%27mlb%27&season={}"

# Set randomized delay range in seconds
DELAY_MIN = 0.5
DELAY_MAX = 5


def delay_fuzzy():
    """Be kind."""
    length = random.uniform(DELAY_MIN, DELAY_MAX)
    time.sleep(length)


def get_xml(url):
    """Gets XML from a URL.
    Args:
        url: URL where the xml is.
    Returns:
        ElementTree of the XML file, or None
    """
    delay_fuzzy()
    LOG.debug("Request to xml URL: %s", url)
    response = requests.get(url)
    if response.status_code != requests.codes.ok:
        LOG.error("Request to %s: status %s", url, response.status_code)
        return None
    return ElementTree.fromstring(response.text)


def get_json(url):
    """Gets JSON from a url.
    Args:
        url: URL where the JSON is.
    Returns:
        json of the JSON response, or none.
    """
    delay_fuzzy()
    LOG.debug("Request to json URL: %s", url)
    response = requests.get(url)
    if response.status_code != requests.codes.ok:
        LOG.error("Request to %s: status %s", url, response.status_code)
        return None
    LOG.debug("Received data: %s", response.text[:100])
    if len(response.text) == 0:
        return {}
    return response.json()


def get_soup(url):
    """Returns HTML soup from a url.
    Args:
        url: URL where the soup is.
    Returns:
        BeautifulSoup of the HTML file, or None
    """
    delay_fuzzy()
    response = requests.get(url)
    LOG.debug("Request to html URL: %s", url)
    if response.status_code != requests.codes.ok:
        LOG.error("Request to %s: status %s", url, response.status_code)
        return None
    return BeautifulSoup(response.text, 'html.parser')


def get_players_xml_urls(date):
    """Gets the URLs of the players.xml files for a given date.
    Args:
        date: Date to get players.xml files from (today if empty).
    Returns:
        List of players.xml urls.
    """
    if date is None:
        date = datetime.datetime.today()
    gd_date = GD_DATE_FMT.format(date.year, date.month, date.day)
    soup = get_soup(GD_URL_PRE + gd_date)
    if soup is None:
        return []
    players = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href.startswith("gid_"):
            xml_url = GD_URL_PRE + gd_date + href + "players.xml"
            players.append(xml_url)
    return players


def game(gameday_id):
    return linescore.Game(gameday_id)


def list_game_ids(date):
    gd_date = GD_DATE_FMT.format(date.year, date.month, date.day)
    soup = get_soup(GD_URL_PRE + gd_date)
    if soup is None:
        return []
    games = []
    regex = r"gid_(\d+_\d+_\d+_(\w+)mlb_(\w+)mlb_1/)"
    for link in soup.find_all('a'):
        href = link.get('href')
        res = re.match(regex, href)
        if res:
            gameday_id = res.group(1).rstrip('/')
            games.append(gameday_id)
    return games


def list_games(date, team_code=None):
    gd_date = GD_DATE_FMT.format(date.year, date.month, date.day)
    soup = get_soup(GD_URL_PRE + gd_date)
    if soup is None:
        return []
    games = []
    regex = r"gid_(\d+_\d+_\d+_(\w+)mlb_(\w+)mlb_1/)"
    for link in soup.find_all('a'):
        href = link.get('href')
        res = re.match(regex, href)
        if res and (not team_code or (team_code.lower() in res.group(2) or team_code.lower() in res.group(3))):
            gameday_id = res.group(1).rstrip('/')
            games.append(game(gameday_id))
    return games


def get_game_attribs(date, team):
    """Gets game.xml attributes for a date and team.
    Args:
        date: Date to run against.
        team: Team abbreviation.
    Returns:
        List of game_attribs
    """
    if date is None:
        pacific = timezone('US/Pacific')
        date = datetime.datetime.now() + pacific.localize(
            datetime.datetime.now()).utcoffset()
    gd_date = GD_DATE_FMT.format(date.year, date.month, date.day)
    soup = get_soup(GD_URL_PRE + gd_date)
    if soup is None:
        return []
    game_attribs = []
    regex = r"gid_\d+_\d+_\d+_(\w+)mlb_(\w+)mlb_1/"
    for link in soup.find_all('a'):
        href = link.get('href')
        res = re.match(regex, href)
        if res and (team in res.group(1) or team in res.group(2)):
            xml_url = GD_URL_PRE + gd_date + href + "game.xml"
            xml = get_xml(xml_url)
            if xml:
                game_attribs.append(xml.attrib)
    return game_attribs


def get_game_details(year, month, day):
    gd_date = GD_DATE_FMT.format(year, month, day)
    soup = get_soup(GD_URL_PRE + gd_date)
    if soup is None:
        return []
    game_details = []
    regex = r"gid_\d+_\d+_\d+_(\w+)mlb_(\w+)mlb_1/"
    for link in soup.find_all('a'):
        href = link.get('href')
        res = re.match(regex, href)
        if res:
            json_url = GD_URL_PRE + gd_date + href + "linescore.json"
            data = get_json(json_url)
            if data:
                game_details.append(data['data']['game'])
    return game_details


def get_color_feed(game_pk):
    """Gets color feed for a game.
    Args:
        game_pk: game_pk of game to get feed for.
    Returns:
        Parsed JSON feed.
    """
    url = "http://statsapi.mlb.com/api/v1/game/%s/feed/color.json" % str(
        game_pk)
    return get_json(url)


def get_player_attribs(url):
    """Gets a list of player attribute dicts from a players.xml file.
    Args:
        url: URL of a players.xml file.
    Returns:
        List of player attribute dicts.
    """
    xml = get_xml(url)
    if xml is None:
        return []
    return [player.attrib for player in xml.iter('player')]


def update_gameday_ids(year, month, day):
    """Updates the database players table w/ gameday ids from a given date.
    Args:
        date: Date to get gameday ids from (today if empty).
    Returns:
        List of the player objects updated in the database.
    """
    date = None
    try:
        date = datetime.datetime(year, month, day)
    except ValueError:
        date = datetime.datetime.today()
    players_xml_urls = get_players_xml_urls(date)
    updated = []
    for url in players_xml_urls:
        players = get_player_attribs(url)
        for player in players:
            try:
                for_team = db.Team.get_one(gdid=player['team_id'])
            except sqlite3.OperationalError as err:
                if 'no such table' in str(err):
                    for_team = None
                else:
                    raise err
            if not for_team:
                for_team = db.Team(gdid=player['team_id'], abbrev=player['team_abbrev'])
                for_team.create()
            try:
                db_player = db.Player.get_one(gdid=player['id'])
            except sqlite3.OperationalError as err:
                if 'no such table' in str(err):
                    db_player = None
                else:
                    raise err
            if not db_player:
                db_player = db.Player(
                    firstname=player['first'],
                    lastname=player['last'],
                    gdid=player['id'],
                    number=player['num'],
                    boxname=player['boxname'],
                    throws=player['rl'],
                    bats=player['bats'],
                    position=player['position'],
                    status=player['status'],
                    team=for_team,
                    date_modified=datetime.datetime.now())
                db_player.create()
            else:
                db_player.gdid = player['id']
                db_player.number = player['num']
                db_player.position = player['position']
                db_player.status = player['status']
                db_player.team = for_team
                db_player.date_modified = datetime.datetime.now(datetime.timezone.utc)
                db_player.update()
            updated.append(db_player)
    return updated


def get_player_stats(type='hitting',
                     player_id='',
                     year=datetime.datetime.today().year):
    """Gets the player's stats for a year.
    Args:
        type: String type of stats (hitting or pitching)
        player_id: Gameday id of the player.
        year: Season to get stats from
    Returns:
        Dictionary of form {"stat_abbrev":"value"} with the stats.
    """
    url = M_URL_PRE + M_STAT_FMT.format(type, player_id, year)
    json = get_json(url)
    if json is None:
        return {}
    idx_composed = 'sport_{}_composed'.format(type)
    idx_agg = 'sport_{}_agg'.format(type)
    data = json[idx_composed][idx_agg]['queryResults']
    if data['totalSize'] is '1':  # TODO multi year in one request
        return data['row']
    return {}


def get_player_by_name(first, last):
    """Gets a player from the database.
    Args:
        first: The player's first name.
        last: The player's last name (Scott Van Slyke -> last="Van Slyke")
    Returns:
        The Player, or None if player isn't in the database.
    """
    player = db.Player.get_one(firstname=first, lastname=last)
    if not player:
        LOG.warning(
            "Player not in database. Updating gameday ids and retrying.")
        tdy = datetime.datetime.today()
        update_gameday_ids(tdy.year, tdy.month, tdy.day)
        player = db.Player.get_one(firstname=first, lastname=last)
        if not player:
            LOG.error("Player not in database.")
            return None
    LOG.info("Retrieved player: %s",
             ' '.join([player.firstname, player.lastname]))
    return player


def get_player_by_id(player_id):
    """Gets a player from the database.
    Args:
        player_id: The player's id.
    Returns:
        The Player, or None if player isn't in the database.
    """
    player = db.Player.get_one(gdid=player_id)
    if not player:
        LOG.warning(
            "Player not in database. Updating gameday ids and retrying.")
        tdy = datetime.datetime.today()
        update_gameday_ids(tdy.year, tdy.month, tdy.day)
        player = db.Player.get_one(gdid=player_id)
        if not player:
            LOG.error("Player not in database.")
            return None
    return player


def get_player_stats_by_name(first, last, year):
    """Gets player stats for a year.
    Args:
        first: Player's first name.
        last: Player's last name (Scott Van Slyke -> last="Van Slyke")
        year: Season to get stats for.
    Returns:
        Dictionary of form {"stat_abbrev":"value"}
    """
    player = get_player_by_name(first, last)
    if player is None:
        return {}
    if player.position is 'P':
        return get_player_stats('pitching', player.gdid, year)
    return get_player_stats('hitting', player.gdid, year)


def get_pitching_stats_by_name(first, last, year,
                               stats=None):  # TODO default stats
    """Gets a player's pitching stats by name.
    Args:
        first: First name of the player.
        last: Last name of the player (Scott Van Slyke -> last="Van Slyke")
        year: Season to get stats from.
        stats: List of stat abbreviations.
    Returns:
        Dictionary of form {"stat_abbrev":"value"}
    """
    player = get_player_by_name(first, last)
    if player is None:
        return {}
    player_stats = get_player_stats('pitching', player.gdid, year)
    if not stats:
        stats = []
    stats_lower = [s.lower() for s in stats]
    found_stats = OrderedDict()
    for stat in stats_lower:
        if stat in player_stats:
            found_stats[stat.upper()] = player_stats[stat]
    return found_stats


def get_batting_stats_by_name(first, last, year,
                              stats=[]):  # TODO default stats
    """Gets a player's hitting stats by name.
    Args:
        first: First name of the player.
        last: Last name of the player (Scott Van Slyke -> last="Van Slyke")
        year: Season to get stats from.
        stats: List of stat abbreviations.
    Returns:
        Dictionary of form {"stat_abbrev":"value"}
    """
    player = get_player_by_name(first, last)
    if player is None:
        return {}
    player_stats = get_player_stats('hitting', player.gdid, year)
    if not stats:
        stats = []
    stats_lower = [s.lower() for s in stats]
    found_stats = OrderedDict()
    for stat in stats_lower:
        if stat in player_stats:
            found_stats[stat.upper()] = player_stats[stat]
    return found_stats


def _build_gameday_url(game_id, *args):
    date_path = "year_{}/month_{}/day_{}".format(*game_id.split('_')[:3])
    return '/'.join((GD_URL_PRE, date_path, 'gid_' + game_id, '/'.join(args)))


def innings_all(game_id):
    url = _build_gameday_url(game_id, 'inning', 'inning_all.xml')
    xml = get_xml(url)
    return inning.Game.from_etree(xml)


def game_feed(game_pk):
    url = "https://baseballsavant.mlb.com/gf?game_pk=%s" % game_pk
    data = get_json(url)['exit_velocity']
    out = []
    for mapping in data:
        out.append(gamefeed.ExitVelocity(**mapping))
    return out


class MLBInfo(object):

    def __init__(self, al_info, nl_info):
        self.national = nl_info
        self.american = al_info


class LeagueInfo(object):

    def __init__(self, name, divisions):
        self.name = name
        self.divisions = divisions


class DivisionInfo(object):

    def __init__(self, name, league, id, teams):
        self.name = name
        self.league = league
        self.gdid = id
        self.teams = teams


class TeamInfo(object):

    def __init__(self, name, city, league, division, code, file_code, id, names):
        self.name = name
        self.city = city
        self.league = league
        self.division = division
        self.code = code
        self.file_code = file_code
        self.gdid = id
        self.names = names


def mlb_info():
    with open(os.path.join(os.path.dirname(__file__), '../contrib/mlb.yml')) as mlbfp:
        mlb = yaml.load(mlbfp.read())
    return MLBInfo(mlb['AL'], mlb['NL'])


def league_info(league):
    mlb = mlb_info()
    if league.lower() == 'american' or league.lower() == 'al':
        return mlb.american
    elif league.lower() == 'national' or league.lower() == 'nl':
        return mlb.national
    else:
        raise ValueError("League %s not found." % league)


def division_info(league, division):
    league = league_info(league)
    if division.lower() == 'east':
        return league.divisions['East']
    elif division.lower() == 'central':
        return league.divisions['Central']
    elif division.lower() == 'west':
        return league.divisions['West']
    else:
        raise ValueError("Division %s not found." % division)


def team_info(team_name):
    mlb = mlb_info()
    for league in [mlb.american, mlb.national]:
        for division in league.divisions.values():
            for team in division.teams.values():
                if team_name.lower() == team.name.lower():
                    return team
    raise ValueError("Team %s not found." % team_name)
