import sys
import os
import sqlite3
import copy
from ormlite.exception import *
from ormlite.fields import Field,PrimaryKey,RelatedMix,Mappings
from ormlite.utils import _format,_condition,convert

__models__ = {}

def registered_model(name,model):
	global __models__
	model_name = "%s.%s" % (model.__module__,name)
	__models__[model_name] = model


Sum = lambda x:'SUM(%s)' % x
Count = lambda x:"COUNT(%s)" % x
Avg = lambda x:"AVG(%s)" % x
Max = lambda x:"MAX(%s)" % x
Min = lambda x:"MIN(%s)" % x


class Database(object):

	db = {}
	
	def __init__(self,db = None):
		if db:
			self.db = db
		self.connect = None
		self.cursor = None
		self.connector = sqlite3.connect

	def __enter__(self):
		self.connect = self.connector(**self.db)
		self.cursor = self.connect.cursor()
		return self.cursor

	def __exit__(self,exc_type,exc_instance,traceback):
		if not exc_instance:
			self.connect.commit()
		self.connect.close()

	def __str__(self):
		return "<Database:'%s'>" % self.db['database']

	@classmethod
	def config(cls,database,timeout = 5,**kw):
		cls.db['database'] = database
		cls.db['timeout'] = timeout
		cls.db.update(kw)


class Where(object):

	def __init__(self,where=None):
		self.buf = []
		if where is not None:
			self.buf.append(where)

	def __or__(self,where):
		new = self.copy()
		if where and self:
			where = where.copy()
			new.brackets()
			where.brackets()
			new.buf.append(" OR ")
			new.buf.append(where)
		elif where:
			new = where.copy()
		return new


	def __and__(self,where):
		new = self.copy()
		if where and self:
			where = where.copy()
			new.brackets()
			where.brackets()
			new.buf.append(" AND ")
			new.buf.append(where)
		elif where:
			new = where.copy()
		return new

	def __invert__(self):
		new = self.copy()
		if self:
			new.brackets()
			new.buf.insert(0,'NOT ')
		return new

	def __str__(self):
		where = ""
		for x in self.buf:
			where += str(x)
		return where

	def __bool__(self):
		return bool(self.buf)

	def __copy__(self):
		return self.copy()

	def copy(self):
		new = self.__class__()
		new.buf = copy.deepcopy(self.buf)
		return new

	def brackets(self):
		if len(self.buf) > 1:
			self.buf.insert(0,"(")
			self.buf.append(")")

	def as_sql(self):
		where = []
		for node in self.buf:
			if isinstance(node,self.__class__):
				where.append(node.as_sql())
			elif isinstance(node,dict):
				conditions = convert(**node)
				w = " AND ".join(conditions)
				if len(conditions) > 1:
					w = "(%s)" % w
				where.append(w)
			else:
				where.append(node)
		return "".join(where)



