
import sys
import os
import sqlite3


### database ###

db_config = {
	'name':None
}


class Database(object):

	# instance = None

	# def __new__(*args,**kwargs):
	# 	if cls.instance in None:
	# 		cls.instance = super().__new__(*args,**kwargs)
	# 	return cls.instance

	def __init__(self,db = None):
		self.db = db or db_config
		self.connect = None
		self.cursor = None
		self.connector = sqlite3.connect

	def __enter__(self):
		self.connect = self.connector(self.db['name'])
		self.cursor = self.connect.cursor()
		return self.cursor

	def __exit__(self,exc_type,exc_instance,traceback):
		if not exc_instance:
			self.connect.commit()
		self.connect.close()


### Exception ###

class RecordNotExistsError(Exception):
	pass

class MultiRecordError(Exception):
	pass





class Utils(object):

	@staticmethod
	def dumps_dict(**kwargs):
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
	def loads_datetime(value):
		pass

	@staticmethod
	def get_attrs(obj,attrs):
		result = []
		for attr in attrs:
			value = getattr(obj,atr)
			result.append(Utils.repr(value))
		return result


class Query(object):

	def __init__(self,model,fields=None,**kwargs):
		self.model = model
		self.table = model.__table__
		self.fields = fields or []
		self.where = kwargs.get('where',None)
		self.alias = kwargs.get('alias',{})
		self.distinct = kwargs.get('distinct',False)
		self.orderby = kwargs.get('orderby',[])
		self.limit = kwargs.get('limit',None)
		self.sql = ''
		self.cache = None
		self.result = []

	def as_sql(self):
		sql = ['SELECT']
		if self.distinct:
			sql.append("DISTINCT")
		if self.alias:
			alias = ("%s AS %s " % (k,v) for k,v in self.alias.items())
			self.fields.extend(alias)
		sql.append(', '.join(self.fields))
		sql.append('FROM')
		sql.append(self.table)
		if self.where:
			sql.append("WHERE %s" % self.where)
		if self.orderby:
			sql.append("ORDER BY %s" % ', '.join(self.orderby))
		if self.limit:
			if isinstance(self.limit,slice):
				start = self.limit.start or 0
				length = self.limit.stop
				sql.append("LIMIT %s OFFSET %s" % (length,start))
			elif isinstance(self.limit,int):
				sql.append("LIMIT 1 OFFSET %s" % self.limit)
		self.sql = ' '.join(sql) + ';'
		return self.sql

	def execute(self,sql = None):
		sql = sql or self.as_sql()
		print(sql)
		with Database() as conn:
			conn.execute(sql)
			self.cache = conn.fetchall()
		self._make_objects()
		return self.result

	def _make_objects(self):
		attrs = {}
		self.result = []
		for values in self.cache:
			for attr,value in zip(self.fields,values):
				attrs[attr] = value
			self.result.append(self.model(**attrs))
		return self.result

	def copy(self):
		new = self.__class__(self.model,self.fields)
		new.where = self.where
		new.alias = self.alias.copy()
		new.distinct = self.distinct
		new.orderby = self.orderby[:]
		new.limit = self.limit
		return new

	def __getitem__(self,value):
		if not isinstance(value,(slice,int)):
			raise TypeError("Query object must be integers or slices")
		if self.cache:
			return list(self.result)[value]
		new = self.copy()
		new.limit = value
		new.execute()
		if isinstance(value,int):
			return new.result[0] if new.result else []
		return new.result[value]

	def __bool__(self):
		if self.cache is None:	
			self.execute()
		return bool(self.cache)

	def __iter__(self):
		if self.cache is None:
			self.execute()
		return iter(self.result)

	def __len__(self):
		if self.cache is None:
			self.execute()
		return len(self.result)

	def __or__(self,other):
		new = self.copy()
		if new.where:
			new.where = new.where + " AND " + other.where
		else:
			new.where = other.where
		return new

	def __and__(self,other):
		new = self.copy()
		if self.where:
			self.where = self.where + " OR " + other.where
		else:
			self.where = other.where
		return self

	def __str__(self):
		if self.cache is None:
			self.execute()
		return "<Query: %r>" % self.result

	def count(self):
		if self.cache is None:
			self.execute()
		return len(self.cache)

	def order_by(self,*fields):
		new = self.copy()
		new.orderby.extend(fields)
		return new

	def values(self,*fields):
		new = self.copy()
		new.fields = fields
		new.execute()
		return new.cache

	def exclude(self,**query):
		pass


