import datetime
from ormlite.exception import CompileError


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
        fields = instance._opts.fields
        columns = []
        params = []
        for field in fields:
            if field.is_related:
                obj = getattr(instance,field.name,None)
                if obj is not None:
                    value = obj.pk
                else:
                    value = getattr(instance,field.get_column(),None)
            else:
                value = getattr(instance,field.name,None)
                if value is None and hasattr(field,"on_insert"):
                    value = field.on_insert()
                    setattr(instance,field.name,value)
                value = field.adapt(value)
            columns.append('"%s"' % field.get_column())
            params.append(value)
        sql = 'INSERT INTO "%s" (%s) VALUES (%s);' % (table, ",".join(columns), ",".join(self.placeholder * len(params)))
        return sql,tuple(params)

    def _compile_delete(self,delete):
        table = delete.table
        instance = delete.instance
        where = None
        if instance:
            if instance.pk is None:
                raise ValueError("%s primary key is invalid" % instance)
            delete.add_where({instance.get_pk_name():instance.pk})
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
        update_columns = {}
        params = []
        if instance:
            if instance.pk is None:
                raise CompileError("%s primary key is invalid" % instance)
            update.add_where({instance.get_pk_field().name: instance.pk})
            if update.fields:
                for field_name in update.fields:
                    update_columns[field_name] = self.placeholder
                    value = getattr(instance,field_name)
                    params.append(value)
            else:
                for field in instance._opts.fields:
                    #跳过主键
                    if field.primary_key:
                        continue
                    # 如果是关系对象或有时间对象需要自动更新时间 [待处理]
                    if field.is_related:
                        obj = getattr(instance,field.name,None)
                        value = obj.pk if obj else getattr(instance,field.get_column(),None)
                    else:
                        value = getattr(instance, field.name)
                    update_columns[field.get_column()] = self.placeholder
                    params.append(value)
        elif update.update_fields:
            for field_name, value in update.update_fields.items():
                update_columns[field_name] = self.placeholder
                params.append(value)
        else:
            raise CompileError("No fields need update")
        expressions = ['"%s" = %s' % (k, v) for k, v in update_columns.items()]
        sql.append(','.join(expressions))
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
        columns = []
        aliases = []
        if query.fields:
            for field_name in query.fields:
                field = query.model._opts.get_field(field_name)
                if field:
                    column = field.get_column()
                    if field.is_related:
                        aliases.append(self.alias_column(column,field.name))
                    else:
                        columns.append(column)
                else:
                    columns.append(field_name)

        if query.distinct:
            sql.append("DISTINCT")
        if query.alias:
            aliases.extend(self.alias_column(v,k) for k, v in query.alias.items())
            columns.extend(aliases)
        sql.append(', '.join(columns))
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
            for column in query.orderby:
                if column.startswith("-"):
                    column = column[1:]
                    orderby.append(self.quote(column) + " DESC")
                else:
                    orderby.append(self.quote(column))
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

    def alias_column(self,o,l):
        if o.find('"') >= 0:
            return '%s AS "%s"' % (o,l)
        return '"%s" AS "%s"' % (o,l)






