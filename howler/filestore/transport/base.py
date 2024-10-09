from typing import AnyStr

from howler.common.exceptions import HowlerNotImplementedError
from howler.filestore.exceptions import TransportException


def normalize_srl_path(srl):
    if "/" in srl:
        return srl

    return "{0}/{1}/{2}/{3}/{4}".format(srl[0], srl[1], srl[2], srl[3], srl)


class Transport(object):
    """FileTransport base class.

    - Subclasses should override all methods.
    - Except as noted, FileTransport methods do not return value and raise
    - TransportException on failure.
    - Methods should only raise TransportExceptions. (The decorators
      Chain and ChainAll can be applied to a function/method and class,
      respectively, to ensure that any exceptions raised are converted to
      TransportExceptions.
    """

    def __init__(self, normalize=normalize_srl_path):
        self.normalize = normalize

    def close(self):
        pass

    def delete(self, path: str):
        """Deletes the file."""
        raise TransportException("Not Implemented", HowlerNotImplementedError())

    def exists(self, path: str) -> bool:
        """Returns True if the path exists, False otherwise.
        Should work with both files and directories.
        """
        raise TransportException("Not Implemented", HowlerNotImplementedError())

    def makedirs(self, path: str):
        """Like os.makedirs the super-mkdir, create the leaf directory path and
        any intermediate path segments.
        """
        raise TransportException("Not Implemented", HowlerNotImplementedError())

    # File based functions
    def download(self, src_path: str, dst_path: str):
        """Copies the content of the filestore src_path to the local dst_path."""
        raise TransportException("Not Implemented", HowlerNotImplementedError())

    def upload(self, src_path: str, dst_path: str):
        """Save upload source file src_path to to the filesotre dst_path, overwriting dst_path if it already exists."""
        raise TransportException("Not Implemented", HowlerNotImplementedError())

    # Buffer based functions
    def get(self, path: str) -> bytes:
        """Returns the content of the file."""
        raise TransportException("Not Implemented", HowlerNotImplementedError())

    def put(self, dst_path: str, content: AnyStr):
        """Put the content of the file in memory directly to the filestore dst_path"""
        raise TransportException("Not Implemented", HowlerNotImplementedError())
