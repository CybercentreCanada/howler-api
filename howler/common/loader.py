import logging
import os
import typing
from pathlib import Path
from string import Template
from typing import TYPE_CHECKING, Any, Optional, Union

import yaml

from howler.utils.dict_utils import recursive_update

if TYPE_CHECKING:
    from howler.common.classification import Classification
    from howler.odm.models.config import Config

APP_NAME = os.environ.get("APP_NAME", "howler")
APP_PREFIX = os.environ.get("APP_PREFIX", "hwl")
USER_TYPES = {"admin", "user", "automation_basic", "automation_advanced"}

config_cache = {}


def env_substitute(buffer):
    """Replace environment variables in the buffer with their value.

    Use the built in template expansion tool that expands environment variable style strings ${}
    We set the idpattern to none so that $abc doesn't get replaced but ${abc} does.

    Case insensitive.
    Variables that are found in the buffer, but are not defined as environment variables are ignored.
    """
    return Template(buffer).safe_substitute(os.environ, idpattern=None, bracedidpattern="(?a:[_a-z][_a-z0-9]*)")


_CLASSIFICATIONS: dict[Union[str, Path], "Classification"] = {}


def get_classification(yml_config: Optional[str] = None):  # noqa: C901
    "Get the classification from a given classification.yml file, caching results"
    if yml_config in _CLASSIFICATIONS:
        return _CLASSIFICATIONS[yml_config]

    log = logging.getLogger(f"{APP_NAME}.common.loader")

    if not yml_config:
        yml_config_path = Path("/etc") / APP_NAME.replace("-dev", "") / "conf" / "classification.yml"
        if yml_config_path.is_symlink():
            log.info("%s is a symbolic link!", yml_config_path)
            if str(yml_config_path.readlink()).startswith("..data"):
                yml_config_path = yml_config_path.parent / yml_config_path.readlink()
                log.info(
                    "This symbolic link links to a configmap, handling accordingly. Reading from %s",
                    yml_config_path,
                )
            else:
                yml_config_path = Path(os.path.realpath(yml_config_path.readlink()))
                log.info(
                    "Reading from %s",
                    yml_config_path,
                )

        if not yml_config_path.exists():
            log.warning(f"{yml_config_path} does not exist!")
            yml_config_path = Path("/etc") / APP_NAME.replace("-dev", "") / "classification.yml"
            log.warning(f"Checking at {yml_config_path} instead.")
    else:
        yml_config_path = Path(yml_config)

    log.debug("Loading classification definition from %s", yml_config_path)

    classification_definition = None
    # Load modifiers from the yaml config
    if yml_config_path.exists():
        with yml_config_path.open() as yml_fh:
            yml_data = yaml.safe_load(yml_fh.read())
            if yml_data:
                classification_definition = yml_data

    if classification_definition is None:
        log.warning(
            "Specified classification file does not exist or does not contain data!"
            " Defaulting to default classification file."
        )
        default_file = Path(__file__).parent / "classification.yml"
        if default_file.exists():
            with default_file.open() as default_fh:
                default_yml_data = yaml.safe_load(default_fh.read())
                if default_yml_data:
                    classification_definition = default_yml_data
        else:
            log.critical("%s was not accessible!", default_file)

    from howler.common.classification import Classification, InvalidDefinition

    if not classification_definition:
        raise InvalidDefinition("Could not find any classification definition to load.")

    _classification = Classification(classification_definition)

    if yml_config:
        _CLASSIFICATIONS[yml_config] = _classification

    return _classification


def get_lookups(lookup_folder: Optional[str] = None):
    """Get lookups from the specified lookup folder"""
    from howler.config import config

    if not lookup_folder:
        lookup_folder_path = Path("/etc/") / APP_NAME.replace("-dev", "") / "lookups"
    else:
        lookup_folder_path = Path(lookup_folder)

    lookups = {}

    if lookup_folder_path.exists():
        for file in lookup_folder_path.iterdir():
            with file.open("r") as f:
                data = yaml.safe_load(f)
                lookups[file.stem] = data
    local_path = Path(__file__).parent.parent.parent / "static/mitre"
    config_path = Path(config.ui.static_folder) if config.ui.static_folder else None
    if local_path.exists():
        mitre_path = local_path
    elif config_path and (config_path / "mitre").exists():
        mitre_path = config_path / "mitre"
    else:
        mitre_path = None

    if mitre_path:
        lookups["icons"] = sorted(set(f.stem for f in mitre_path.iterdir()))
    else:
        lookups["icons"] = []

    lookups["roles"] = sorted(USER_TYPES)

    return lookups


def _get_config(yml_config: Optional[str] = None) -> "Config":
    """Get the configuration file data from a given path"""
    from howler.odm.models.config import Config

    if not yml_config:
        yml_config_path = Path("/etc") / APP_NAME.replace("-dev", "") / "conf" / "config.yml"
        if not yml_config_path.exists():
            yml_config_path = Path("/etc") / APP_NAME.replace("-dev", "") / "config.yml"
    else:
        yml_config_path = Path(yml_config)

    # Initialize a default config
    config = Config().as_primitives()

    # Load modifiers from the yaml config
    if yml_config_path.exists():
        with yml_config_path.open() as yml_fh:
            yml_data = yaml.safe_load(env_substitute(yml_fh.read()))
            if yml_data:
                config = typing.cast(dict[str, Any], recursive_update(config, yml_data))

    # Override log level from environment variable
    config["logging"]["log_level"] = os.environ.get(f"{APP_PREFIX.upper()}_LOG_LEVEL", config["logging"]["log_level"])

    return Config(config)


def get_config(yml_config: Optional[str] = None) -> "Config":
    """Get config data from a given path, caching results"""
    if yml_config not in config_cache:
        config_cache[yml_config] = _get_config(yml_config=yml_config)

    return config_cache[yml_config]


# Lazy load the datastore
_datastore = None


def datastore(config=None, archive_access=True):
    """Get a datastore connection"""
    global _datastore

    from howler.datastore.howler_store import HowlerDatastore
    from howler.datastore.store import ESStore

    if not config:
        config = get_config()

    if _datastore is None:
        _datastore = HowlerDatastore(ESStore(config=config, archive_access=archive_access))

    return _datastore
