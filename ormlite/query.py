import copy
from ormlite.base import configuration


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


def get_alias_converter(aliases):
	def converter(row,cursor):
		result = []
		columns = [col[0] for col in cursor.description]
		for values in row:
			kwargs = {}
			for k,v in zip(columns,values):
				alias = aliases.get(k,None)
				if alias:
					k = alias
				kwargs[k] = v
			result.append(kwargs)
		return result
	return converter


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


Min = lambda x:'MIN(`%s`)' % x

Max = lambda x:'MAX(`%s`)' % x

Sum = lambda x:'SUM(`%s`)' % x

Count = lambda x:'COUNT(`%s`)' % x

Avg = lambda x:'AVG(`%s`)' % x



class Query(object):
	statement = "SELECT"

	def __init__(self,model,fields=None,where=None):
		self.model = model
		self.table = model.__name__
		self._fields = list(fields) if fields else []
		self._where = where.copy() if where else Where()
		self._alias = {}
		self._distinct = False
		self._orderby = []
		self._groupby = []
		self._limit = None
		self._compiler = None
		self._converter = None
		self._cache = None
		self.result = None

	def as_sql(self):
		if self._compiler is None:
			self._compiler = configuration.compiler
		return self._compiler.compile(self)

	def execute(self):
		if self._converter is None:
			self._converter = get_object_converter(self.model)
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
			self._cache = cursor.fetchall()
			self.result = self._converter(self._cache,cursor)
		return self.result

	def copy(self):
		#克隆并返回一个新的对象
		new = self.__class__(self.model,self._fields,self._where)
		new._alias = self._alias.copy()
		new._distinct = self._distinct
		new._limit = self._limit
		new._groupby = list(self._groupby)
		new._orderby = list(self._orderby)
		return new

	def __getitem__(self,value):
		if not isinstance(value,(slice,int)):
			raise TypeError("parameter must be integers or slices")
		if isinstance(value,int) and value < 0:
			raise TypeError("Negative indexing is not supported.")
		elif isinstance(value,slice) and value.start is not None and value.start < 0:
			raise TypeError("Negative indexing is not supported.")
		elif isinstance(value,slice) and value.stop is not None and value.stop < 0:
			raise TypeError("Negative indexing is not supported.")
		if self.result:
			return list(self.result)[value]
		new = self.copy()
		new._limit = value
		new.execute()
		if isinstance(value,int):
			return new.result[0] if new.result else []
		return new.result[::value.step] if value.step else new.result

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
			raise query.model.DoesNotExists('Not query %s object record:%s' % (self.model,query._where))
		elif len(query.result) > 1:
			raise query.model.MultiResult('Query multiple %s object records:%s' % (self.table,query._where))
		return query.result[0]

	def count(self):
		if self.result is not None:
			return len(self.result)
		new = self.copy()
		new._fields = []
		new._alias = {"count":Count(self.model.get_pk_name())}
		new._converter = flat_converter
		new.execute()
		return new.result[0]

	def sort(self,*fields):
		new = self.copy()
		new._orderby.extend(fields)
		new._converter = self._converter
		return new

	def items(self,*fields,**kwargs):
		flat = kwargs.pop('flat', False)
		new = self.copy()
		new._alias.update(kwargs)
		new._fields = list(fields)
		if flat:
			new._converter = flat_converter
		else:
			new._converter = raw_data#get_fields_converter(new.fields)
		return new

	def values(self,*fields,**kwargs):
		new = self.copy()
		new._fields = list(fields)
		if kwargs:
			new._alias.update(kwargs)
		new._converter = dict_converter
		return new

	def query(self,**kwargs):
		where = Where(kwargs)
		new = self.copy()
		new._where &= where
		new._converter = get_object_converter(self.model)
		return new

	def exclude(self,**kwargs):
		where = ~Where(kwargs)
		new = self.copy()
		new._where &= where
		new._converter = get_object_converter(self.model)
		return new

	def group(self,*fields):
		new = self.copy()
		new._fields.extend(fields)
		new._groupby = list(fields)
		new._converter = dict_converter
		return new.execute()

	def update(self,**update_fields):
		update = Update(model=self.model,update_fields=update_fields,where=self.where)
		update.execute()

	def first(self):
		return self[0]

	def last(self):
		if self.result is not None:
			return self.result[-1]
		new = self.copy()
		if new._orderby:
			new_orderby = []
			for field_name in new._orderby:
				if field_name.startswith('-'):
					new_orderby.append(field_name[1:])
				else:
					new_orderby.append("-" + field_name)
			new._orderby = new_orderby
		else:
			new._orderby = ['-id']
		return new.first()

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
		self.table = model._opts.model_name
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

	def execute(self,db=None):
		sql, params = self.as_sql()
		if configuration.debug:
			s = sql.replace("?",'%r')
			configuration.logger.debug(s % params)
		db = configuration.db
		with db as connection:
			cursor = connection.cursor()
			if params:
				cursor.execute(sql,params)
			else:
				cursor.execute(sql)



class Insert(Statement):
	statement = "INSERT"

	def execute(self,db=None):
		sql, params = self.as_sql()
		if configuration.debug:
			placeholder = configuration.db.placeholder
			s = sql.replace(placeholder,'%r')
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

