from ormlite import configuration
from . import Field,PrimaryKey


#外键约束
CASCADE = "CASCADE"
SET_NULL = "SET NULL"
NOT_ACTION = "NOT ACTION"
RESTRICT = "RESTRICT"


class RelatedField(Field):

    is_related = True

    def __init__(self,related_model,related_field,on_delete,*args,**kwargs):
        super(RelatedField,self).__init__(*args,**kwargs)
        self._rel_field = related_field
        self._rel_model = related_model
        self.on_update = CASCADE
        self.on_delete = on_delete
        self.related_model = None
        self.related_field = None

    def get_type(self):
        field = self.get_related_field()
        if isinstance(field,PrimaryKey):
            return "IntegerField"
        return field.get_type()

    def get_column(self):
        return self.name + "_id"

    def get_related_model(self):
        if self.related_model is not None:
            return self.related_model
        rel_model = self._rel_model
        if not isinstance(rel_model,str):
            self.related_model = rel_model
            return self.related_model
        if rel_model == "self":
            model = self.model
        else:
            model = configuration.get_model(self.model.__module__,rel_model)
        if model is not None:
            self.related_model = model
            return self.related_model
        return None

    def get_related_field(self):
        if self.related_field is not None:
            return self.related_field
        rel_model = self.get_related_model()
        if rel_model is None:
            return None
        rel_field = self._rel_field
        if not isinstance(rel_field,str):
            self.related_field = rel_field
            return self.related_field
        if rel_field == "pk":
            field = rel_model.get_pk_field()
        else:
            field = rel_model._opts.get_field(rel_field)
        if field is not None:
            self.related_field = field
            return self.related_field
        return None



class ForeignKey(RelatedField):
    #一对多 外键
    #关联的表必须只有一个主键，不能是组合主键
    def __init__(self,related_model,on_delete,*args,**kwargs):
        related_field = "pk"
        super(ForeignKey,self).__init__(related_model,related_field,on_delete,*args,**kwargs)


class RelatedDescriptor():

    def __init__(self,model,field):
        self.from_model = model
        self.from_field = field
        self._to_model = None
        self._to_field = None
        self.cache_name = "_%s_cache" % field.name


    @property
    def to_model(self):
        if self._to_model:
            return self._to_model
        else:
            self._to_model = self.from_field.get_related_model()
        return self._to_model

    @property
    def to_field(self):
        if self._to_field is not None:
            return self._to_field
        else:
            self._to_field = self.from_field.get_related_field()
        return self._to_field

    def __get__(self,instance,owner):
        if instance is None:
            return self.from_field # or self
        obj = getattr(instance,self.cache_name,None)
        if obj is not None:
            return obj
        rel_value = getattr(instance,self.from_field.get_column(),None)
        if rel_value is None:
            return None
        q = {
            self.to_field.name:rel_value
        }
        obj = self.to_model.object.get(**q)
        if obj:
            setattr(instance,self.cache_name,obj)
        return obj

    def __set__(self,instance,value):
        if value is None:
            setattr(instance, self.cache_name, None)
            return
        if not isinstance(value,self.to_field):
            raise ValueError('"%s.%s" must be a "%s" instance:%s' % (self.from_model._opts.model_name,
                                self.from_field.name,self.to_model._opts.model_name,value))
        setattr(instance,self.cache_name,value)
        setattr(instance,self.from_field.get_column(),value.pk)

    def __repr__(self):
        return "<RelatedDescriptor:%s>" % (self.from_field.name,)



