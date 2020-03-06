import logging
from importlib import import_module
from ormlite.exception import ORMLiteException
from ormlite.compiler import Compiler

class Configuration(object):

    def __init__(self):
        self.db_config = {}
        self.db_engine = None
        self.db = None
        self.compiler = None
        self.logger = None
        self._debug = False
        self.models = {}

    def conf_db(self,config):
        if 'ENGINE' not in config:
            raise ORMLiteException("conf_db method 'config' parameter missing 'ENGINE'")
        self.db_config = config
        self.db_engine = import_module(config["ENGINE"])
        self.db = self.db_engine.base.Database(config)
        self.compiler = Compiler(self.db)

    def set_logger(self,logger):
        self.logger = logger

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self,value):
        self._debug = value
        if self._debug and not self.logger:
            self.logger = logging

    def register_model(self,model):
        key = "%s.%s" % (model.__module__, model._opts.model_name)
        self.models[key] = model

    def get_model(self,module,model_name):
        key = "%s.%s" % (module, model_name)
        return self.models.get(key,None)


configuration = Configuration()

