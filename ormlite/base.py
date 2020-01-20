from importlib import import_module
from ormlite.exception import ORMLiteException
from ormlite.compiler import Compiler

class Configuration(object):

    def __init__(self):
        self.db_config = {}
        self.db_engine = None
        self.db = None
        self.compiler = None

    def conf_db(self,config):
        self.db_config = config
        if 'ENGINE' not in config:
            raise ORMLiteException("conf_db method 'config' parameter missing 'ENGINE'")
        self.db_engine = import_module(config["ENGINE"])
        self.db = self.db_engine.base.Database(config)
        self.compiler = Compiler(self.db)


configuration = Configuration()

