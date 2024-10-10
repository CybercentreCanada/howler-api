from inspect import getmembers, isfunction
from sys import exc_info
from traceback import format_tb
from typing import Optional


class HowlerException(Exception):
    """Wrapper for all exceptions thrown in howler's code"""

    message: str
    cause: Optional[Exception]

    def __init__(self, message: str = "Something went wrong", cause: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.message = message
        self.cause = cause

    def __repr__(self) -> str:
        """String reproduction of the howler exception. Pass the message on"""
        return self.message


class InvalidClassification(HowlerException):
    """Exception for Invalid Classification"""

    pass


class InvalidDefinition(HowlerException):
    """Exception for Invalid Definition"""

    pass


class InvalidRangeException(HowlerException):
    """Exception for Invalid Range"""

    pass


class NonRecoverableError(HowlerException):
    """Exception for an unrecoverable error"""

    pass


class RecoverableError(HowlerException):
    """Exception for a recoverable error"""

    pass


class ConfigException(HowlerException):
    """Exception thrown due to invalid configuration"""

    pass


class ResourceExists(HowlerException):
    """Exception thrown due to a pre-existing resource"""

    pass


class VersionConflict(HowlerException):
    """Exception thrown due to a version conflict"""

    def __init__(self, message: str = "Something went wrong", cause: Optional[Exception] = None) -> None:
        HowlerException.__init__(self, message, cause)


class HowlerTypeError(HowlerException, TypeError):
    """TypeError child specifically for exceptions thrown by us"""

    def __init__(self, message: str = "Something went wrong", cause: Optional[Exception] = None) -> None:
        HowlerException.__init__(self, message, cause if cause is not None else TypeError(message))


class HowlerAttributeError(HowlerException, AttributeError):
    """AttributeError child specifically for exceptions thrown by us"""

    def __init__(self, message: str = "Something went wrong", cause: Optional[Exception] = None) -> None:
        HowlerException.__init__(self, message, cause if cause is not None else AttributeError(message))


class HowlerValueError(HowlerException, ValueError):
    """ValueError child specifically for exceptions thrown by us"""

    def __init__(self, message: str = "Something went wrong", cause: Optional[Exception] = None) -> None:
        HowlerException.__init__(self, message, cause if cause is not None else ValueError(message))


class HowlerNotImplementedError(HowlerException, NotImplementedError):
    """NotImplementedError child specifically for exceptions thrown by us"""

    def __init__(self, message: str = "Something went wrong", cause: Optional[Exception] = None) -> None:
        HowlerException.__init__(self, message, cause if cause is not None else NotImplementedError(message))


class HowlerKeyError(HowlerException, KeyError):
    """KeyError child specifically for exceptions thrown by us"""

    def __init__(self, message: str = "Something went wrong", cause: Optional[Exception] = None) -> None:
        HowlerException.__init__(self, message, cause if cause is not None else KeyError(message))


class HowlerRuntimeError(HowlerException, RuntimeError):
    """RuntimeError child specifically for exceptions thrown by us"""

    def __init__(self, message: str = "Something went wrong", cause: Optional[Exception] = None) -> None:
        HowlerException.__init__(self, message, cause if cause is not None else RuntimeError(message))


class NotFoundException(HowlerException):
    """Exception thrown when a resource cannot be found"""

    pass


class AccessDeniedException(HowlerException):
    """Exception thrown when a resource cannot be accessed by a user"""

    pass


class InvalidDataException(HowlerException):
    """Exception thrown when user-provided data is invalid"""

    pass


class AuthenticationException(HowlerException):
    """Exception thrown when a user cannot be authenticated"""

    pass


class Chain(object):
    """This class can be used as a decorator to override the type of exceptions returned by a function"""

    def __init__(self, exception):
        self.exception = exception

    def __call__(self, original):
        """Execute a function and wrap any resulting exceptions"""

        def wrapper(*args, **kwargs):
            try:
                return original(*args, **kwargs)
            except Exception as e:
                wrapped = self.exception(str(e), e)
                raise wrapped.with_traceback(exc_info()[2])

        wrapper.__name__ = original.__name__
        wrapper.__doc__ = original.__doc__
        wrapper.__dict__.update(original.__dict__)

        return wrapper

    def execute(self, func, *args, **kwargs):
        """Execute a function and wrap any resulting exceptions"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            wrapped = self.exception(str(e), e)
            raise wrapped.with_traceback(exc_info()[2])


class ChainAll:
    """This class can be used as a decorator to override the type of exceptions returned by every method of a class"""

    def __init__(self, exception):
        self.exception = Chain(exception)

    def __call__(self, cls):
        """We can use an instance of this class as a decorator."""
        for method in getmembers(cls, predicate=isfunction):
            setattr(cls, method[0], self.exception(method[1]))

        return cls


def get_stacktrace_info(ex: Exception) -> str:
    """Get and format traceback information from a given exception"""
    return "".join(format_tb(exc_info()[2]) + [": ".join((ex.__class__.__name__, str(ex)))])
