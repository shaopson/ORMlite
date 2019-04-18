import os
from orm import model


class User(model.Model):
	id = model.PrimaryKey('id')
	name = model.CharField('name',max_length=50)
	sex = model.CharField('sex',max_length=20)
	age = model.IntegerField('age')


class Studen(model.Model):
	name = model.CharField('name',max_length=50,unique=True)
	sex = model.CharField('sex',max_length=20)
	age = model.IntegerField('age',default='M',null=False)


db = os.path.join(os.getcwd(),'db.sqlite3')

model.Database(db)

u = User.objects.all()
print(u)
#model.migrate((Studen,),db) 