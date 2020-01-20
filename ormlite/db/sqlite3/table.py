from ormlite.exception import FieldTypeError
from ormlite.fields import RelatedField
from .base import Database


class TableExisted(Exception):
    pass


class Table():
    column_types = Database.column_types
    TableExisted = TableExisted

    def __init__(self,model):
        self.model = model

    def get_column_define(self,field):
        sql = []
        column_type = self.column_types.get(field.get_type())
        if not column_type:
            raise FieldTypeError("%s Unknown field type:%s" % (field,field.get_type()))
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

    def as_sql_create(self):
        table = []
        table_name = self.model.__table__
        primary_key = []
        foreign_key = []
        for field in self.model.__fields__.values():
            column = self.get_column_define(field)
            table.append("'%s' %s" % (field.name,column))
            if field.primary_key:
                primary_key.append(repr(field.name))
            elif isinstance(field,RelatedField):
                foreign_key.append(field)
        if primary_key:
            table.append("PRIMARY KEY(%s)" % ",".join(primary_key))
        if foreign_key:
            constraint = []
            for field in foreign_key:
                constraint.append("FOREIGN KEY('%s') REFERENCES '%s'('%s')" % (
                field.name, field.related_model.__table__, field.related_field.name))
            table.append(",".join(constraint))
        sql = "CREATE TABLE IF NOT EXISTS %s (\r\n\t%s\r\n);" % (table_name,",\r\n\t".join(table))
        return sql

    def as_sql_delete(self):
        sql = "DROP TABLE %s;" % self.model.__table__
        return sql

    def create(self,connection):
        if self.is_existed(connection):
            raise self.TableExisted("Create fail! <Table:%s> existed" % self.model.__table__)
        sql = self.as_sql_create()
        print(sql)
        connection.execute(sql)
        connection.commit()

    def is_existed(self,connection):
        sql = 'SELECT "name" FROM sqlite_master WHERE "name" = "%s";' % self.model.__table__
        cursor = connection.execute(sql)
        result = cursor.fetchall()
        if result:
            return True
        return False


