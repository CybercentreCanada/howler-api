from howler import odm
from howler.odm.models.ecs.user import ShortUser


@odm.model(index=True, store=True, description="Information about the char device.")
class CharDevice(odm.Model):
    major = odm.Optional(odm.Integer(description="The major number identifies the driver associated with the device."))
    minor = odm.Optional(
        odm.Integer(
            description="The minor number is used only by the driver specified by the major number; other parts of "
            "the kernel don’t use it, and merely pass it along to the driver."
        )
    )


@odm.model(index=True, store=True, description="Information about the controlling TTY device.")
class TTY(odm.Model):
    char_device = odm.Optional(odm.Compound(CharDevice, description="Information about the char device."))


@odm.model(index=True, store=True, description="Thread Information.")
class Thread(odm.Model):
    id = odm.Optional(odm.Integer(description="Thread ID."))
    name = odm.Optional(odm.Keyword(description="Thread name."))


@odm.model(
    index=True,
    store=True,
    description="These fields contain information about a previous process.",
)
class PreviousProcess(odm.Model):
    args = odm.Optional(
        odm.List(
            odm.Keyword(),
            description="Array of process arguments, starting with the absolute path to the executable.",
        )
    )
    args_count = odm.Optional(odm.Integer(description="Length of the process.args array."))
    executable = odm.Optional(odm.Keyword(description="Absolute path to the process executable."))


@odm.model(
    index=True,
    store=True,
    description="These fields contain information about the parent process.",
)
class ParentProcess(odm.Model):
    args = odm.Optional(
        odm.List(
            odm.Keyword(),
            description="Array of process arguments, starting with the absolute path to the executable.",
        )
    )
    args_count = odm.Optional(odm.Integer(description="Length of the process.args array."))
    command_line = odm.Optional(
        odm.Keyword(
            description="Full command line that started the process, including the absolute path to the "
            "executable, and all arguments."
        )
    )
    end = odm.Date(odm.Keyword(description="The time the process ended."))
    entity_id = odm.Optional(odm.Keyword(description="Unique identifier for the process."))
    env_vars = odm.Optional(
        odm.Mapping(
            odm.Keyword(),
            description="Environment variables (env_vars) set at the time of the event. May be filtered to "
            "protect sensitive information.",
        )
    )
    executable = odm.Optional(odm.Keyword(description="Absolute path to the process executable."))
    exit_code = odm.Optional(odm.Integer(description="The exit code of the process, if this is a termination event."))
    interactive = odm.Optional(odm.Boolean(description="Whether the process is connected to an interactive shell."))
    name = odm.Optional(odm.Keyword(description="Process name."))
    pid = odm.Optional(odm.Integer(description="Process id."))
    same_as_process = odm.Optional(
        odm.Boolean(
            description="This boolean is used to identify if a leader process is the same as the top level process."
        )
    )
    start = odm.Optional(odm.Date(description="The time the process started."))
    user = odm.Optional(odm.Compound(ShortUser, description="The effective user (euid)."))


@odm.model(
    index=True,
    store=True,
    description="These fields contain information about a process.",
)
class Process(odm.Model):
    args = odm.Optional(
        odm.List(
            odm.Keyword(),
            description="Array of process arguments, starting with the absolute path to the executable.",
        )
    )
    args_count = odm.Optional(odm.Integer(description="Length of the process.args array."))
    command_line = odm.Optional(
        odm.Keyword(
            description="Full command line that started the process, including the absolute path to the "
            "executable, and all arguments."
        )
    )
    end = odm.Optional(odm.Date(odm.Keyword(description="The time the process ended.")))
    entity_id = odm.Optional(odm.Keyword(description="Unique identifier for the process."))
    env_vars = odm.Optional(
        odm.Mapping(
            odm.Keyword(),
            description="Environment variables (env_vars) set at the time of the event. May be filtered to "
            "protect sensitive information.",
        )
    )
    executable = odm.Optional(odm.Keyword(description="Absolute path to the process executable."))
    exit_code = odm.Optional(odm.Integer(description="The exit code of the process, if this is a termination event."))
    interactive = odm.Optional(odm.Boolean(description="Whether the process is connected to an interactive shell."))
    name = odm.Optional(odm.Keyword(description="Process name."))
    parent = odm.Optional(
        odm.List(
            odm.Compound(ParentProcess),
            description="Information about the parent process.",
        )
    )
    pid = odm.Optional(odm.Integer(description="Process id."))
    same_as_process = odm.Optional(
        odm.Boolean(
            description="This boolean is used to identify if a leader process is the same as the top level process."
        )
    )
    start = odm.Optional(odm.Date(description="The time the process started."))
    title = odm.Optional(odm.Keyword(description="Process title."))
    uptime = odm.Optional(odm.Integer(description="Seconds the process has been up."))
    user = odm.Optional(odm.Compound(ShortUser, description="The effective user (euid)."))
    working_directory = odm.Optional(odm.Keyword(description="The working directory of the process."))
