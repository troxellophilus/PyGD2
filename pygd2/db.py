import datetime

import sssorm

sssorm.connect_database('pygd2.db')


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


class Team(sssorm.Model):
    gdid = str
    abbrev = str

    def __init__(self, gdid, abbrev, **kwds):
        super().__init__(gdid=gdid, abbrev=abbrev, **kwds)


class Player(sssorm.Model):
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
