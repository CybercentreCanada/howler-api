import logging
import os
import shutil

from howler.common.exceptions import ChainAll, HowlerException
from howler.common.loader import APP_NAME
from howler.filestore.transport.base import (
    Transport,
    TransportException,
    normalize_srl_path,
)
from howler.utils.uid import get_random_id


@ChainAll(TransportException)
class TransportLocal(Transport):
    """Local file system Transport class."""

    def __init__(self, base=None, normalize=None):
        self.log = logging.getLogger(f"{APP_NAME}.transport.local")
        self.base = base
        self.host = "localhost"

        def local_normalize(path):
            # If they've provided an absolute path. Leave it a is.
            if path.startswith("/"):
                s = path
            # Relative paths
            elif "/" in path or len(path) != 64:
                s = _join(self.base, path)
            else:
                s = _join(self.base, normalize_srl_path(path))
            self.log.debug("local normalized: %s -> %s", path, s)
            return s

        if not normalize:
            normalize = local_normalize

        super(TransportLocal, self).__init__(normalize=normalize)

    def delete(self, path):
        path = self.normalize(path)
        os.unlink(path)

    def exists(self, path):
        path = self.normalize(path)
        return os.path.exists(path)

    def makedirs(self, path):
        path = self.normalize(path)
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno == 17:
                pass
            else:
                raise HowlerException(str(e), e)

    # File based functions
    def download(self, src_path, dst_path):
        if src_path == dst_path:
            return

        src_path = self.normalize(src_path)
        dir_path = os.path.dirname(dst_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        shutil.copy(src_path, dst_path)

    def upload(self, src_path, dst_path):
        dst_path = self.normalize(dst_path)
        if src_path == dst_path:
            return

        dirname = os.path.dirname(dst_path)
        filename = os.path.basename(dst_path)
        temp_name = get_random_id()
        temp_path = _join(dirname, temp_name)
        final_path = _join(dirname, filename)
        if final_path != dst_path:
            raise HowlerException(f"Final and destination paths do not match: {final_path} != {dst_path}")
        self.makedirs(dirname)
        shutil.copy(src_path, temp_path)
        shutil.move(temp_path, final_path)
        if not self.exists(dst_path):
            raise HowlerException(f"Destination path does not exist: {dst_path}")

    # Buffer based functions
    def get(self, path: str) -> bytes:
        path = self.normalize(path)
        fh = None
        try:
            fh = open(path, "rb")
            return fh.read()
        finally:
            if fh:
                fh.close()

    def put(self, path, content):
        path = self.normalize(path)

        dirname = os.path.dirname(path)
        filename = os.path.basename(path)

        temp_name = get_random_id()
        temp_path = _join(dirname, temp_name)

        final_path = _join(dirname, filename)

        if final_path != path:
            raise HowlerException(f"Final and expected path do not match: {final_path} != {path}")

        self.makedirs(dirname)
        fh = None
        try:
            fh = open(temp_path, "wb")
            return fh.write(content)
        finally:
            if fh:
                fh.close()

            try:
                shutil.move(temp_path, final_path)
            except shutil.Error:
                pass

            if not self.exists(path):
                raise HowlerException(f"Path does not exist: {path}")

    def __str__(self):
        return "file://{}".format(self.base)


###############################
# Helper functions.
###############################


def _join(base, path):
    path = path.replace("\\", "/").replace("//", "/")
    if base is None:
        return path
    return os.path.join(base, path.lstrip("/")).replace("\\", "/")
