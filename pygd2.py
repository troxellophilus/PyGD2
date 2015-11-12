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

import sqlite3
import requests
from datetime import datetime
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

class PyGd2(object):
    def __init__(self):
        self.GD_PREFIX = "http://gd2.mlb.com/components/game/mlb/"
        self.GD_DATE_FMT = "year_{}/month_{:02d}/day_{:02d}/"
        self.STAT_FMT = "http://m.mlb.com/lookup/json/named.sport_{}_composed.bam?game_type=%27R%27&league_list_id=%27mlb%27&sort_by=%27season_asc%27&player_id={}&sport_hitting_composed.season={}"

        self.db = sqlite3.connect('pygd2.db')
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()

    def update_players(self, date):
        # update the database players, only run every so often
        for pname, pid in self.__get_players(date).items():
            self.__upsert_player(pname, pid)
        self.db.commit()

    def __get_players(self, today):
        players = {} # to be filled w/ player_name -> player_id mappings
        # build the gd2 date dir url and request its source
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
        self.cursor.execute(query, (pname.lower(), pid))
        query = "UPDATE players SET id=? WHERE name=?"
        self.cursor.execute(query, (pid, pname.lower()))

    def __process_data(self, data, year, stats):
        buf = {}
        res = {}
        if isinstance(data, list):
            for group in data:
                if int(group['season']) == int(year):
                    buf = group
        elif isinstance(data, dict):
            buf = data
        else:
            return res
        for key, value in buf.items():
            if key.lower() in stats:
                res[key] = value
        return res

    def get_stats(self, player_name, year, stats):
        result = {}
        player_id = self.__get_player_id(player_name.lower())
        if not player_id:
            print("Could not find player id.")
            return result
        raw_h, raw_p = self.__get_player_stats(player_id, year)
        data_h = raw_h['sport_hitting_composed']['sport_hitting_agg']['queryResults'] # TODO grab career and projected too
        data_p = raw_p['sport_pitching_composed']['sport_pitching_agg']['queryResults']
        stats = [x.lower() for x in stats]
        if 'row' in data_h.keys():
            season_h = self.__process_data(data_h['row'], year, stats)
        else:
            season_h = {}
        if 'row' in data_p.keys():
            season_p = self.__process_data(data_p['row'], year, stats)
        else:
            season_p = {}
        return season_h, season_p

    def __get_player_id(self, player_name):
        query = "SELECT * FROM players WHERE name=?"
        row = self.cursor.execute(query, (player_name,)).fetchone()
        if row:
            return row['id']
        return False

    def __get_player_stats(self, player_id, year):
        response = requests.get(self.STAT_FMT.format("hitting", player_id, year))
        if response.status_code != requests.codes.ok:
            return
        hitting = response.json()
        response = requests.get(self.STAT_FMT.format("pitching", player_id, year))
        if response.status_code != requests.codes.ok:
            return
        pitching = response.json()
        return hitting, pitching


def main():
    gd = PyGd2()

    print("Andre Ethier 2015: " + str(gd.get_stats('Andre Ethier', 2015, ["hr", "gidp", "avg", "slg"])))
    print("Clayton Kershaw 2015: " + str(gd.get_stats('Clayton Kershaw', 2015, ["k", "whip", "avg", "era"])))

if __name__ == '__main__':
    main()
