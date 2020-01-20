import datetime
from ormlite.base import configuration
from ormlite.model import Model
from ormlite import fields
from ormlite.db.utils import create_tables,Min,Count,Sum

configuration.conf_db({
    "ENGINE":"ormlite.db.sqlite3",
	"NAME":"db.sqlite3",
})



class User(Model):
    id = fields.PrimaryKey()
    name = fields.CharField(max_length=50)
    sex = fields.CharField(max_length=1)
    age = fields.IntegerField()
    birthday = fields.DateField()
