
class ORMLiteException(Exception):
    # ormlite base exception
    pass


class FieldException(ORMLiteException):
    # field base exception
    pass


class ModelException(ORMLiteException):
    # model base exception
    pass


class CompilerException(ORMLiteException):
    # compiler base exception
    pass


class NotExists(ModelException):
    # record not exists
    pass

class MultiResult(ModelException):
    pass


class FieldNameException(ORMLiteException):
    pass

class FieldTypeError(ORMLiteException):
    pass

class ModelError(ORMLiteException):
    pass

class RecordNotExists(ORMLiteException):
    pass

class MultiRecordError(ORMLiteException):
    pass

class CompileError(ORMLiteException):
    pass

class InvalidConfiguration(ORMLiteException):
    pass


class AccessorError(ORMLiteException):
    pass
