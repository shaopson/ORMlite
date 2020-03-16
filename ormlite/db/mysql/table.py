from ormlite.fields import FieldException
from .base import Database


class TableExisted(Exception):
    pass


class Table():
    column_types = Database.column_types
    TableExisted = TableExisted

    def __init__(self,model):
        self.model = model

    def get_definition(self,field):
        sql = []
        column_type = self.column_types.get(field.get_type())
        if not column_type:
            raise FieldException("%s Unknown field type:%s" % (field,field.get_type()))
        elif column_type.find("max_length") > 0:
            column_type = column_type % {"max_length":field.max_length}
        sql.append(column_type)
        if field.default is not None:
            sql.append("DEFAULT %s" % field.to_sql(field.default))
        if field.unique:
            sql.append("UNIQUE")
        if field.null is False:
            sql.append("NOT NULL")
        return " ".join(sql)

    def get_constraint(self,fk):
        field = fk
        rel_model = field.get_related_model()
        rel_field = field.get_related_field()
        const_name = "fk_%s_%s_%s_%s" % (self.model._opts.model_name, field.name,
                        rel_model._opts.model_name, rel_field.name)
        constraint = "CONSTRAINT `%s` FOREIGN KEY(`%s`) REFERENCES `%s`(`%s`) ON UPDATE %s ON DELETE %s" % (
                            const_name, field.get_column(), rel_model._opts.model_name,rel_field.get_column(),
                            field.on_update,field.on_delete)
        return constraint

    def as_sql_create(self):
        table = []
        table_name = self.model._opts.model_name
        primary_key = []
        foreign_key = []
        for field in self.model._opts.fields:
            definition = self.get_definition(field)
            table.append("`%s` %s" % (field.get_column(),definition))
            if field.primary_key:
                primary_key.append(field)
            elif field.is_related:
                foreign_key.append(field)
        if primary_key:
            pks = (self.quote(f.get_column()) for f in primary_key)
            table.append("PRIMARY KEY(%s)" % ",".join(pks))
        if foreign_key:
            for field in foreign_key:
                constraint = self.get_constraint(field)
                table.append(constraint)
        sql = "CREATE TABLE IF NOT EXISTS `%s` (\r\n\t%s\r\n);" % (table_name,",\r\n\t".join(table))
        return sql

    def as_sql_delete(self):
        sql = "DROP TABLE `%s`;" % self.model._opts.model_name
        return sql

    def create(self,connection):
        if self.is_existed(connection):
            raise self.TableExisted("Create fail! <Table:%s> existed" % self.model._opts.model_name)
        sql = self.as_sql_create()
        print(sql)
        cursor = connection.cursor()
        cursor.execute(sql)
        connection.commit()

    def is_existed(self,connection):
        sql = 'SHOW TABLES LIKE %s'
        cursor = connection.cursor()
        cursor.execute(sql,(self.model._opts.model_name,))
        result = cursor.fetchall()
        cursor.close()
        if result:
            return True
        return False

    def quote(self,name):
        return "`%s`" % name


