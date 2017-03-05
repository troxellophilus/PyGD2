import datetime

import pytz

from pygd2 import pygd2


class _Team(object):
    def __init__(self, abbrev, name, division, wins, losses, games_back):
        self.abbrev = abbrev
        self.name = name
        self.division = division
        self.wins = wins
        self.losses = losses
        self.games_back = games_back


class _GameState(object):
    def __init__(self, balls, strikes, outs, inning, runs, hits, errors, top, win, loss, save, nono, perfect):
        self.balls = balls
        self.strikes = strikes
        self.outs = outs
        self.inning = inning
        self.runs = runs
        self.hits = hits
        self.errors = errors
        self.top = top
        self.win = win
        self.loss = loss
        self.save = save
        self.nono = nono
        self.perfect = perfect


class _Pitcher(object):
    def __init__(self, gdid, last, first, display, era, wins, losses, saves):
        self.gdid = gdid
        self.last = last
        self.first = first
        self.display = display
        self.era = era
        self.wins = wins
        self.losses = losses
        self.saves = saves

    @classmethod
    def from_mapping(cls, pitcher):
        return cls(pitcher.get('id'),
                   pitcher.get('last_name'),
                   pitcher.get('first_name'),
                   pitcher.get('name_display_roster'),
                   None if pitcher['era'] == '-' else float(pitcher['era']),
                   int(pitcher.get('wins', 0)),
                   int(pitcher.get('losses', 0)),
                   int(pitcher.get('saves', 0)))


class _LinescoreInning(object):
    def __init__(self, inning, away_runs, home_runs):
        self.inning = inning
        self.away_runs = away_runs
        self.home_runs = home_runs


class Game(object):
    def __init__(self, gameday_id):
        self.gameday_id = gameday_id
        gid = gameday_id.split('_')
        self.gameday_url = ("http://gdx.mlb.com/components/game/mlb"
                            "/year_{}/month_{}/day_{}/gid_{}/linescore.json").format(
                                gid[0], gid[1], gid[2], gameday_id)
        self.game_type = None
        self.double_header = None
        self.location = None
        self.wrapup_link = None
        self.preview_link = None
        self.start_time_utc = None
        self.start_time_et = None
        self.home_team = None
        self.away_team = None
        self.status = None
        self.state = None
        self.linescore = None
        self.tiebreaker = None
        self.game_pk = None
        self.venue = None

    def reload(self):
        data = pygd2.get_json(self.gameday_url)['data']['game']
        self.game_type = data.get('game_type')
        self.double_header = data.get('double_header_sw') == 'Y'
        self.location = data.get('location')
        self.wrapup_link = data.get('wrapup_link')
        self.preview_link = data.get('home_preview_link')
        start_time_string = ' '.join([data['time_date'], data['ampm']])
        raw_dt = datetime.datetime.strptime(start_time_string, "%Y/%m/%d %I:%M %p")
        self.start_time_et = pytz.timezone('US/Eastern').localize(raw_dt)
        utc = pytz.timezone('utc')
        self.start_time_utc = utc.normalize(self.start_time_et.astimezone(utc))
        self.home_team = _Team(abbrev=data.get('home_name_abbrev'),
                               name=data.get('home_team_name'),
                               division=data.get('home_division'),
                               wins=int(data.get('home_win', 0)),
                               losses=int(data.get('home_loss', 0)),
                               games_back=float(0 if data.get('home_games_back', 0) == '-' else data.get('home_games_back', 0)))
        self.away_team = _Team(abbrev=data.get('away_name_abbrev'),
                               name=data.get('away_team_name'),
                               division=data.get('away_division'),
                               wins=int(data.get('away_win', 0)),
                               losses=int(data.get('away_loss', 0)),
                               games_back=float(0 if data.get('away_games_back', 0) == '-' else data.get('away_games_back', 0)))
        self.status = data.get('status')
        win = _Pitcher.from_mapping(data['winning_pitcher']) if data.get('winning_pitcher') else None
        loss = _Pitcher.from_mapping(data['losing_pitcher']) if data.get('losing_pitcher') else None
        save = _Pitcher.from_mapping(data['save_pitcher']) if data.get('save_pitcher') else None
        self.state = _GameState(balls=int(data.get('balls', 0)),
                                strikes=int(data.get('strikes', 0)),
                                outs=int(data.get('outs', 0)),
                                inning=int(data.get('inning', 0)),
                                runs=(int(data.get('away_team_runs', 0)), int(data.get('home_team_runs'), 0)),
                                hits=(int(data.get('away_team_hits', 0)), int(data.get('home_team_hits'), 0)),
                                errors=(int(data.get('away_team_errors', 0)), int(data.get('home_team_errors', 0))),
                                top=data.get('top_inning') == 'Y',
                                win=win,
                                loss=loss,
                                save=save,
                                nono=data.get('is_no_hitter') == 'Y',
                                perfect=data.get('is_perfect_game') == 'Y')
        self.linescore = [_LinescoreInning(int(l['inning'] or 0), int(l['away_inning_runs'] or 0), int(l['home_inning_runs'] or 0)) for l in data.get('linescore', [])]
        self.tiebreaker = data.get('tiebreaker_sw') == 'Y'
        self.game_pk = data.get('game_pk')
        self.venue = data.get('venue')
