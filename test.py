import os,sys
from ormlite import model,fields,creation
from ormlite.model import Count,Min,Sum
import ormlite


db = os.path.join(os.getcwd(),'db.sqlite3')
ormlite.Database.config(db)


class User(model.Model):
	def pwd_check(value):
		print(value)
		return "pwd%s" % value
	name = fields.CharField(length=50)
	email = fields.CharField(length=50)
	pwd = fields.CharField(length=20,auto=pwd_check)


#creation.create_table([User],db)
# u = User(name='shao',email='shaopson@outlook.com',pwd='1234')
# u.save()
us = User.object.query(name='shao')
print(us)




