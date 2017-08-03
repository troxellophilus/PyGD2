import datetime

import sssorm


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


class BaseModel(sssorm.Model):
    pass


BaseModel.connect_database('pygd2.db')


class Team(BaseModel):
    gdid = str
    abbrev = str

    def __init__(self, gdid, abbrev, **kwds):
        super().__init__(gdid=gdid, abbrev=abbrev, **kwds)


class Player(BaseModel):
    gdid = str
    firstname = str
    lastname = str
    number = int
    boxname = str
    throws = str
    bats = str
    position = str
    status = str
    team_idx = int
    date_modified = datetime.datetime

    def __init__(self, gdid, firstname, lastname, number, boxname, throws, bats,
                 position, status, team, date_modified=utc_now, **kwds):
        super().__init__(gdid=gdid, firstname=firstname, lastname=lastname,
                         number=number, boxname=boxname, throws=throws, bats=bats,
                         position=position, status=status, team_idx=int(team or 0),
                         date_modified=date_modified, **kwds)

    @property
    def team(self):
        return self.get_by_index(self.team_idx)

    @team.setter
    def team(self, team):
        self.team_idx = team.idx
