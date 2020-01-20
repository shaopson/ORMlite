import sqlite3 as engine
from ormlite.exception import InvalidConfiguration

def row_to_dict(cursor,row):
    result = {}
    cols = cursor.description
    for col,value in zip(cols,row):
        result[col[0]] = value
    return result


def parse_bool(value):
    value = value.decode('utf-8')
    return bool(int(value)) if value in ('0','1') else value


engine.register_converter("BOOL",parse_bool)
engine.register_converter("bool",parse_bool)


class Database(object):

    name = 'sqlite3'

    column_types = {
        'BinaryField': 'BLOB',
        'BooleanField': 'BOOL',
        'CharField': 'VARCHAR(%(max_length)s)',
        'DateField': 'DATE',
        'DateTimeField': 'TIMESTAMP',
        'DecimalField': 'DECIMAL',
        'FloatField': 'REAL',
        'IntegerField': 'INTEGER',
        'BigIntegerField': 'BIGINT',
        'SmallIntegerField': 'SMALLINT',
        'TextField': 'TEXT',
        'TimeField': 'TIME',
        "PrimaryKey": "INTEGER"
    }

    operators = {
        'pk': "= %s",
        'id': "= %s",
        'eq': "= %s",
        'gt': "> %s",
        'ge': ">= %s",
        'lt': "< %s",
        'le': "<= %s",
        'not': "!= %s",
        'in': "IN (%s)",
        'range': "BETWEEN %s AND %s",
        'like': "LIKE %s",
        'contains': "LIKE %%%s%%",
        'startswith': "LIKE %s%%",
        'endswith': "LIKE %%%s"
    }
    placeholder = "?"


    def __init__(self,config):
        self.config = config
        self.connector = None
        self.engine = engine

    def get_connection_params(self):
        if not self.config['NAME']:
            raise InvalidConfiguration("ORMLite.set_db config invaild")
        kwargs = {
            'database': self.config['NAME'],
            'detect_types': engine.PARSE_DECLTYPES | engine.PARSE_COLNAMES,
        }
        if "OPTIONS" in self.config:
            kwargs.update(self.config['OPTIONS'])
        kwargs.update({'check_same_thread': False})
        return kwargs

    def get_connector(self):
        params = self.get_connection_params()
        return self.engine.connect(**params)

    def __enter__(self):
        if self.connector is None:
            self.connector = self.get_connector()
        return self.connector

    def __exit__(self, exc_type, exc_instance, traceback):
        if not exc_instance:
            self.connector.commit()
        else:
            self.connector.rollback()

    def close(self):
        self.connector.close()
        self.connector = None

