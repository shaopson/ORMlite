import copy
from ormlite import exception
from ormlite.base import configuration
from ormlite.db.utils import Count

def flat_converter(row,cursor):
	return [values[0] for values in row]


def dict_converter(row,cursor):
	result = []
	keys = [col[0] for col in cursor.description]
	for values in row:
		d = {}
		for k,v in zip(keys,values):
			d[k] = v
		result.append(d)
	return result


def raw_data(row,cursor):
	return row


def get_object_converter(cls):
	def converter(row,cursor):
		result = []
		cols = [col[0] for col in cursor.description]
		for values in row:
			kwargs = {}
			for k,v in zip(cols,values):
				kwargs[k] = v
			result.append(cls(**kwargs))
		return result
	return converter


class Result(object):

	def __init__(self,data=None,converter=None):
		self.data = data
		self.converter = converter


class Query(object):
	statement = "SELECT"

	def __init__(self,model,fields=None,where=None,**kwargs):
		self.model = model
		self.table = model.__table__
		self.fields = fields or []
		self.where = where or Where()
		self.alias = kwargs.get('alias',{})
		self.distinct = kwargs.get('distinct',False)
		self.orderby = kwargs.get('orderby',[])
		self.groupby = kwargs.get('groupby',[])
		self.limit = kwargs.get('limit',None)
		self.function = None
		self.cache = None
		self.result = None
		self.compiler = None
		self.converter = None

	def as_sql(self):
		if self.compiler is None:
			self.compiler = configuration.compiler
		return self.compiler.compile(self)

	def execute(self,db=None):
		if self.converter is None:
			self.converter = get_object_converter(self.model)
		sql, params = self.as_sql()
		if configuration.debug:
			s = sql.replace("?","%r")
			configuration.logger.debug(s % params)
		db = configuration.db
		with db as connection:
			cursor = connection.cursor()
			if params:
				cursor.execute(sql, params)
			else:
				cursor.execute(sql)
			self.cache = cursor.fetchall()
			self.result = self.converter(self.cache,cursor)
		return self.result

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
			raise TypeError("parameter must be integers or slices")
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

	def __str__(self):
		if self.result is None:
			self.execute()
		return "<Query %r>" % self.result

	def get(self,**kwargs):
		query = self.copy().query(**kwargs)
		query.execute()
		if not query.result:
			raise query.model.NotExists('Not query %s object record:%s' % (self.model,query.where))
		elif len(query.result) > 1:
			raise query.model.MultiResult('Query multiple %s object records:%s' % (self.model.__name__,query.where))
		return query.result[0]

	def count(self):
		if self.result is not None:
			return len(self.result)
		new = self.copy()
		new.fields = []
		new.alias = {"count":Count(self.model.__pk__.name)}
		new.converter = flat_converter
		new.execute()
		return new.result[0]

	def sort(self,*fields):
		new = self.copy()
		new.orderby.extend(fields)
		new.converter = self.converter
		return new

	def values(self,*fields,**kwargs):
		flat = kwargs.pop('flat', False)
		new = self.copy()
		new.alias.update(kwargs)
		new.fields = list(fields)
		if flat:
			new.converter = flat_converter
		else:
			new.converter = raw_data
		return new

	def items(self,*fields,**kwargs):
		new = self.copy()
		new.fields = list(fields)
		#new.fields.extend(fields)
		new.alias.update(kwargs)
		new.converter = dict_converter
		return new

	def query(self,**kwargs):
		where = Where(kwargs)
		new = self.copy()
		new.where &= where
		new.converter = get_object_converter(self.model)
		return new

	def exclude(self,**kwargs):
		where = ~Where(kwargs)
		new = self.copy()
		new.where &= where
		new.converter = get_object_converter(self.model)
		return new

	def group(self,*fields,**kwargs):
		new = self.copy()
		new.fields.extend(fields)
		new.groupby = list(fields)
		new.converter = dict_converter
		new.alias.update(kwargs)
		return new.execute()

	def update(self,**update_fields):
		update = Update(model=self.model,update_fields=update_fields,where=self.where)
		update.execute()

	def exists(self):
		if self.result is None:
			self.execute()
		return bool(self.result)


class Where(object):
	statement = "WHERE"

	def __init__(self,condition=None):
		self.buf = []
		if condition:
			self.buf.append(condition)

	def __or__(self,other):
		new = self.copy()
		if other and self:
			where = other.copy()
			new.brackets()
			where.brackets()
			new.buf.append(" OR ")
			new.buf.append(where)
		elif other:
			new = other.copy()
		return new

	def __and__(self,other):
		new = self.copy()
		if other and self:
			where = other.copy()
			new.brackets()
			where.brackets()
			new.buf.append(" AND ")
			new.buf.append(where)
		elif other:
			new = other.copy()
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


class Statement(object):

	def __init__(self, model, instance=None, fields=None, where=None):
		self.model = model
		self.table = model.__table__
		self.instance = instance
		self.fields = fields
		self.where = where
		self.compiler = None
		self.converter = None

	def as_sql(self):
		if self.compiler is None:
			self.compiler = configuration.compiler
		return self.compiler.compile(self)

	def execute(self,db=None):
		sql, params = self.as_sql()
		if configuration.debug:
			s = sql.replace("?",'%r')
			configuration.logger.debug(s % params)
		db = configuration.db
		result = []
		with db as connection:
			cursor = connection.cursor()
			if params:
				cursor.execute(sql,params)
			else:
				cursor.execute(sql)
			if callable(self.converter):
				result = self.converter(cursor.fetchall(),cursor)
			else:
				result = cursor.fetchall()
		return result

	def add_where(self,kwargs):
		where = Where(kwargs)
		if self.where:
			self.where = self.where | where
		else:
			self.where = where

	def __str__(self):
		return "<%s object>" % self.__class__.__name__


class Update(Statement):
	statement = "UPDATE"

	def __init__(self, model, instance=None, fields=None, where=None,update_fields=None):
		super(Update,self).__init__(model,instance,fields,where)
		self.update_fields = update_fields


class Insert(Statement):
	statement = "INSERT"

	def execute(self,db=None):
		sql, params = self.as_sql()
		if configuration.debug:
			s = sql.replace("?",'%r')
			configuration.logger.debug(s % params)
		db = configuration.db
		with db as connection:
			cursor = connection.cursor()
			cursor.execute(sql,params)
			self.lastrowid = cursor.lastrowid
		return self.lastrowid

	def get_id(self):
		return getattr(self,"lastrowid",None)


class Delete(Statement):
	statement = "DELETE"
	pass