class Compile(object):

	def __init__(self,model):
		self.model = model

	def update(self,obj=None,where=None,frag=True,**columns):
		"""
		obj: Model instance
		columns dict:{field:value}
		"""
		buf = ['UPDATE "%s" SET' % self.model.__table__]
		if not obj and not columns:
			raise ValueError("obj and columns can not both be None")
		if obj:
			if obj.pk is None:
				raise ValueError("Object <%s> id is invalid" % obj)
			if where:
				where += 'AND "id" = %s' % obj.id
			else:
				where = '"id" = %s' % obj.id
			if not columns: 
				columns = {}
				for field in obj.__mapping__.keys():
					#如果是关系对象或有时间对象需要自动更新时间 待处理
					columns[field] = getattr(obj,field)

		fields = []
		values = []
		for k,v in columns.items():
			if frag:
				fields.append('"%s" = ?' % k)
				values.append(v)
			else:
				date.append('"%s" = %s' % (k,_format(v)))
		buf.append(','.join(fields))
		if where:
			buf.append("WHERE")
			buf.append(where)
		buf.append(";")
		sql = " ".join(buf)
		if frag:
			return sql,values
		return sql

	def insert(self,obj,frag=True):
		# INSERT OR REPLACE INTO %s (%s) VALUES (%s);
		table = self.model.__table__
		fields = []
		values = []
		for attr,field in obj.__mapping__.items():
			fields.append('"%s"' % attr)
			if isinstance(field,RelatedMix):
				value = getattr(obj,attr).pk
			else:
				value = getattr(obj,attr)
			if field.auto:
				value = field.auto(value)
			if not frag:
				value = _format(value)
			values.append(value)
		if frag:
			values_ph = "?" * len(fields)
			sql = 'INSERT INTO "%s" (%s) VALUES (%s);' % (table,",".join(fields),",".join(values_ph))
			return sql,values
		sql = 'INSERT INTO "%s" (%s) VALUES (%s);' % (table,",".join(fields),",".join(values))
		return sql

	def delete(self,obj=None,where=None):
		if obj is None and where is None:
			raise ValueError('obj and where can not both be None') 
		if obj:
			if not obj.pk:
				raise ValueError("object <%s> id is invalid" % obj)
			where = '"id" = %s' % obj.pk 
		sql = 'DELETE FROM "%s" WHERE %s' % (self.model.__table__,where)
		return sql

	def select(self,fields,where=None,orderby=None,limit=None,**kw):
		buf = ['SELECT']
		if kw.get("distinct"):
			buf.append("DISTINCT")
		columns = fields[:]
		if "alias" in kw:
			alias = kw.get("alias",{})
			fields.extend(alias.keys())
			alias = ("%s AS %s " % (v,k) for k,v in alias.items())
			columns.extend(alias)
		buf.append(', '.join(columns))
		buf.append('FROM')
		buf.append(self.model.__table__)
		if where:
			buf.append("WHERE %s" % where)
		if 'groupby' in kw:
			groupby = kw.get("groupby",[])
			buf.append("GROUP BY %s" % ','.join(groupby))
		if orderby:
			buf.append("ORDER BY %s" % ', '.join(orderby))
		if limit is not None:
			if isinstance(limit,slice):
				start = limit.start or 0
				length = limit.stop
				buf.append("LIMIT %s OFFSET %s" % (length,start))
			elif isinstance(limit,int):
				buf.append("LIMIT 1 OFFSET %s" % limit)
		sql = ' '.join(buf) + ';'
		print(sql,fields)
		return sql,fields

	def create(self):
		pass