class Insert():

	def __init__(self,table,fields,value):
		self.table = table
		self.fields = fields
		self.value = value
		self.sql = ''

	def as_sql(self):
		fields = ', '.join(self.fields)
		value = ', '.join('?' * len(self.value))
		sql = "INSERT INTO %s (%s) VALUES (%s);" % (self.table,fields,value)
		self.sql = sql 
		return self.sql

	def __str__(self):
		return self.sql or self.as_sql()

class Update():

	def __init__(self,table,fields,value,where):
		self.table = table
		self.fields = fields
		self.value = value
		self.where = where
		self.sql = ''

	def as_sql(self):
		sql = "UPDATE %s SET %s WHERE %s;"
		fields = ["%s = ?" % f for f in self.fields]
		sql = sql % (self.table,', '.join(fields),self.where)
		self.sql = sql
		return self.sql

	def __str__(self):
		return self.sql or self.as_sql()

class Delete():

	def __init__(self,table,where):
		self.table = table
		self.where = where
		self.sql = ''

	def as_sql(self):
		self.sql = "DELETE FROM %s WHERE %s" % (self.table,self.where)
		return self.sql

	def __str__(self):
		return self.sql or self.as_sql()



class Converter(object):

	db = Database

	def __init__(self,model,instance = None):
		self.model = model
		self.table = model.__table__
		self._instance = instance
		self.fields = []
		for k,v in model.__mapping__.items():
			self.fields.append(k)


	def get(self,**query):		
		condition = Utils.dumps_dict(**query)
		sql = "SELECT %s FROM %s WHERE %s;" % (','.join(self.fields),self.table,condition)
		print(sql)
		with self.db(_db['name']) as db:
			db.execute(sql)
			data = db.fetchall()
		if not data:
			raise RecordNotExistsError('Not query this record:%s' % query)
		elif len(data) > 1:
			raise MultiRecordError('Query multi record:%s' % query)
		attrs = dict()
		for field,value in zip(self.fields,data[0]):
			attrs[field] = value
		return self.model(**attrs)

	def save(self):
		if self._instance is None:
			raise AttributeError('Missing %s object instance' % self.model)
		value = []
		for field in self.fields:
			value.append(getattr(instance,field))
		sql = Insert(self.table,self.fields,value).as_sql()
		print(sql,value)
		with self.db(_db['name']) as db:
			db.execute(sql,value)
			data = db.rowcount
		return data

	def all(self):
		query = Query(self.model,fields=self.fields)
		return query

	def query(self,**q):
		pass

	def update(self):
		pass



class ConverterDescriptor(object):

	def __init__(self,model):
		self.converter = Converter(model)

	def __get__(self,instance,onwer):
		if instance is not None:
			return Converter(model,instance)
		return self.converter



class Field(object):
	column_type = ''

	def __init__(self,name=None,default=None,unique=False,null=True):
		self.name = name
		self.default = default
		self.unique = unique
		self.null = null

	def constraint(self):
		sql = []
		if self.default:
			sql.append("DEFAULT %s" % Utils.repr(self.default))
		if self.unique:
			sql.append("UNIQUE")
		if not self.null:
			sql.append("NOT NULL")
		return ' '.join(sql)

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
		instance.object = ConverterDescriptor(instance)
		return instance


class Model(object,metaclass=ModelMetaClass):

	def __init__(self,**kwargs):
		for k,v in kwargs.items():
			setattr(self,k,v)

	def __repr__(self):
		attrs = []
		for k,v in self.__dict__.items():
			v = "%r" % v
			if len(v) > 20:
				v = v[:20] + '...'
			attrs.append('%s:%s' % (k,v))
		if len(attrs) > 6:
			attrs = attrs[:6]
			attrs[-1] = '...'
		return "<%s: %s>" % (self.__class__.__name__,','.join(attrs))

	def __str__(self):
		return "%s object" % self.__class__.__name__



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
		





