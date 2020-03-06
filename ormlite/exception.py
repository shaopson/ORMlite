
class ORMLiteException(Exception):
    # ormlite base exception
    pass


class ModelException(Exception):
    pass


class CompilerException(Exception):
    pass


class FieldException(Exception):
    pass


class ObjectNotExists(Exception):
    pass


class MultiResult(Exception):
    pass


class ModelError(ORMLiteException):
    pass


class CompileError(ORMLiteException):
    pass

class InvalidConfiguration(ORMLiteException):
    pass

class ModelAgentError(ORMLiteException):
    pass
