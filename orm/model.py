
import sys
import os
import sqlite3


class Database(object):
	instance = False
	def __new__(cls,*args,**kwargs):
		if not cls.instance:
			cls.instance = super().__new__(cls)
		return cls.instance

	def __init__(self,name=''):
		self.name = name

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.name



class RecordNotExistsError(Exception):
	pass


class Utils(object):

	@staticmethod
	def sql_dict(**kwargs):
		result = []
		for k,v in kwargs.items():
			result.append("%s = %s" % (k,Utils.repr(v)))
		return ",".join(result)

	@staticmethod
	def repr(value):
		from datetime import datetime,time,date
		if isinstance(value,datetime):
			value = value.strftime('%Y-%m-%d %H:%M:%S')
		if isinstance(value,(date,time)):
			value = value.isoformat()
		if isinstance(value,str):
			return repr(value)
		if value == None:
			return 'NULL'
		return str(value)

	@staticmethod
	def get_value(obj,fields):
		result = []
		for field in fields:
			value = getattr(obj,field)
			result.append(Utils.repr(value))
		return result


class Query(object):
	db = Database()

	def __init__(self,model):
		self.model = model
		self.table = model.__table__
		self.fields = []
		for k,v in model.__mapping__.items():
			self.fields.append(k)

	def make_objects(self,datas):
		attrs = dict()
		result = []
		for data in datas:
			index = 0
			for field in self.fields:
				attrs[field] = data[index]
				index += 1
			result.append(self.model(**attrs))
		return result
			
	
	def get(self,**query):		
		condition = Utils.sql_dict(**query)
		sql = "SELECT %s FROM %s WHERE %s;" % (','.join(self.fields),self.table,condition)
		print(sql)
		conn = sqlite3.connect(self.db.name)
		cur = conn.cursor()
		data = []
		try:
			cur.execute(sql)
			data = cur.fetchall()
		finally:
			cur.close()
			conn.close()
		if not data:
			raise RecordNotExistsError('Not query this record:%s' % query)
		attrs = dict()
		for field,value in zip(self.fields,data[0]):
			attrs[field] = value
		return self.model(**attrs)

	def save(self,instance):
		value = Utils.get_value(instance,self.fields)
		value = ','.join(value)
		sql = "INSERT INTO %s (%s) VALUES (%s);" % (self.table,','.join(self.fields),value)
		print(sql)
		conn = sqlite3.connect(self.db.name)
		cur = conn.cursor()
		data = []
		try:
			cur.execute(sql)
			data = cur.rowcount
		finally:
			cur.close()
			conn.commit()
			conn.close()
		return data


	def all(self):
		sql = "SELECT %s FROM %s;" % (','.join(self.fields),self.table)
		print(sql)
		conn = sqlite3.connect(self.db.name)
		cur = conn.cursor()
		data = [] 
		try:
			cur.execute(sql)
			data = cur.fetchall()
		finally:
			cur.close()
			conn.close()
		return self.make_objects(data)

	def delete(self):
		pass


	def update(self):
		pass

	def filter(self):
		pass
		



class Field(object):
	column_type = ''

	def __init__(self,name=None,default=None,unique=False,null=True):
		self.name = name
		self.default = default
		self.unique = unique
		self.null = null

	def constraint(self):
		s = ''
		if self.default:
			s += " DEFAULT " + self._str(self.default)
		if self.unique:
			s += " UNIQUE"
		if not self.null:
			s += " NOT NULL"
		return s

	def _str(self,value):
		import datetime as dt
		if isinstance(value,(dt.date,dt.time)):
			return "\'%s\'" % value.isoformat()
		if isinstance(value,dt.datetime):
			return "\'%s\'" % value.strstime('%Y-%m-%d %H:%M:%S')
		if isinstance(value,str):
			return "\'%s\'" % value
		return str(value)

	def define(self):
		return "%s %s %s" % (self.name,self.column_type,self.constraint())

	def __repr__(self):
		return "<%s:%s>" % (self.__class__.__name__,self.name)


class PrimaryKey(Field):

	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.column_type = "INTEGER"

	def constraint(self):
		return "PRIMARY KEY AUTOINCREMENT"


class CharField(Field):

	def __init__(self,*args,max_length=100,**kwargs):
		super().__init__(*args,**kwargs)
		self.max_length = max_length
		self.column_type = "CHAR(%s)" % max_length


class IntegerField(Field):

	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.column_type = "INTEGER"


class TextField(Field):
	column_type = 'TEXT'


class DateTimeField(Field):
	column_type = "DATETIME"


class DateField(Field):
	column_type = "DATE"


class ModelMetaClass(type):

	def __new__(cls,name,bases,attrs):
		if name == 'Model':
			return type.__new__(cls,name,bases,attrs)
		mapping = {}
		for k,v in attrs.items():
			if isinstance(v,Field):
				mapping[k] = v
		has_pk = False
		for k,v in mapping.items():
			if isinstance(v,PrimaryKey):
				has_pk = True
			attrs[k] = v.default
		if not has_pk:
			mapping['id'] = PrimaryKey('id')
			attrs['id'] = None
		attrs['__mapping__'] = mapping
		attrs['__table__'] = name
		instance = type.__new__(cls,name,bases,attrs)
		instance.objects = Query(instance)
		return instance


class Model(object,metaclass=ModelMetaClass):

	def __init__(self,**kwargs):
		for k,v in kwargs.items():
			if k in self.__mapping__:
				setattr(self,k,v)
			else:
				raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__,k))

	def save(self):
		return self.objects.save(self)


def migrate(model_list,db):
	sql_create = []
	for model in model_list:
		table = model.__table__
		fields = []
		for k,v in model.__mapping__.items():
			fields.append(v.define())
		sql = "CREATE TABLE %s (%s);" % (table,','.join(fields))
		print(sql)
		sql_create.append(sql)

	with sqlite3.connect(db) as conn:
		cur = conn.cursor()
		for sql in sql_create:
			cur.execute(sql)
		cur.close()
		conn.commit()
		





