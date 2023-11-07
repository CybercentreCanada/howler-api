# Filestore support

This library offers support for multiple different file storage types under a common API. This allows you to change the file storage type without having to change any code. The filestore uses a URL based configuration for each storage where the storage type is determined by the scheme of the URL.

## Multi-location file storage

The file storage interface also supports multiple location storage that way you can have the most recent files on faster storage and the archives on slower long term storage. When performing a file operation (download/upload/...) on the filestore, it will try each location in order but you can also tell it on which node to perform the operation on.

Node location:

- **Near**: first node only
- **Far**: Last node only
- **All**: Will check all nodes (default)

![Filestore Locations](filestore_location.svg)

## Supported Storage types

These are the currently supported type of storage for the filestore with an example of URL to use in your configuration file  :

- HTTP/HTTPS (Read Only)

        # HTTP
        http://{USER}:{PASSWORD}@domain.tld:80/path/to/folder

        # HTTPS
        https://{USER}:{PASSWORD}@domain.tld:443/path/to/folder

- FTP/FTPS

        # FTP
        ftp://{USER}:{PASSWORD}@domain.tld:21/path/to/folder

        # FTPS
        ftps://{USER}:{PASSWORD}@domain.tld:990/path/to/folder

- SFTP

        sftp://{USER}:{PASSWORD}@domain.tld/path/to/folder?private_key=...&private_key_pass=...&validate_host=true

- Amazon S3 or S3 compatible

        # Amazon
        s3://{USER}:{PASSWORD}@s3.amazonaws.com/path/to/folder?aws_region={REGION}&s3_bucket={STORAGE_NAME}

        # S3 Compatible (Minio)
        s3://{USER}:{PASSWORD}@domain.tld/path/to/folder?s3_bucket=app_storage&use_ssl=false

- Azure Blob Storage

        azure://{STORAGE_NAME}.blob.core.windows.net/path/to/folder?access_key=...
        azure://{STORAGE_NAME}.blob.core.windows.net/path/to/folder?tenant_id=...&client_id=...&client_secret=...

- Local Storage

        file:///path/to/folder

## Usage

To use the filestore in your code, you can simply configure it using the example URLs seen in the previous section then load the filestore using the loader:

    ```python
    from howler.common import loader

    with loader.get_filestore() as fs:
        binary_data = fs.get('myfile')
    ```

### Support filestore function

These are the supported functions of the filestore:

- `close()`: Terminate the connection to all configured storage
- `delete(path, location?)`: Delete the path from the selected location
- `download(path, dest, location?)`: Download the path to the destination path from the selected location
- `exists(path, location?)`: Check if the file exists at the specified location
- `get(path, location?)`: Returns the binary data of the path from the selected location
- `put(path, content, location?)`: Put the content at the path in the selected location
- `upload(src, dest, location?)`: Upload the content of the src path to the dest path at the given location
- `upload_batch(tuples, location?)`: Upload the content of multiple src path to multiple dest path at the given location
