#from ormlite.base import configuration
from ormlite.exception import CompileError
from ormlite.fields import ForeignKey,RelatedField

# def get_compiler():
#     db = configuration.db
#     return Compiler(db)


class Compiler(object):

    def __init__(self,db):
        self.db = db
        self.operators = db.operators
        self.placeholder = db.placeholder
        self.mappings = {
            "UPDATE":self._compile_update,
            "SELECT":self._compile_select,
            "INSERT":self._compile_insert,
            "DELETE":self._compile_delete,
            "WHERE":self._compile_where
        }

    def compile(self,obj):
        statement = getattr(obj,"statement",None)
        _compile = self.mappings.get(statement,None)
        if _compile:
            return _compile(obj)
        elif hasattr(obj, "as_sql"):
            return obj.as_sql()
        else:
            raise CompileError("Objects that cannot be compiled:%s" % obj)

    def _compile_condition(self,conditions):
        sql = []
        params = []
        for k,v in conditions.items():
            if k.find("__") > 0:
                name,symbol = k.split("__")
            else:
                name,symbol = k,'eq'
            op = self.operators.get(symbol)
            if symbol == "in":
                op = op % (",".join(self.placeholder*len(v)))
                params.extend(v)
            elif symbol == "range":
                op = op % (self.placeholder,self.placeholder)
                params.extend(v)
            else:
                op = op % self.placeholder
                params.append(v)
            sql.append("%s %s" % (name, op))
        return " AND ".join(sql),params

    def _compile_where(self,where):
        sql = []
        params = []
        for node in where.buf:
            if isinstance(node, where.__class__):
                _sql,_params = self._compile_where(node)
                sql.append(_sql)
                params.extend(_params)
            elif isinstance(node, dict):
                _sql,_params = self._compile_condition(node)
                sql.append(_sql)
                params.extend(_params)
            else:
                sql.append(node)
        return "".join(sql),tuple(params)

    def _compile_insert(self,insert):
        table = insert.table
        instance = insert.instance
        fields = []
        params = []
        for attr, field in instance.__fields__.items():
            print(attr,field)
            if isinstance(field, RelatedField):
                related_obj = getattr(instance,attr)
                value = related_obj.pk if hasattr(related_obj,"pk") else related_obj
            elif attr.endswith("_id") or attr.endswith("_pk"):
                value = getattr(instance, attr)
                attr = attr[:-3]
            else:
                value = getattr(instance, attr)
                value = field.adapt(value)
            # if field.auto:
            #     value = field.auto(value)
            fields.append('"%s"' % attr)
            params.append(value)
        sql = 'INSERT INTO "%s" (%s) VALUES (%s);' % (table, ",".join(fields), ",".join(self.placeholder * len(params)))
        return sql,tuple(params)

    def _compile_delete(self,delete):
        table = delete.table
        instance = delete.instance
        where = None
        if instance:
            if instance.pk is None:
                raise ValueError("%s primary key is invalid" % instance)
            delete.add_where({instance.pk_name:instance.pk})
        if delete.where:
            where = delete.where
        else:
            raise CompileError("Delete object's 'where' attribute cannot be empty")
        where_sql,where_params = self._compile_where(where)
        sql = 'DELETE FROM "%s" WHERE %s' % (table, where_sql)
        return sql,tuple(where_params)

    def _compile_update(self,update):
        instance = update.instance
        sql = ['UPDATE "%s" SET' % update.table]
        update_fields = {}
        params = []
        if instance:
            if instance.pk is None:
                raise CompileError("%s primary key is invalid" % instance)
            update.add_where({instance.pk_name: instance.pk})
            if update.fields:
                for field_name in update.fields:
                    update_fields[field_name] = self.placeholder
                    value = getattr(instance,field_name)
                    params.append(value)
            else:
                for field_name, field in instance.__fields__.items():
                    #跳过主键
                    if field_name == instance.pk_name:
                        continue
                    # 如果是关系对象或有时间对象需要自动更新时间 [待处理]
                    value = getattr(instance, field_name)
                    update_fields[field_name] = self.placeholder
                    params.append(value)
        elif update.update_fields:
            for field_name, value in update.update_fields.items():
                update_fields[field_name] = self.placeholder
                params.append(value)
        else:
            raise CompileError("No fields need update")
        columns = ['"%s" = %s' % (k, v) for k, v in update_fields.items()]
        sql.append(','.join(columns))
        where = update.where
        if where:
            sql.append("WHERE")
            where_sql, where_params = self._compile_where(where)
            sql.append(where_sql)
            params.extend(where_params)
        sql.append(";")
        sql = " ".join(sql)
        return sql, tuple(params)

    def _compile_select(self,query):
        sql = ['SELECT']
        params = []
        if query.distinct:
            sql.append("DISTINCT")
        fields = [self.quote(f) for f in query.fields]
        if query.alias:
            query.fields.extend(query.alias.keys())
            alias = (self.alias_field(v,k) for k, v in query.alias.items())
            fields.extend(alias)
        sql.append(', '.join(fields))
        sql.append('FROM "%s"' % query.table)
        if query.where:
            sql.append("WHERE")
            where_sql, where_params = self._compile_where(query.where)
            sql.append(where_sql)
            params.extend(where_params)
        if query.groupby:
            sql.append("GROUP BY %s" % ', '.join((self.quote(f) for f in query.groupby)))
        if query.orderby:
            orderby = []
            for field_name in query.orderby:
                if field_name.startswith("-"):
                    field_name = field_name[1:]
                    orderby.append(self.quote(field_name) + " DESC")
                else:
                    orderby.append(self.quote(field_name))
            sql.append("ORDER BY %s" % ', '.join((f for f in orderby)))
        if query.limit is not None:
            if isinstance(query.limit, slice):
                start = query.limit.start or 0
                length = query.limit.stop or -1 # max length
                sql.append("LIMIT %s OFFSET %s" % (length, start))
            elif isinstance(query.limit, int):
                sql.append("LIMIT 1 OFFSET %s" % query.limit)
        sql.append(";")
        sql = ' '.join(sql)
        return sql, tuple(params)

    def quote(self,name):
        return '"%s"' % name

    def alias_field(self,o,l):
        if o.find('"') >= 0:
            return '%s AS "%s"' % (o,l)
        return '"%s" AS "%s"' % (o,l)






