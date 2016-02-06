from peewee import SqliteDatabase, Model, BaseModel, TextField, \
        DateTimeField, IntegerField, CharField, ForeignKeyField, CompositeKey


database = SqliteDatabase('pygd2.db')


class BaseModel(Model):
    class Meta:
        database = database


class Team(BaseModel):
    gdid = TextField(primary_key=True)
    abbrev = TextField(unique=True)


class Player(BaseModel):
    gdid = TextField(primary_key=True)
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


def open():
    database.connect()


def close():
    database.commit()
    database.close()


database.create_tables([Player, Team], safe=True)