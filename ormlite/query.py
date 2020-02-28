from ormlite import fields,exception
from ormlite.base import configuration
from ormlite.query import Query,Insert,Update,Delete,Where

class ModelAgent(object):

    AccessorError = exception.AccessorError

    def __init__(self, model, instance=None):
        self.model = model
        self.table = model.__table__
        self._instance = instance
        self.fields = list(model.__fields__.keys())

    def create(self,**kwargs):
        obj = self.model(**kwargs)
        obj.save()
        return obj

    def get_or_create(self,**kwargs):
        try:
           return self.get(**kwargs)
        except self.model.NotExists:
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

    def values(self,*fields,flat=False):
        return Query(self.model,fields=self.fields).values(*fields,flat=flat)

    def items(self,*fields,**kwargs):
        return Query(self.model,fields=self.fields).items(*fields,**kwargs)

    def count(self):
        return Query(self.model).count()

    def update(self, **kwargs):
        return Update(model=self.model,update_fields=kwargs).execute()

    def _insert(self,obj):
        if not isinstance(obj,self.model):
            raise TypeError("Argument 'obj' should be %s type" % self.model)
        insert = Insert(model=self.model,instance=obj)
        insert.execute()
        obj.pk = insert.get_id()

    def _update_obj(self,obj,fields):
        if not isinstance(obj,self.model):
            raise TypeError("Argument 'obj' should be %s type" % self.model)
        if obj.pk is None:
            raise AttributeError("%s primary key '%s' field value is invalid:%s" % (obj,obj.pk_name,obj.pk) )
        Update(model=self.model,instance=obj,fields=fields).execute()

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


class ModelMetaclass(type):

    def __new__(cls,name,bases,attrs):
        parents = [base for base in bases if isinstance(base,ModelMetaclass)]
        # 排除Model class
        if not parents:
            return super(ModelMetaclass,cls).__new__(cls, name, bases, attrs)
        #收集Field
        field_mappings = {}
        for attr_name,attr in attrs.items():
            if isinstance(attr,fields.Field):
                field_mappings[attr_name] = attr
        # 处理主键和关系字段
        pk_fields = []
        for field_name,field in field_mappings.items():
            if not field.name:
                field.name = field_name
            if field.primary_key:
                pk_fields.append(field)
            elif isinstance(field,fields.RelatedField):
                attrs[field_name] = fields.RelatedDescriptor(field)
        if not pk_fields:
            field = fields.PrimaryKey(name="id")
            field_mappings["id"] = field
            pk_fields.append(field)
        elif len(pk_fields) > 1:
            raise exception.ModelError("A model can't have more than one primary key Field.")
        attrs["__fields__"] = field_mappings
        attrs["__pk__"] = pk_fields[0]
        attrs["__table__"] = name
        model = super(ModelMetaclass,cls).__new__(cls,name,bases,attrs)
        model.object = ModelAgentDescriptor(model)
        setattr(model,"NotExists",exception.NotExists)
        setattr(model, "MultiResult", exception.MultiResult)
        return model

    @staticmethod
    def check_fields(field_mappings):
        for field in field_mappings.values():
            field.check()


class Model(object,metaclass=ModelMetaclass):

    def __init__(self,*args,**kwargs):
        #设置默认值
        fields = set(self.__fields__.keys())
        attrs = {}
        for attr,value in zip(fields,args):
            attrs[attr] = value
        if kwargs:
            for attr,value in kwargs.items():
                attrs[attr] = value
        no_init_field = fields - set(attrs.keys())
        for field_name in no_init_field:
            field = self.__fields__.get(field_name)
            default_value = getattr(field,"default",None)
            attrs[field_name] = default_value
        for attr,value in attrs.items():
            setattr(self,attr,value)


    def save(self):
        if self.pk is not None:
            self.__class__.object._update_obj(self,self.__fields__.keys())
        else:
            self.__class__.object._insert(self)

    def delete(self):
        if self.pk is not None:
            self.__class__.object._delete_obj(self)
            self.pk = None

    def update(self,*fields):
        if self.pk is None:
            raise AttributeError("%s primary key invalid " % self)
        self.__class__.object._update_obj(self,fields)


    @property
    def pk(self):
        return getattr(self,self.__pk__.name)

    @pk.setter
    def pk(self,value):
        setattr(self,self.__pk__.name,value)

    @property
    def pk_name(self):
        return self.__pk__.name

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
