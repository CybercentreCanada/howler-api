from typing import Optional

from howler.common.exceptions import HowlerException


class FileStoreException(HowlerException):
    pass


class CorruptedFileStoreException(HowlerException):
    pass


class TransportException(HowlerException):
    """FileTransport exception base class.

    TransportException is a subclass of HowlerException so that it can be
    used with the Chain and ChainAll decorators.
    """

    pass


class HowlerConnectionError(HowlerException, ConnectionError):
    def __init__(self, message: str = "Something went wrong", cause: Optional[Exception] = None) -> None:
        HowlerException.__init__(self, message, cause if cause is not None else ConnectionError(message))
