import datetime
from ormlite.exception import FieldException


class FieldNameError(FieldException):
    pass


class Field(object):

    def __init__(self,default=None,null=True,unique=False,primary_key=False,
                column_name=None,on_update=None,on_create=None,on_delete=None):
        """
        :param default: 默认值
        :param null: 值是否可为NULL
        :param unique: 是否唯一
        :param primary_key: 是否是主键
        :param column_name: 字段名
        :param on_update: 当更新数据时要执行的动作
        :param on_create: 当第一次写数据时要执行的动作
        :param on_delete: 当删除数据时要执行的动作
        """
        self.default = default
        self.null = null
        self.unique = unique
        self.primary_key = primary_key
        self.column = column_name
        self.on_update = on_update
        self.on_create = on_create
        self.on_delete = on_delete
        self.name = None

    def get_type(self):
        return self.__class__.__name__


    def check(self):
        pass

    def check_field_name(self):
        pass
        # if not self.name:
        #     raise FieldNameError("Field name cannot be empty:%s" % self.name)
        # if self.name.startswith("__") or self.name.startswith("_"):
        #     raise FieldNameError("Field names cannot begin with '__' or '_':%s" % self.name)
        # if self.name == "id" and not self.primary_key:
        #     raise FieldNameError("This field is not a primary key and cannot be named 'id'")

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
        return "<%s:%s>" % (self.__class__.__name__,self.attname)


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

    def adapt(self,value):
        if isinstance(value,datetime.datetime):
            return value.date()
        return value


class DateTimeField(Field):
    pass


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

    def get_type(self):
        return "TimeField"

    def to_sql(self,value):
        pass


class PrimaryKey(IntegerField):

    def __init__(self,*args,**kwargs):
        super(PrimaryKey,self).__init__(*args,**kwargs)
        self.primary_key = True
        self.null = False

    def get_type(self):
        return "PrimaryKey"


class LazyModel():

    def __init__(self,model_name,module_name):
        self.model_name = model_name
        self.model = None

    def __set__(self,instance,value):
        pass

    def __get__(self,instance,cls):
        if instance is None:
            return self
        if self.model:
            return self.model



class RelatedObject(object):

    def __init__(self,model):
        self.model = model
        self.object_cache = None

    def get_object(self):
        if self.object_cache:
            return self.object_cache




class RelatedField(Field):

    def __init__(self,related_model,field,*args,**kwargs):
        super(RelatedField,self).__init__(*args,**kwargs)
        self.related_model = related_model
        self.related_field = self.related_model.__fields__.get(field)

    def get_type(self):
        return self.related_field.get_type()


class ForeignKey(RelatedField):
    #一对多 外键
    #关联的表必须只有一个主键，不能是组合主键
    def __init__(self,related_model,*args,**kwargs):
        field_name = related_model.__pk__.name
        super(ForeignKey,self).__init__(related_model,field_name,*args,**kwargs)


class RelatedDescriptor():

    def __init__(self,field):
        self.field = field
        self.object_cache = None

    def __get__(self,instance,owner):
        if instance is None:
            return self.field # or self
        obj = getattr(instance,self.chech_name,None)
        if obj is not None:
            return obj
        related_value = getattr(instance,self.related_name,None)
        if related_value is None:
            return None
        q = {
            self._field.name:related_value
        }
        return self._model.query(**q)

    def __set__(self,instance,value):
        if value is None:
            setattr(instance, self.chech_name, None)
            setattr(instance, self.related_name, None)
            return
        if not isinstance(value,self._model):
            raise ValueError('"%s.%s" must be a "%s" instance:%s' % (instance.__class__.__name__,self.related.name,
                                                                         self._model.__name__,value))
        setattr(instance,self.chech_name,value)
        related_value = getattr(value,self._field.name,None)
        if related_value is not None:
            setattr(instance,self.related_name,related_value)

    def __repr__(self):
        return "<RelatedDescriptor:%s>" % (self.related.name)






