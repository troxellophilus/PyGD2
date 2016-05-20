#!/usr/bin/python3


"""Copyright (C) 2015  Drew Troxell

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


from datetime import datetime
import logging
import random
import re
import time
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from pytz import timezone
import requests

from pygd2 import db


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
DELAY_MAX = 10


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
    return ET.fromstring(response.text)


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
        date = datetime.today()
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
        date = datetime.now() + pacific.localize(datetime.now()).utcoffset()
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


def get_color_feed(game_pk):
    """Gets color feed for a game.
    Args:
        game_pk: game_pk of game to get feed for.
    Returns:
        Parsed JSON feed.
    """
    url = "http://statsapi.mlb.com/api/v1/game/%s/feed/color.json" % str(game_pk)
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
        date = datetime(year, month, day)
    except ValueError:
        date = datetime.today()
    players_xml_urls = get_players_xml_urls(date)
    db.opendb()
    updated = []
    for url in players_xml_urls:
        players = get_player_attribs(url)
        for player in players:
            for_team, _ = db.Team.create_or_get(
                gdid=player['team_id'],
                abbrev=player['team_abbrev']
            )
            db_player, created = db.Player.create_or_get(
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
                date_modified=datetime.now()
            )
            if not created:
                db_player.gdid = player['id']
                db_player.number = player['num']
                db_player.position = player['position']
                db_player.status = player['status']
                db_player.team = for_team
                db_player.date_modified = datetime.now()
                db_player.save()
            updated.append(db_player)
    db.closedb()
    return updated


def get_player_stats(type='hitting', player_id='', year=datetime.today().year):
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
    if json == None:
        return {}
    idx_composed = 'sport_{}_composed'.format(type)
    idx_agg = 'sport_{}_agg'.format(type)
    data = json[idx_composed][idx_agg]['queryResults']
    if data['totalSize'] is '1': # TODO multi year in one request
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
    try:
        player = db.Player.get(firstname=first, lastname=last)
    except db.Player.DoesNotExist:
        LOG.error("Player not in database.")
        return None
    else:
        return player


def get_player_by_id(player_id):
    """Gets a player from the database.
    Args:
        player_id: The player's id.
    Returns:
        The Player, or None if player isn't in the database.
    """
    try:
        player = db.Player.get(gdid=player_id)
    except db.Player.DoesNotExist:
        LOG.error("Player not in database.")
        return None
    else:
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


def get_pitching_stats_by_name(first, last, year, stats=[]): # TODO default stats
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
    stats_lower = [s.lower() for s in stats]
    found_stats = {}
    for abbrev, value in player_stats.items():
        if abbrev.lower() in stats_lower:
            found_stats[abbrev.upper()] = value
    return found_stats


def get_batting_stats_by_name(first, last, year, stats=[]): # TODO default stats
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
    stats_lower = [s.lower() for s in stats]
    found_stats = {}
    for abbrev, value in player_stats.items():
        if abbrev.lower() in stats_lower:
            found_stats[abbrev.upper()] = value
    return found_stats
