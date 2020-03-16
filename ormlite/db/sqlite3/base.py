import datetime
import sqlite3 as engine
from ormlite.exception import InvalidConfiguration


def parse_bool(value):
    value = value.decode('utf-8')
    return bool(int(value)) if value in ('0','1') else value


def time_converter(value):
    value = value.decode()
    return datetime.datetime.strptime(value,"%H:%M:%S.%f").time()


def time_adapter(value):
    if isinstance(value,datetime.time):
        return value.strftime("%H:%M:%S.%f")
    return value


engine.register_converter("BOOL",parse_bool)
engine.register_converter("TIME",time_converter)
engine.register_adapter(engine.Time,time_adapter)



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

#SQL标准规定字符串必须使用“单引号”,引用时标识符(如表名和列名)必须使用“双引号”
#sqlte3 使用的是双引号，同时sqlite3兼用mysql的 “反引号”
#所以这里统一使用反引号
