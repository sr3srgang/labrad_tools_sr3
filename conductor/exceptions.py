import traceback
import sys

class ConductorException(Exception):
    def __init__(self, message=None):
#        traceback.print_exc()
        super(ConductorException, self).__init__(message)

class ParameterImportError(ConductorException):
    pass

class ParameterNotActiveError(ConductorException):
    pass

class ParameterNotFoundError(ConductorException):
    pass

class ParameterValueNotFoundError(ConductorException):
    pass

class ParameterAlreadyActiveError(ConductorException):
    pass

class ParameterInitializationError(ConductorException):
    pass

class ParameterTerminationError(ConductorException):
    pass

class ParameterReloadError(ConductorException):
    pass

class ParameterAdvanceError(ConductorException):
    pass

class ParameterUpdateError(ConductorException):
    pass

class ParameterSetValueError(ConductorException):
    pass

class ParameterGetValueError(ConductorException):
    pass

class ExperimentAdvanceError(ConductorException):
    pass

class AlreadyAdvancingError(ConductorException):
    pass

class AdvanceError(ConductorException):
    pass
