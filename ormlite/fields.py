from ormlite.utils import _format


class Mappings:
	columns = {
		"CharField":"varchar(%s)",
		"DateField":"data",
		"DateTimeField":"datetime",
		"IntegerField":"integer",
		"TextField":"text",
		"PrimaryKey":'integer',
		"ForeignKey":'integer',
	}

	operates = {
		"gt":"> %s",
		"ge":">= %s",
		"lt":"< %s",
		"le":"<= %s",
		"not":"!= %s",
		"in":"IN %s",
		"range":"BETWEEN %s AND %s",
		"id":"= %s"
	}
	
	@classmethod
	def get_column(cls,field):
		column = cls.columns.get(field.__class__.__name__,None)
		if not column:
			raise KeyError('Not found column:%s' % field)
		length = getattr(field,'length',None)
		if length:
			return column % length
		return column


def __gt(column,value):
	return '"%s" > %r' % (column,value)

def __ge(column,value):
	return '"%s" >= %r' % (column,value)

def __lt(column,value):
	return '"%s" < %r' % (column,value)

def __le(column,value):
	return '"%s" <= %r' % (column,value)

def __not(column,value):
	return '"%s" != %r' % (column,value)

def __in(column,value):
	return '"%s" IN %s' % (column,value)

def __range(column,value):
	data = [column]
	for x in value:
		data.append(x)
	return '"%s" BETWEEN %s AND %s' % (tuple(data))

def __id(column,value):
	return '"%s" = %s' % (column,value)

def __like(column,value):
	return '"%s" LIKE \'%s\'' % (column,value)

def __contains(column,value):
	return '"%s" LINK \'%%%s%%\'' % (column,value)

def __startswith(column,value):
	return '"%s" LIKE \'%s%%\'' % (column,value)

def __endswith(column,value):
 	return '"%s" LIKE \'%%%s\'' % (column,value)

#__endswith = lambda x,y:'"%s" LIKE %%%s' % (x,y)


operators = {
	"gt":__gt,
	"ge":__ge,
	"lt":__lt,
	"lt":__le,
	"not":__not,
	"in":__in,
	"range":__range,
	"id":__id,
	"like":__like,
	"contains":__contains,
	"startswith":__startswith,
	"endswith":__endswith
}


class Field(object):

	def __init__(self,default=None,unique=False,null=True,auto=None,check=None):
		self.default = default
		self.unique = unique
		self.null = null
		self.check = check
		self.auto = auto
		self.name = ''

	def constraint(self):
		const = []
		if self.default:
			const.append("DEFAULT %s" % _format(self.default))
		if self.unique:
			const.append("UNIQUE")
		if not self.null:
			const.append("NOT NULL")
		if self.check:
			const.append("CHECK(%s)" % self.check)
		return ' '.join(const)

	def run_auto(self,value = None):
		if self.auto:
			return self.auto(value)

	def convert(self,value):
		if value is None:
			return "NULL"
		return value

	def restore(self,value):
		return value

	def __str__(self):
		return self.__class__.__name__

	def __repr__(self):
		return "<%s:%s>" % (self.__class__.__name__,self.name)


class CharField(Field):

	def __init__(self,length=100,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.length = length

	def convert(self,value):
		return "'%s'" % value



class TextField(Field):
	
	def convert(self,value):
		return "'%s'" % value


class IntegerField(Field):
	
	def convert(self,value):
		if not isinstance(value,int):
			raise ValueError("<%s:%s> value requires int type" % (self.__class__.__name__,self.name))
		return value


class DateTimeField(Field):

	
	def restore(self,value):
		from datetime import datetime
		if isinstance(value,str):
			value = value.strip()
			if value.find("."):
				return datetime.strptime(value,"%Y-%m-%d %H:%M:%S.%f")
			return datetime.strptime(value,"%Y-%m-%d %H:%M:%S")
		return value


class DateField(Field):

	def restore(self,value):
		from datetime import datetime
		if isinstance(value,str):
			value = value.strip()
			return datetime.strptime(value,"%Y-%m-%d")
		return value


class TimeField(Field):

	def restore(self,value):
		from datetime import datetime
		if isinstance(value,str):
			value = value.strip()
			if value.find("."):
				return datetime.strptime(value,"%H:%M:%S.%f")
			return datetime.strptime(value,"%H:%M:%S")
		return value


class PrimaryKey(Field):

	def __init__(self):
		super().__init__()

	def constraint(self):
		return "PRIMARY KEY AUTOINCREMENT"


SET_NULL = "SET NULL"
CASCADE = "CASCADE"
NO_ACTION = "NO ACTION"
SET_DEFAULT = "SET DEFAULT"

class RelatedMix(object):
	
	ops = [SET_NULL,SET_DEFAULT,CASCADE,NO_ACTION]

	def __init__(self,related_model,on_update=None,on_delete=None):
		self.related_model = related_model
		self.on_update = on_update
		self.on_delete = on_delete

	def joint(self,name):
		cons = []
		if self.on_update:
			if self.on_update not in self.ops:
				raise ValueError("%s ON UPDATE not support %s" % (self.__class__.__name__,self.on_update))		
			cons.append("ON UPDATE %s" % self.on_update)
		if self.on_delete:
			if self.on_delete not in self.ops:
				raise ValueError("%s ON DELETE not support %s" % (self.__class__.__name__,self.on_update))
			cons.append("ON UPDATE %s" % self.on_delete)
		op = " ".join(cons)
		return "FOREIGN KEY (%s) REFERENCES %s(%s) %s" % (name,self.related_model,"id",op)	


class ForeignKey(Field,RelatedMix):

	def __init__(self,related_model,on_delete=None,on_update=None,**kwargs):
		super(ForeignKey,self).__init__(**kwargs)
		RelatedMix.__init__(self,related_model,on_update,on_delete)

	




