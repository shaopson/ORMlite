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


class Field(object):

	def __init__(self,default=None,unique=False,null=True,check=None):
		self.default = default
		self.unique = unique
		self.null = null
		self.check = check
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

	def __str__(self):
		return self.__class__.__name__

	def __repr__(self):
		return "<%s:%s>" % (self.__class__.__name__,self.name)


class CharField(Field):

	def __init__(self,length=100,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.length = length


class TextField(Field):
	pass


class IntegerField(Field):
	pass


class DateTimeField(Field):
	pass


class DateField(Field):
	pass


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

	









# Foreign Key (name) REFERENCES table(name);


