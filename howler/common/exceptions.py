from inspect import getmembers, isfunction
from sys import exc_info
from traceback import format_tb
from typing import Optional


class HowlerException(Exception):
    """Wrapper for all exceptions thrown in howler's code"""

    message: str
    cause: Exception

    def __init__(
        self, message: str = "Something went wrong", cause: Optional[Exception] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.cause = cause

    def __repr__(self) -> str:
        return self.message


class InvalidClassification(HowlerException):
    pass


class InvalidDefinition(HowlerException):
    pass


class InvalidRangeException(HowlerException):
    pass


class NonRecoverableError(HowlerException):
    pass


class RecoverableError(HowlerException):
    pass


class ConfigException(HowlerException):
    pass


class ResourceExists(HowlerException):
    pass


class VersionConflict(HowlerException):
    def __init__(
        self, message: str = "Something went wrong", cause: Optional[Exception] = None
    ) -> None:
        HowlerException.__init__(self, message, cause)


class HowlerTypeError(HowlerException, TypeError):
    def __init__(
        self, message: str = "Something went wrong", cause: Optional[Exception] = None
    ) -> None:
        HowlerException.__init__(
            self, message, cause if cause is not None else TypeError(message)
        )


class HowlerAttributeError(HowlerException, AttributeError):
    def __init__(
        self, message: str = "Something went wrong", cause: Optional[Exception] = None
    ) -> None:
        HowlerException.__init__(
            self, message, cause if cause is not None else AttributeError(message)
        )


class HowlerValueError(HowlerException, ValueError):
    def __init__(
        self, message: str = "Something went wrong", cause: Optional[Exception] = None
    ) -> None:
        HowlerException.__init__(
            self, message, cause if cause is not None else ValueError(message)
        )


class HowlerNotImplementedError(HowlerException, NotImplementedError):
    def __init__(
        self, message: str = "Something went wrong", cause: Optional[Exception] = None
    ) -> None:
        HowlerException.__init__(
            self, message, cause if cause is not None else NotImplementedError(message)
        )


class HowlerKeyError(HowlerException, KeyError):
    def __init__(
        self, message: str = "Something went wrong", cause: Optional[Exception] = None
    ) -> None:
        HowlerException.__init__(
            self, message, cause if cause is not None else KeyError(message)
        )


class HowlerRuntimeError(HowlerException, RuntimeError):
    def __init__(
        self, message: str = "Something went wrong", cause: Optional[Exception] = None
    ) -> None:
        HowlerException.__init__(
            self, message, cause if cause is not None else RuntimeError(message)
        )


class NotFoundException(HowlerException):
    pass


class AccessDeniedException(HowlerException):
    pass


class InvalidDataException(HowlerException):
    pass


class AuthenticationException(HowlerException):
    pass


class Chain(object):
    """
    This class can be used as a decorator to override the type of exceptions returned by a function
    """

    def __init__(self, exception):
        self.exception = exception

    def __call__(self, original):
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
        try:
            return func(*args, **kwargs)
        except Exception as e:
            wrapped = self.exception(str(e), e)
            raise wrapped.with_traceback(exc_info()[2])


class ChainAll:
    """
    This class can be used as a decorator to override the type of exceptions returned by every method of a class
    """

    def __init__(self, exception):
        self.exception = Chain(exception)

    def __call__(self, cls):
        """We can use an instance of this class as a decorator."""
        for method in getmembers(cls, predicate=isfunction):
            setattr(cls, method[0], self.exception(method[1]))

        return cls


def get_stacktrace_info(ex: Exception) -> str:
    return "".join(
        format_tb(exc_info()[2]) + [": ".join((ex.__class__.__name__, str(ex)))]
    )
