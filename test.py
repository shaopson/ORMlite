import datetime
import logging
import ormlite
from ormlite import configuration
from ormlite.query import Count
from ormlite.db.utils import create_tables


logging.basicConfig(level=logging.DEBUG)
configuration.set_logger(logging)
configuration.debug = True

configuration.conf_db({
    "ENGINE":"ormlite.db.sqlite3",
    "NAME":"db.sqlite3",
})

# configuration.conf_db({
#     "ENGINE":"ormlite.db.mysql",
#     'NAME': 'ormlite',
#     'USER': 'root',
#     'PASSWORD': '123456',
#     'HOST': 'localhost',
#     'PORT': '3306',
#     'OPTIONS': {
#         'autocommit': True,
#     }
# })

class User(ormlite.Model):
    id = ormlite.PrimaryKey()
    name = ormlite.CharField(max_length=50)
    sex = ormlite.CharField(max_length=1)
    birthday = ormlite.DateField()


class Goods(ormlite.Model):
    id = ormlite.PrimaryKey()
    name = ormlite.CharField(max_length=100,default='11')
    price = ormlite.FloatField(default=0.0)
    production_time = ormlite.DateTimeField()


class Order(ormlite.Model):
    id = ormlite.PrimaryKey(null=False)
    user = ormlite.ForeignKey(User,on_delete=ormlite.CASCADE)
    goods = ormlite.ForeignKey(Goods, on_delete=ormlite.CASCADE)
    amount = ormlite.IntegerField(default=0.0)
    total = ormlite.FloatField()
    created_time = ormlite.DateTimeField(auto_now_add=True)


#create_tables([User,Goods,Order],configuration.db)

