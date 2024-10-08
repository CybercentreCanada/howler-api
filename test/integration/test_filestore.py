import os
import re
import tempfile
from urllib.parse import urlparse

import pytest
import requests

from howler.filestore import FileStore
from howler.filestore.transport.base import TransportException

_temp_body_a = b"temporary file string"


def create_fs(url, skip_liveness_check=False, **kwargs):
    parsed = urlparse(url)
    if not skip_liveness_check:
        get_url = "http://" + re.sub(r"^.+@(.+)$", r"\1", parsed.netloc) + parsed.path
        try:
            requests.get(get_url)
        except requests.ConnectionError:
            pytest.skip(f"{get_url} is not accessible")

    return FileStore(url, **kwargs)


def test_azure():
    """
    Azure filestore by downloading a file from our public storage blob
    """
    fs = create_fs("azure://alpytest.blob.core.windows.net/pytest/", connection_attempts=2)
    assert fs.exists("test")
    assert fs.get("test") is not None
    with pytest.raises(TransportException):
        fs.put("bob", "bob")


def test_http():
    """
    Test HTTP FileStore by fetching the assemblyline page on
    CSE's cyber center page.
    """
    fs = create_fs("http://github.com/CybercentreCanada/")
    assert "github.com" in str(fs)
    httpx_tests(fs)


def test_https():
    """
    Test HTTPS FileStore by fetching the assemblyline page on
    CSE's cyber center page.
    """
    fs = create_fs("https://github.com/CybercentreCanada/")
    assert "github.com" in str(fs)
    httpx_tests(fs)


def httpx_tests(fs):
    assert fs.exists("assemblyline-base")
    assert fs.get("assemblyline-base")
    with tempfile.TemporaryDirectory() as temp_dir:
        local_base = os.path.join(temp_dir, "base")
        fs.download("assemblyline-base", local_base)
        assert os.path.exists(local_base)


# def test_sftp():
#     """
#     Test SFTP FileStore by fetching the readme.txt file from
#     Rebex test server.
#     """
#     fs = FileStore("sftp://demo:password@test.rebex.net")
#     assert fs.exists("readme.txt") != []
#     assert fs.get("readme.txt") is not None


def test_file():
    """
    Test Local FileStore by fetching the README.md file from
    the cccs common repo directory.

    Note: This test will fail if pytest is not ran from the root
          of the cccs common repo.
    """
    fs = create_fs("file://%s" % os.path.dirname(__file__), skip_liveness_check=True)
    assert fs.exists(os.path.basename(__file__)) != []
    assert fs.get(os.path.basename(__file__)) is not None

    with tempfile.TemporaryDirectory() as temp_dir:
        with FileStore("file://" + temp_dir) as fs:
            common_actions(fs)


# This currently doesn't run on WSL, commenting out until we actually use S3
# def test_s3():
#     """
#     Test Amazon S3 FileStore by fetching a test file from
#     the assemblyline-support bucket on Amazon S3.
#     """
#     fs = FileStore(
#         "s3://AKIAIIESFCKMSXUP6KWQ:Uud08qLQ48Cbo9RB7b+H+M97aA2wdR8OXaHXIKwL@"
#         "s3.amazonaws.com/?s3_bucket=assemblyline-support&aws_region=us-east-1"
#     )
#     assert fs.exists("al4_s3_pytest.txt") != []
#     assert fs.get("al4_s3_pytest.txt") is not None


def test_minio():
    """
    Test Minio FileStore by pushing and fetching back content from it.
    """
    content = b"THIS IS A MINIO TEST"

    fs = create_fs("s3://hwl_storage_key:Ch@ngeTh!sPa33w0rd@localhost:9000/?s3_bucket=test&use_ssl=False")
    assert fs.delete("al4_minio_pytest.txt") is None
    assert fs.put("al4_minio_pytest.txt", content) != []
    assert fs.exists("al4_minio_pytest.txt") != []
    assert fs.get("al4_minio_pytest.txt") == content
    assert fs.delete("al4_minio_pytest.txt") is None


def common_actions(fs):
    # Write and read file body directly
    fs.put("put", _temp_body_a)
    assert fs.get("put") == _temp_body_a

    # Write a file body by batch upload
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_a = os.path.join(temp_dir, "a")
        with open(temp_file_a, "wb") as handle:
            handle.write(_temp_body_a)
        temp_file_b = os.path.join(temp_dir, "a")
        with open(temp_file_b, "wb") as handle:
            handle.write(_temp_body_a)

        failures = fs.upload_batch([(temp_file_a, "upload/a"), (temp_file_b, "upload/b")])
        assert len(failures) == 0, failures
        assert fs.exists("upload/a")
        assert fs.exists("upload/b")

        # Read a file body by download
        temp_file_name = os.path.join(temp_dir, "scratch")
        fs.download("upload/b", temp_file_name)
        assert open(temp_file_name, "rb").read() == _temp_body_a

    assert fs.exists("put")
    fs.delete("put")
    assert not fs.exists("put")
