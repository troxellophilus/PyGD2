import json

def _dict_lits(mapping):
    out = {}
    for key, val in mapping.items():
        try:
            out[key] = json.loads(val)
        except json.JSONDecodeError:
            out[key] = str(val)
    return out


class ExitVelocity(object):

    def __init__(self, **kwargs):
        kwargs = _dict_lits(kwargs)
        self.inning = kwargs.get('inning')
        self.ab_number = kwargs.get('ab_number')
        self.outs = kwargs.get('outs')
        self.batter = kwargs.get('batter')
        self.stand = kwargs.get('stand')
        self.batter_name = kwargs.get('batter_name')
        self.pitcher = kwargs.get('pitcher')
        self.p_throws = kwargs.get('p_throws')
        self.pitcher_name = kwargs.get('pitcher_name')
        self.team_batting = kwargs.get('team_batting')
        self.team_fielding = kwargs.get('team_fielding')
        self.result = kwargs.get('result')
        self.des = kwargs.get('des')
        self.events = kwargs.get('events')
        self.sv_id = kwargs.get('sv_id')
        self.strikes = kwargs.get('strikes')
        self.balls = kwargs.get('balls')
        self.pre_strikes = kwargs.get('pre_strikes')
        self.pre_balls = kwargs.get('pre_balls')
        self.call = kwargs.get('call')
        self.call_name = kwargs.get('call_name')
        self.pitch_type = kwargs.get('pitch_type')
        self.pitch_name = kwargs.get('pitch_name')
        self.description = kwargs.get('description')
        self.balls_and_strikes = kwargs.get('balls_and_strikes')
        self.start_speed = kwargs.get('start_speed')
        self.end_speed = kwargs.get('end_speed')
        self.sz_top = kwargs.get('sz_top')
        self.sz_bot = kwargs.get('sz_bot')
        self.px = kwargs.get('px')
        self.pz = kwargs.get('pz')
        self.x0 = kwargs.get('x0')
        self.z0 = kwargs.get('z0')
        self.hit_speed = kwargs.get('hit_speed')
        self.hit_distance = kwargs.get('hit_distance')
        self.hit_angle = kwargs.get('hit_angle')
        self.is_bip_out = kwargs.get('is_bip_out')
        self.pitch_number = kwargs.get('pitch_number')
        self.hc_x = kwargs.get('hc_x')
        self.hc_y = kwargs.get('hc_y')
        self.player_total_pitches = kwargs.get('player_total_pitches')
        self.player_total_pitches_pitch_types = kwargs.get('player_total_pitches_pitch_types')
        self.game_total_pitches = kwargs.get('game_total_pitches')
        self.rowId = kwargs.get('rowId')
        self.game_pk = kwargs.get('game_pk')
        self.play_id = kwargs.get('play_id')
        self.xba = kwargs.get('xba')
        self.result_table = kwargs.get('result_table')
