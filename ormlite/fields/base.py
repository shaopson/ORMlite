import datetime
from ormlite.exception import FieldException



class Field(object):

    is_related = False

    def __init__(self,default=None,null=True,unique=False,primary_key=False,column_name=None):
        """
        :param default: 默认值
        :param null: 值是否可为NULL
        :param unique: 是否唯一
        :param primary_key: 是否是主键
        :param column_name: 字段名
        """
        self.default = default
        self.null = null
        self.unique = unique
        self.primary_key = primary_key
        self.column = column_name
        self.name = None
        self.model = None

    def get_type(self):
        return self.__class__.__name__

    def get_column(self):
        if self.column:
            return self.column
        return self.name

    def check(self):
        self._check_field_name()
        self._check_definition()

    def _check_field_name(self):
        if self.name == "pk":
            raise FieldException("'%s' field name cannot use 'pk', the name is reserved" % self)
        if self.name.endswith("_"):
            raise FieldException("'%s' field name cannot end with '_'" % self)
        if self.name.find("__") >= 0:
            raise FieldException("'%s' field name cannot contain '__'" % self)

    def _check_definition(self):
        if self.primary_key and self.null:
            raise FieldException("'%s' primary key must not have null=True" % self)

    def to_sql(self,value):
        #将python数据类型 换成sql类型
        if value is None:
            return "NULL"
        return str(value)

    def adapt(self,value):
        # python -> sql
        return value

    def convert(self,value):
        # sql -> python
        return value

    def __repr__(self):
        return "<%s:%s>" % (self.__class__.__name__,self.name)


class BooleanField(Field):

    def to_sql(self,value):
        if value:
            return '"1"'
        return '"0"'


class CharField(Field):

    def __init__(self,max_length=None,*args,**kwargs):
        super(CharField,self).__init__(*args,**kwargs)
        self.max_length = max_length

    def get_type(self):
        #字段类型
        #orm将通过 field_type 转换成数据库的 column_type
        return "CharField"

    def to_sql(self,value):
        return '"%s"' % value


class DateField(Field):

    def __init__(self,auto_now=False,auto_now_add=False,**kwargs):
        super(DateField,self).__init__(**kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add

    def adapt(self,value):
        if isinstance(value,datetime.datetime):
            return value.date()
        return value

    @property
    def value_on_create(self):
        if self.auto_now:
            return datetime.datetime.now().date()
        return None

    @property
    def value_on_update(self):
        if self.auto_now_add:
            return datetime.datetime.now().date()
        return None


class DateTimeField(Field):

    def __init__(self,auto_now=False,auto_now_add=False,**kwargs):
        super(DateTimeField,self).__init__(**kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add

    @property
    def value_on_create(self):
        if self.auto_now_add:
            return datetime.datetime.now()
        return None

    @property
    def value_on_update(self):
        if self.auto_now:
            return datetime.datetime.now()
        return None


class FloatField(Field):

    def get_type(self):
        return "FloatField"


class IntegerField(Field):

    def get_type(self):
        return "IntegerField"


class TextField(Field):

    def get_type(self):
        return "TextField"

    def to_sql(self,value):
        return "'%s'" % value


class TimeFiled(Field):

    def __init__(self,auto_now=False,auto_now_add=False,**kwargs):
        super(TimeFiled,self).__init__(**kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add

    def get_type(self):
        return "TimeField"

    def to_sql(self,value):
        pass

    @property
    def value_on_create(self):
        if self.auto_now_add:
            return datetime.datetime.now().time()
        return None

    @property
    def value_on_update(self):
        if self.auto_now:
            return datetime.datetime.now().time()
        return None


class PrimaryKey(IntegerField):

    def __init__(self,*args,**kwargs):
        super(PrimaryKey,self).__init__(*args,**kwargs)
        self.primary_key = True
        self.null = False

    def get_type(self):
        return "PrimaryKey"
