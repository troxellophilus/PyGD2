import datetime
import json

import pytz


class Pitch(object):

    def __init__(self, **kwds):
        # pylint: disable=I0011,C0103
        strptime = datetime.datetime.strptime
        self.des = kwds.get('ball')
        self.des_es = kwds.get('des_es')
        self.id_ = kwds.get('id')
        self.type = kwds.get('type')
        try:
            self.tfs = pytz.utc.localize(strptime(str(kwds['tfs']), "%H%M%S")).timetz()
        except KeyError:
            self.tfs = None
        try:
            self.tfs_zulu = pytz.utc.localize(strptime(kwds['tfs_zulu'], "%Y-%m-%dT%H:%M:%SZ"))
        except KeyError:
            self.tfs_zulu = None
        self.x = kwds.get('x')
        self.y = kwds.get('y')
        self.event_num = kwds.get('event_num')
        self.sv_id = kwds.get('sv_id')
        self.play_guid = kwds.get('play_guid')
        self.start_speed = kwds.get('start_speed')
        self.end_speed = kwds.get('end_speed')
        self.sz_top = kwds.get('sz_top')
        self.sz_bot = kwds.get('sz_bot')
        self.pfx_x = kwds.get('pfx_x')
        self.pfx_z = kwds.get('pfx_z')
        self.px = kwds.get('px')
        self.pz = kwds.get('pz')
        self.x0 = kwds.get('x0')
        self.y0 = kwds.get('y0')
        self.z0 = kwds.get('z0')
        self.vx0 = kwds.get('vx0')
        self.vy0 = kwds.get('vy0')
        self.vz0 = kwds.get('vz0')
        self.ax = kwds.get('ax')
        self.ay = kwds.get('ay')
        self.az = kwds.get('az')
        self.break_y = kwds.get('break_y')
        self.break_angle = kwds.get('break_angle')
        self.break_length = kwds.get('break_length')
        self.pitch_type = kwds.get('pitch_type')
        self.type_confidence = kwds.get('type_confidence')
        self.zone = kwds.get('zone')
        self.nasty = kwds.get('nasty')
        self.spin_dir = kwds.get('spin_dir')
        self.spin_rate = kwds.get('spin_rate')
        self.cc = kwds.get('cc')
        self.mt = kwds.get('mt')


class Runner(object):

    def __init__(self, **kwds):
        # pylint: disable=I0011,C0103
        self.id = kwds.get('id')
        self.start = kwds.get('start')
        self.end = kwds.get('end')
        self.event = kwds.get('event')
        self.event_num = kwds.get('event_num')


class AtBat(object):

    def __init__(self, **kwds):
        # pylint: disable=I0011,C0103
        strptime = datetime.datetime.strptime
        self.num = kwds.get('num')
        self.b = kwds.get('b')
        self.s = kwds.get('s')
        self.o = kwds.get('o')
        try:
            self.tfs = pytz.utc.localize(strptime(str(kwds['start_tfs']), "%H%M%S")).timetz()
        except KeyError:
            self.tfs = None
        try:
            self.tfs_zulu = pytz.utc.localize(strptime(kwds['start_tfs_zulu'],
                                                       "%Y-%m-%dT%H:%M:%SZ"))
        except KeyError:
            self.tfs_zulu = None
        self.batter = kwds.get('batter')
        self.stand = kwds.get('stand')
        self.b_height = kwds.get('b_height')
        self.pitcher = kwds.get('pitcher')
        self.p_throws = kwds.get('p_throws')
        self.des = kwds.get('des')
        self.des_es = kwds.get('des_es')
        self.event_num = kwds.get('event_num')
        self.event = kwds.get('event')
        self.event_es = kwds.get('event_es')
        self.play_guid = kwds.get('play_guid')
        self.home_team_runs = kwds.get('home_team_runs')
        self.away_team_runs = kwds.get('away_team_runs')
        self.pitches = None
        self.runners = None


class Inning(object):

    def __init__(self, **kwds):
        # pylint: disable=I0011,C0103
        self.num = kwds.get('num')
        self.away_team = kwds.get('away_team')
        self.home_team = kwds.get('home_team')
        self.next = kwds.get('next')
        self.atbats = None


def _dict_lits(mapping):
    out = {}
    for key, val in mapping.items():
        try:
            out[key] = json.loads(val)
        except json.JSONDecodeError:
            out[key] = str(val)
    return out


class Game(object):

    def __init__(self, **kwds):
        # pylint: disable=I0011,C0103
        self.atBat = kwds.get('atBat')
        self.deck = kwds.get('deck')
        self.hole = kwds.get('hole')
        self.ind = kwds.get('ind')
        self.innings = None

    @classmethod
    def from_etree(cls, root):
        game = Game(**_dict_lits(root.attrib))
        innings = []
        for c_inn in root:
            inning = Inning(**_dict_lits(c_inn.attrib))
            atbats = []
            for c_ab in (c_ab for c_top in c_inn for c_ab in c_top):
                atbat = AtBat(**_dict_lits(c_ab.attrib))
                pitches = []
                runners = []
                for c_pitch in (c for c in c_ab if c.tag == 'pitch'):
                    pitch = Pitch(**_dict_lits(c_pitch.attrib))
                    pitches.append(pitch)
                for c_runner in (c for c in c_ab if c.tag == 'runner'):
                    runner = Runner(**_dict_lits(c_runner.attrib))
                    runners.append(runner)
                atbat.pitches = tuple(pitches)
                atbat.runners = tuple(runners)
                atbats.append(atbat)
            inning.atbats = tuple(atbats)
            innings.append(inning)
        game.innings = tuple(innings)
        return game
