from howler import odm

from howler.odm.models.ecs.code_signature import CodeSignature
from howler.odm.models.ecs.elf import ELF
from howler.odm.models.ecs.hash import Hashes
from howler.odm.models.ecs.pe import PE

# from howler.odm.models.ecs.x509 import X509

FILE_TYPE = ["file", "dir", "symlink"]


@odm.model(
    index=True,
    store=True,
    description="A file is defined as a set of information that has "
    "been created on, or has existed on a filesystem.",
)
class File(odm.Model):
    accessed = odm.Optional(odm.Date(description="Last time the file was accessed."))
    attributes = odm.Optional(
        odm.List(odm.Keyword(), description="Array of file attributes.")
    )
    created = odm.Optional(odm.Date(description="File creation time."))
    ctime = odm.Optional(
        odm.Date(description="Last time the file attributes or metadata changed.")
    )
    device = odm.Optional(
        odm.Keyword(description="Device that is the source of the file.")
    )
    directory = odm.Optional(
        odm.Keyword(
            description="Directory where the file is located. It should include the drive letter, when appropriate."
        )
    )
    drive_letter = odm.Optional(
        odm.Keyword(
            description="Drive letter where the file is located. This field is only relevant on Windows."
        )
    )
    extension = odm.Optional(
        odm.Keyword(description="File extension, excluding the leading dot.")
    )
    fork_name = odm.Optional(
        odm.Keyword(
            description="A fork is additional data associated with a filesystem object."
        )
    )
    gid = odm.Optional(odm.Keyword(description="Primary group ID (GID) of the file."))
    group = odm.Optional(odm.Keyword(description="Primary group name of the file."))
    inode = odm.Optional(
        odm.Keyword(description="Inode representing the file in the filesystem.")
    )
    mime_type = odm.Optional(
        odm.Keyword(
            description="MIME type should identify the format of the file or stream of "
            "bytes using IANA official types, where possible."
        )
    )
    mode = odm.Optional(
        odm.Keyword(description="Mode of the file in octal representation.")
    )
    mtime = odm.Optional(
        odm.Date(description="Last time the file content was modified.")
    )
    name = odm.Optional(
        odm.Keyword(
            description="Name of the file including the extension, without the directory."
        )
    )
    owner = odm.Optional(odm.Keyword(description="File owner’s username."))
    path = odm.Optional(
        odm.Keyword(
            description="Full path to the file, including the file name. "
            "It should include the drive letter, when appropriate."
        )
    )
    size = odm.Optional(odm.Integer(description="File size in bytes."))
    target_path = odm.Optional(odm.Keyword(description="Target path for symlinks."))
    type = odm.Optional(
        odm.Enum(values=FILE_TYPE, description="File type (file, dir, or symlink).")
    )
    uid = odm.Optional(
        odm.Keyword(
            description="The user ID (UID) or security identifier (SID) of the file owner."
        )
    )

    code_signature = odm.Optional(
        odm.Compound(
            CodeSignature,
            description="These fields contain information about binary code signatures.",
        )
    )
    elf = odm.Optional(
        odm.Compound(
            ELF,
            description="These fields contain Linux Executable Linkable Format (ELF) metadata.",
        )
    )
    hash = odm.Optional(
        odm.Compound(
            Hashes,
            description="These fields contain Windows Portable Executable (PE) metadata.",
        )
    )
    pe = odm.Optional(odm.Compound(PE, description="Hashes, usually file hashes."))
