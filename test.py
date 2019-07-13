import os,sys
from ormlite import model,fields,creation
from ormlite.model import Count,Min,Sum
import ormlite


db = os.path.join(os.getcwd(),'db.sqlite3')
ormlite.Database.config(db)


class User(model.Model):
	name = fields.CharField(length=50)
	email = fields.CharField(length=50)
	pwd = fields.CharField(length=20)


#creation.create_table([User],db)
# u = User(name='shao',email='shaopson@outlook.com',pwd='1234')
# u.save()
us = User.object.get(id=11)
print(us.name)
us.name = 'shao'
us.save()





