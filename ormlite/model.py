from ormlite import configuration
from ormlite.fields import Field,PrimaryKey,RelatedDescriptor
from ormlite.query import Query,Insert,Update,Delete,Where
from ormlite.exception import ObjectNotExists,ModelException,MultiResult,ModelAgentError

PK_FIELD_NAME = "id"

class ModelAgent(object):


    def __init__(self, model, instance=None):
        self.model = model
        self._instance = instance
        self.fields = list(model._opts.get_fields_name())

    def create(self,**kwargs):
        obj = self.model(**kwargs)
        self._insert(object=obj)
        return obj

    def get_or_create(self,**kwargs):
        try:
           return self.get(**kwargs)
        except self.model.DoesNotExists:
           return self.create(**kwargs)

    def get(self, **kwargs):
        return Query(self.model,self.fields).get(**kwargs)

    def all(self):
        return Query(self.model, fields=self.fields)

    def query(self, **kwargs):
        where = Where(kwargs)
        return Query(self.model,fields=self.fields,where=where)

    def exclude(self,**kwargs):
        where = ~Where(kwargs)
        return Query(self.model,fields=self.fields,where=where)

    def values(self,*fields,**kwargs):
        return Query(self.model,fields=self.fields).values(*fields,**kwargs)

    def items(self,*fields,**kwargs):
        return Query(self.model,fields=self.fields).items(*fields,**kwargs)

    def count(self):
        return Query(self.model).count()

    def update(self, **kwargs):
        return Update(model=self.model,update_fields=kwargs).execute()

    def _insert(self,object):
        if not isinstance(object,self.model):
            raise TypeError("Argument 'obj' should be %s type" % self.model)
        insert = Insert(model=self.model,instance=object)
        insert.execute()
        object.pk = insert.get_id()

    def _update_obj(self,object,fields=None):
        if not isinstance(object,self.model):
            raise TypeError("Argument 'object' should be %s type" % self.model)
        if object.pk is None:
            raise AttributeError("%s primary key '%s' field value is invalid:%s" % (object,object.pk_name,object.pk) )
        Update(model=self.model,instance=object,fields=fields).execute()

    def _delete_obj(self,obj):
        if not isinstance(obj,self.model):
            raise TypeError("Argument 'obj' should be %s type" % self.model)
        if obj.pk is None:
            raise AttributeError("%s primary key '%s' field value is invalid:%s" % (obj,obj.pk_name,obj.pk) )
        return Delete(model=self.model,instance=obj).execute()


class ModelAgentDescriptor(object):

    def __init__(self,model):
        self.agent = ModelAgent(model)

    def __get__(self,instance,onwer):
        if instance is not None:
            raise AttributeError("ModelAgent is not accessible via %s instances" % instance)
        return self.agent


class Options(object):

    def __init__(self):
        self.model_name = None
        self.field_map = {}
        self.fields = None
        self.pk_field = None
        self.related_fields = {}


    def get_field(self,field_name):
        return self.field_map.get(field_name,None)

    def get_fields_name(self):
        return tuple(self.field_map.keys())

    def get_columns(self):
        return tuple(field.get_column() for field in self.fields)


class ModelMetaclass(type):

    def __new__(cls,cls_name,bases,attrs):
        parents = [base for base in bases if isinstance(base,ModelMetaclass)]
        # 排除Model class
        if not parents:
            return super(ModelMetaclass,cls).__new__(cls, cls_name, bases, attrs)
        model = super(ModelMetaclass, cls).__new__(cls, cls_name, bases, attrs)
        #收集Field
        field_mappings = {}
        for attr_name,attr in attrs.items():
            if isinstance(attr,Field):
                field_mappings[attr_name] = attr
        # 处理主键和关系字段
        pk_fields = []
        rel_fields = []
        for field_name,field in field_mappings.items():
            setattr(field,'model',model)
            if field.name is None:
                field.name = field_name
            if field.primary_key:
                pk_fields.append(field)
            elif field.is_related:
                rel_fields.append(field)
                setattr(model, field.name, RelatedDescriptor(model, field))
        if not pk_fields:
            field = PrimaryKey(column_name=PK_FIELD_NAME)
            field.name = PK_FIELD_NAME
            field_mappings[field.name] = field
            pk_fields.append(field)
        elif len(pk_fields) > 1:
            raise ModelException("A model can't have more than one primary key Field.")
        opts = Options()
        opts.pk_field = pk_fields[0]
        opts.related_fields = list(rel_fields)
        opts.model_name = cls_name
        opts.field_map = field_mappings
        opts.fields = tuple(field_mappings.values())
        model._opts = opts
        model.object = ModelAgentDescriptor(model)
        cls.object_bind_property(model,'DoesNotExists',
                                 tuple(base.DoesNotExists for base in bases if hasattr(base,"DoesNotExists"))
                                 or (ObjectNotExists,))
        cls.object_bind_property(model, 'MultiResult',
                                 tuple(base.MultiResult for base in bases if hasattr(base, "MultiResult"))
                                 or (MultiResult,))
        configuration.register_model(model)
        return model

    @staticmethod
    def check_fields(fields):
        for field in fields:
            field.check()

    @classmethod
    def object_bind_property(cls,object,name,bases):
        module = object.__module__
        attrs = {"__module__":module}
        attr = type(name,bases,attrs)
        setattr(object,name,attr)

class Model(object,metaclass=ModelMetaclass):

    def __init__(self,*args,**kwargs):
        #设置默认值
        fields = self._opts.fields
        init_field = []
        if len(args) > len(fields):
            raise IndexError("Number of args exceeds number of fields")
        if args:
            for field,value in zip(fields,args):
                if field.is_related:
                    if not isinstance(value,self.__class__):
                        raise TypeError("The field(%r) is a RelatedField , and the value must be a Model type" %
                                        (field.name,))
                setattr(self,field.name,value)
                init_field.append(field.name)
        for field in fields:
            if kwargs:
                try:
                    value = kwargs.pop(field.name)
                except KeyError:
                    if field.is_related:
                        try:
                            value = kwargs.pop(field.get_column())
                        except KeyError:
                            pass
                        else:
                            setattr(self,field.get_column(),value)
                            continue
                else:
                    setattr(self,field.name,value)
                    continue
            if field.name not in init_field:
                setattr(self, field.name, field.default)
        if kwargs:
            raise KeyError("%r does not belong to fields" % (list(kwargs),))

    def save(self,fields=None):
        if self.pk is None and fields:
            raise ModelException("'save()' method cannot update an object whose primary key is None")
        if fields:
            self.__class__.object._update_obj(object=self,fields=fields)
        elif self.pk:
            self.__class__.object._update_obj(object=self)
        else:
            self.__class__.object._insert(self)

    def delete(self):
        if self.pk is not None:
            self.__class__.object._delete_obj(self)
            self.pk = None

    @property
    def pk(self):
        return getattr(self,self.get_pk_name())

    @pk.setter
    def pk(self,value):
        setattr(self,self.get_pk_name(),value)

    @classmethod
    def get_pk_field(cls):
        return cls._opts.pk_field

    @classmethod
    def get_pk_name(cls):
        return cls._opts.pk_field.name

    def __eq__(self,other):
        pass

    def __repr__(self):
        attrs = ["%s:%s" % (k,v) for k,v in self.__dict__.items()]
        if len(attrs) > 6:
            attrs = attrs[:6]
            attrs[-1] = '...'
        return "<%s object: %s>" % (self.__class__.__name__, ','.join(attrs))

    def __str__(self):
        return "<%s object>" % self.__class__.__name__
 
