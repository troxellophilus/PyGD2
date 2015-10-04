#!/usr/bin/python3

import sqlite3
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup

class PyGd2(object):
    def __init__(self):
        self.GD_PREFIX = "http://gd2.mlb.com/components/game/mlb/"
        self.GD_DATE_FMT = "year_{}/month_{:02d}/day_{:02d}/"
        self.STAT_FMT = "http://m.mlb.com/lookup/json/named.sport_hitting_composed.bam?game_type=%27R%27&league_list_id=%27mlb%27&sort_by=%27season_asc%27&player_id={}&sport_hitting_composed.season={}"

        self.db = sqlite3.connect('pygd2.db')
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()

    def update_players(self):
        # update the database players, only run every so often
        for pname, pid in self.__get_players().items():
            self.__upsert_player(pname, pid)
        self.db.commit()

    def __get_players(self):
        players = {} # to be filled w/ player_name -> player_id mappings
        # build the gd2 date dir url and request its source
        today = datetime.today()
        gd_date = self.GD_DATE_FMT.format(today.year, today.month, today.day)
        print(self.GD_PREFIX + gd_date)
        response = requests.get(self.GD_PREFIX + gd_date)

        # parse the gd2 date dir src for gid dirs, process players.xml for each
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            print(href)
            if href.startswith("gid_"):
                xml = self.GD_PREFIX + gd_date + href + "players.xml"
                print(xml)
                players.update(self.__process_players_xml(xml))

        # return as dictionary
        return players

    def __process_players_xml(self, url):
        players = {} # to be filled w/ player_name -> player_id mappings
        response = requests.get(url)
        if response.status_code != requests.codes.ok:
            return {}
        root = ET.fromstring(response.content)
        for player in root.iter('player'):
            print(player.attrib)
            name = "{} {}".format(player.attrib['first'], player.attrib['last'])
            players[name] = player.attrib['id']
        return players

    def __upsert_player(self, pname, pid):
        query = "INSERT OR IGNORE INTO players VALUES (?, ?)"
        self.cursor.execute(query, (pname, pid))
        query = "UPDATE players SET id=? WHERE name=?"
        self.cursor.execute(query, (pid, pname))

    def get_stats(self, player_name, year, stats = []):
        result = {}
        player_id = self.__get_player_id(player_name)
        raw = self.__get_player_stats(player_id, year)
        data = raw['sport_hitting_composed']['sport_hitting_agg']['queryResults']['row'] # TODO grab career and projected too
        season = {}
        if isinstance(data, list):
            for group in data:
                if int(group['season']) == int(year):
                    season = group
        elif isinstance(data, dict):
            season = data
        else:
            return result
        stats = [x.lower for x in stats]
        for key, value in season.items():
            if key.lower in stats:
                result[key] = value
        return result

    def get_formatted_stats(self, player_name, year, stats = []):
        return

    def __get_player_id(self, player_name):
        query = "SELECT * FROM players WHERE name=?"
        row = self.cursor.execute(query, (player_name,)).fetchone()
        return row['id']

    def __get_player_stats(self, player_id, year):
        response = requests.get(self.STAT_FMT.format(player_id, year))
        if response.status_code != requests.codes.ok:
            return
        return response.json()


def main():
    gd = PyGd2()
    gd.update_players()

    print(gd.get_stats('Andre Ethier', 2014, ["hr", "gidp", "avg", "slg"]))
    print(gd.get_stats('Andre Ethier', 2015, ["hr", "gidp", "avg", "slg"]))

if __name__ == '__main__':
    main()
