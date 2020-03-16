import datetime

try:
    import mysql.connector
except ModuleNotFoundError:
    raise ModuleNotFoundError("No module named 'mysql',you may need to install 'mysql-connector' or 'mysql-connector-python'")

from ormlite.exception import InvalidConfiguration


class Database(object):

    name = 'mysql'

    column_types = {
        'BinaryField': 'BLOB',
        'BooleanField': 'BOOL',
        'CharField': 'VARCHAR(%(max_length)s)',
        'DateField': 'DATE',
        'DateTimeField': 'DATETIME',
        'DecimalField': 'DECIMAL',
        'FloatField': 'DOUBLE',
        'IntegerField': 'INTEGER',
        'BigIntegerField': 'BIGINT',
        'SmallIntegerField': 'SMALLINT',
        'TextField': 'TEXT',
        'TimeField': 'TIME',
        "PrimaryKey": "INTEGER AUTO_INCREMENT"
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
    placeholder = "%s"


    def __init__(self,config):
        self.config = config
        self.connector = None
        self.engine = mysql.connector

    def get_connection_params(self):
        if not self.config['NAME']:
            raise InvalidConfiguration("ORMLite.set_db config invaild")
        kwargs = {
            'database': self.config['NAME'],
            'user': self.config["USER"],
            'password': self.config["PASSWORD"],
            'host': self.config["HOST"],
            'port': self.config["PORT"]
        }
        if "OPTIONS" in self.config:
            kwargs.update(self.config['OPTIONS'])
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

