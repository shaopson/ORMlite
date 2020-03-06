import datetime
import logging
import ormlite
from ormlite import configuration
from ormlite.db.utils import create_tables,Min,Count,Sum


logging.basicConfig(level=logging.DEBUG)

configuration.conf_db({
    "ENGINE":"ormlite.db.sqlite3",
	"NAME":"db.sqlite3",
})

configuration.set_logger(logging)
configuration.debug = True


class Order(ormlite.Model):
    price = ormlite.FloatField()
    user = ormlite.ForeignKey("User",on_delete=ormlite.CASCADE)


class User(ormlite.Model):
    id = ormlite.PrimaryKey()
    name = ormlite.CharField(max_length=50)
    sex = ormlite.CharField(max_length=1)
    age = ormlite.IntegerField()
    birthday = ormlite.DateField()



def aotu_add():
    return datetime.datetime.now()

def today():
    return datetime.datetime.now().date()

class Goods(ormlite.Model):
    number = ormlite.PrimaryKey()
    name = ormlite.CharField(max_length=100)
    dt   = ormlite.DateTimeField()
    time = ormlite.TimeFiled()
    date = ormlite.DateField()


create_tables([Order],configuration.db)
