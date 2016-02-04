from peewee import SqliteDatabase, Model, BaseModel, TextField, DateTimeField


database = SqliteDatabase('pygd2.db')


class BaseModel(Model):
    class Meta:
        database = database


class Player(BaseModel):
    firstname = TextField()
    lastname = TextField()
    gdid = TextField(unique=True)
    number = IntegerField(index=True)
    boxname = TextField()
    throws = CharField(index=True)
    bats = CharField(index=True)
    position = CharField(index=True)
    status = CharField()
    team = ForeignKeyField(Team, related_name='players')
    date_modified = DateTimeField()
    
    class Meta:
        primary_key = CompositeKey('lastname', 'firstname')


class Team(BaseModel):
    gdid = TextField(unique=True)
    abbrev = TextField(unique=True)


def open():
    database.connect()


def close():
    database.commit()
    database.close()


database.create_tables([Player], safe=True)