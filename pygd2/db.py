from peewee import Model
from peewee import SqliteDatabase
from peewee import TextField
from peewee import CharField
from peewee import ForeignKeyField
from peewee import DateTimeField


database = SqliteDatabase('pygd2.db')


class BaseModel(Model):
    class Meta:
        database = database


class Team(BaseModel):
    gdid = TextField(index=True)
    abbrev = TextField(unique=True)


class Player(BaseModel):
    gdid = TextField(index=True)
    firstname = TextField(index=True)
    lastname = TextField(index=True)
    number = CharField()
    boxname = TextField(index=True)
    throws = CharField()
    bats = CharField()
    position = CharField(index=True)
    status = CharField()
    team = ForeignKeyField(Team, related_name='players')
    date_modified = DateTimeField()


def opendb():
    database.connect()


def closedb():
    database.commit()
    database.close()


database.create_tables([Player, Team], safe=True)