class Query(object):

	def __init__(self,model,fields=None,**kwargs):
		self.model = model
		self.table = model.__table__
		self.fields = fields or []
		self.where = kwargs.get('where',Where())
		self.alias = kwargs.get('alias',{})
		self.distinct = kwargs.get('distinct',False)
		self.orderby = kwargs.get('orderby',[])
		self.groupby = kwargs.get('groupby',[])
		self.limit = kwargs.get('limit',None)
		self.sql = ''
		self.function = None
		self.cache = None
		self.result = None

	def as_sql(self):
		sql = ['SELECT']
		if self.distinct:
			sql.append("DISTINCT")
	#	fields = self.fields[:]
		fields = ['"%s"' % f for f in self.fields]
		if self.alias:
			self.fields.extend(self.alias.keys())
			alias = ('"%s" AS "%s"' % (v,k) for k,v in self.alias.items())
			fields.extend(alias)
		sql.append(', '.join(fields))
		sql.append('FROM "%s"' % self.table)
		if self.where:
			print(self.where.as_sql())
			sql.append("WHERE %s" % self.where.as_sql())
		if self.groupby:
			sql.append("GROUP BY %s" % ','.join(('"%s"' % f for f in self.groupby)))
		if self.orderby:
			sql.append("ORDER BY %s" % ', '.join(('"%s"' % f for f in self.orderby)))
		if self.limit is not None:
			if isinstance(self.limit,slice):
				start = self.limit.start or 0
				length = self.limit.stop
				sql.append("LIMIT %s OFFSET %s" % (length,start))
			elif isinstance(self.limit,int):
				sql.append("LIMIT 1 OFFSET %s" % self.limit)
		self.sql = ' '.join(sql) + ';'
		return self.sql

	def eval(self,sql,function=None):
		with Database() as db:
			db.execute(sql)
			result = db.fetchall()
		return function(result) if function else result

	def execute(self):
		sql = self.as_sql()
		print(sql)
		with Database() as db:
			db.execute(sql)
			self.cache = db.fetchall()
		if self.function:
			#根据需要原始处理数据
			self.result = self.function(self.cache)
		else:
			self.result = self.__get_objects()
		return self.result

	def __get_objects(self):
		result = []
		for col in self.cache:
			attrs = {}
			for attr,value in zip(self.fields,col):
				attrs[attr] = value
			result.append(self.model(**attrs))
		return result

	def copy(self):
		#克隆并返回一个新的对象
		new = self.__class__(self.model,self.fields)
		new.where = self.where.copy()
		new.alias = self.alias.copy()
		new.distinct = self.distinct
		new.groupby = self.groupby[:]
		new.orderby = self.orderby[:]
		new.limit = self.limit
		return new

	def __getitem__(self,value):
		if not isinstance(value,(slice,int)):
			raise TypeError("Query object must be integers or slices")
		if self.result:
			return list(self.result)[value]
		new = self.copy()
		new.limit = value
		new.execute()
		if isinstance(value,int):
			return new.result[0] if new.result else []
		return new.result[value]

	def __bool__(self):
		if self.result is None:	
			self.execute()
		return bool(self.result)

	def __iter__(self):
		if self.result is None:
			self.execute()
		return iter(self.result)

	def __len__(self):
		if self.result is None:
			self.execute()
		return len(self.result)

	def __or__(self,other):
		new = self.copy()
		new.where |= other.where
		return new

	def __and__(self,other):
		new = self.copy()
		new.where &= other.where
		return new

	def __invert__(self):
		new = self.copy()
		new.where = ~self.where
		return new

	def __str__(self):
		if self.result is None:
			self.execute()
		return "<Query %r>" % self.result

	def get(self,**kwargs):
		query = self.copy().query(**kwargs)
		query.execute()
		if not query.result:
			raise RecordNotExists('Not query %s object record:%s' % (self.model,query.where))
		elif len(query.result) > 1:
			raise MultiRecordError('Query multiple %s object records:%s' % (self.model.__name__,query.where))
		return query.result[0]

	def count(self):
		if self.result is None:
			return len(self.result)
		new = self.copy()
		new.fields = []
		new.alias = {"__count":Count('id')}
		new.function = lambda x:x[0][0]
		new.execute()
		return new.result

	def sort(self,*fields):
		new = self.copy()
		new.orderby.extend(fields)
		return new

	def values(self,*fields,flat=False):
		new = self.copy()
		if fields:
			new.fields = list(fields)
		if flat:
			new.function = lambda x:[s[0] for s in x]
		else:
			new.function = lambda x:x
		return new

	def items(self,*fields):
		new = self.copy()
		if fields:
			new.fields = list(fields)
		fields = new.fields
		def to_dict(data):
			result = []
			for row in data:
				d = {}
				for field,value in zip(fields,row):
					d[field] = value
				result.append(d)
			return result
		new.function = to_dict
		new.execute()
		return new.result

	def query(self,**kwargs):
		where = Where(kwargs)
		new = self.copy()
		new.where &= where
		return new

	def group(self,**kwargs):#rename
		new = self.copy()
		alias = {k:v for k,v in kwargs.items()}
		new.alias = alias
		new.groupby = self.fields[:]
		fields = new.fields
		def to_dict(data):
			result = []
			for row in data:
				d = {}
				for field,value in zip(fields,row):
					d[field] = value
				result.append(d)
			return result
		new.function = to_dict
		new.execute()
		return new.result

	def extra(self,**kwargs):
		pass

	def exists(self):
		pass


class Accessor(object):

	def __init__(self,model,instance = None):
		self.model = model
		self.table = model.__table__
		self._instance = instance
		self.fields = list(model.__mapping__.keys())

	def get(self,**kwargs):
		return Query(self.model,fields=self.fields).get(**kwargs)

	def save(self):
		if self._instance is None:
			raise ValueError("%s Accessor requires parameter:instance" % self.model)
		compile = Compile(model=self.model)
		if self._instance.pk is None:
			sql,values = compile.insert(obj=self._instance,frag=True)
			print(sql,values)
			with Database() as db:
				db.execute(sql,values)
				db.execute("SELECT last_insert_rowid();")
				id = db.fetchone()[0]
				self._instance.id = id
		else:
			sql,values = compile.update(obj=self._instance)
			with Database() as db:
				db.execute(sql,values)

	def all(self):
		query = Query(self.model,fields=self.fields)
		return query

	def query(self,**kwargs):
		return Query(self.model,fields=self.fields).query(**kwargs)

	def update(self,**columns):
		if self._instance and self._instance.pk is None:
			raise ValueError("object %s id is valied")
		compile = Compile(self.model)
		sql,values = compile.update(obj=self._instance,**columns)
		print(sql,values)
		with Database() as db:
			db.execute(sql,values)
		
	def delete(self):
		if not self._instance:
			raise DoseNotExist("%s object dose not exist" % self.model.__name__)
		if self._instance.pk is not None:
			sql = Compile(self.model).delete(obj=self._instance)
			print(sql)
			with Database() as db:
				db.execute(sql)


