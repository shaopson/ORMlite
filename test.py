import os,sys
from ormlite import model,fields,creation
from ormlite.model import Count,Min,Sum
import ormlite

db = os.path.join(os.getcwd(),'db.sqlite3')
ormlite.Database.config(db)


class User(model.Model):
	id = fields.PrimaryKey()
	name = fields.CharField(length=50)
	sex = fields.CharField(length=20)
	age = fields.IntegerField()


class Studen(model.Model):
	name = fields.CharField(length=50,unique=True)
	sex = fields.CharField(length=20)
	age = fields.IntegerField(default='M',null=False)


class Log(model.Model):
	id = fields.PrimaryKey()
	user = fields.ForeignKey("User")
	desc = fields.CharField()


# u = User.object.get(id=5)
# log = Log.object.get(id=2)
# print(log)
# print(log.user)
# log.user = u
# print(log.user)
#print(log.test)
#creation.create_table([Log],db)
# r = User.object.all()
# print(r)

#save()
#all()
#[0] [1:2]       