class RelatedDescriptor(object):

	def __init__(self,name,reference):
		self.name = name
		self.related_name = name + "_id"
		self._reference = None
		self.reference = reference

	def __get__(self,instance,onwer):
		if instance:
			obj = instance.__dict__.get(self.name)
			if obj:
				return obj
			fk = getattr(instance,self.related_name)
			obj = self.reference.object.get(id=fk)
			instance.__dict__[self.name] = obj
			return obj
		return self.reference

	def __set__(self,instance,value):
		if isinstance(value,Model):
			#应该检查一下value是不是reference的实例？
			instance.__dict__[self.name] = value
			setattr(instance,self.related_name,value.id)
		elif isinstance(value,(int,str)):
			setattr(instance,self.related_name,value)
		else:
			raise ValueError("%s" % value)

	@property
	def reference(self):
		if isinstance(self._reference,str):
			model = __models__.get(self._reference)
			if not model:
				raise ValueError("Not found object:%s" % self._reference)
			return model
		return self._reference

	@reference.setter
	def reference(self,value):
		if isinstance(value,Model):
			self._reference = value
		elif isinstance(value,str):
			model = __models__.get(value,value)
			self._reference = model
		else:
			raise ValueError('Reference value must be str or model')


class AccessorDescriptor(object):

	def __init__(self,model):
		self.accessor = Accessor(model)

	def __get__(self,instance,onwer):
		if instance is not None:
			return Accessor(onwer,instance)
		return self.accessor


class ModelMetaClass(type):

	def __new__(cls,name,bases,attrs):
		if name == 'Model':
			return type.__new__(cls,name,bases,attrs)
		mapping = {}
		for attr,value in attrs.items():
			if isinstance(value,Field):
				mapping[attr] = value
				value.name = attr
		has_pk = False
		relation = {}
		for attr,field in mapping.items():
			if isinstance(field,PrimaryKey):
				has_pk = True
				attrs["__primarykey__"] = attr
			elif isinstance(field,RelatedMix):
				relation[attr] = field
				related_model = field.related_model
				if isinstance(related_model,str):
					if related_model == "self":
						related_model = "%s.%s" % (attrs['__module__'] + "." + name)
					else:
						related_model = "%s.%s" % (attrs['__module__'],related_model)
				attrs[attr] = RelatedDescriptor(attr,related_model)
				continue
			attrs[attr] = field.default #是否应该初始化?
		if not has_pk:
			mapping['id'] = PrimaryKey()
			attrs['id'] = None
			attrs["__primarykey__"] = 'id'
		attrs['__mapping__'] = mapping
		attrs['__table__'] = name
		attrs["__relation__"] = relation
		instance = type.__new__(cls,name,bases,attrs)
		instance.object = AccessorDescriptor(instance)
		registered_model(name,instance)
		return instance


class Model(object,metaclass=ModelMetaClass):

	def __init__(self,**kwargs):
		for k,v in kwargs.items():
			setattr(self,k,v)

	def __repr__(self):
		attrs = []
		for k,v in self.__dict__.items():
			attrs.append('%s:%r' % (k,v))
		if len(attrs) > 8:
			attrs = attrs[:8]
			attrs[-1] = '...'
		return "<%s: %s>" % (self.__class__.__name__,','.join(attrs))

	def __str__(self):
		return "<%s object>" % self.__class__.__name__

	@property
	def pk(self):
		return getattr(self,self.__primarykey__,None)

	@pk.setter
	def pk(self,value):
		setattr(self,self.__primarykey__,value)

	def save(self):
		self.object.save()

	def update(self,*fields):
		columns = {}
		for field in fields:
			columns[field] = getattr(self,field)
		self.object.update(**columns)

	def delete(self):
		self.object.delete()

	def clear(self):
		#将对象字段的值设为None 但不会清除数据库的记录
		pass










		





