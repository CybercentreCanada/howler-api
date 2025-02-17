# mypy: ignore-errors
import logging
import os
from typing import Optional

from howler import odm
from howler.common.loader import APP_NAME

OAUTH_AUTO_PROPERTY_TYPE = ["access", "classification", "role"]


@odm.model(index=False, store=False, description="Redis Service configuration")
class RedisServer(odm.Model):
    host: str = odm.Keyword(description="Hostname of Redis instance")
    port: int = odm.Integer(description="Port of Redis instance")


DEFAULT_REDIS_NP = {"host": "127.0.0.1", "port": 6379}

DEFAULT_REDIS_P = {"host": "127.0.0.1", "port": 6380}


@odm.model(index=False, store=False, description="Redis Configuration")
class Redis(odm.Model):
    nonpersistent: RedisServer = odm.Compound(
        RedisServer, default=DEFAULT_REDIS_NP, description="A volatile Redis instance"
    )
    persistent: RedisServer = odm.Compound(
        RedisServer, default=DEFAULT_REDIS_P, description="A persistent Redis instance"
    )


DEFAULT_REDIS = {"nonpersistent": DEFAULT_REDIS_NP, "persistent": DEFAULT_REDIS_P}


@odm.model(index=False, store=False, description="Parameters associated to ILM Policies")
class ILMParams(odm.Model):
    warm = odm.Integer(description="How long, per unit of time, should a document remain in the 'warm' tier?")
    cold = odm.Integer(description="How long, per unit of time, should a document remain in the 'cold' tier?")
    delete = odm.Integer(description="How long, per unit of time, should a document remain before being deleted?")
    unit = odm.Enum(
        ["d", "h", "m"],
        description="Unit of time used by `warm`, `cold`, `delete` phases",
    )


DEFAULT_ILM_PARAMS = {"warm": 5, "cold": 15, "delete": 30, "unit": "d"}


@odm.model(index=False, store=False, description="Index Lifecycle Management")
class ILM(odm.Model):
    enabled = odm.Boolean(description="Are we enabling ILM across indices?")
    days_until_archive = odm.Integer(description="Days until documents get archived")
    indexes: dict[str, ILMParams] = odm.Mapping(
        odm.Compound(ILMParams),
        default=DEFAULT_ILM_PARAMS,
        description="Index-specific ILM policies",
    )
    update_archive = odm.Boolean(description="Do we want to update documents in the archive?")


DEFAULT_ILM = {
    "days_until_archive": 15,
    "enabled": False,
    "indexes": {},
    "update_archive": False,
}


@odm.model(index=False, store=False, description="Host Entries")
class Host(odm.Model):
    name: str = odm.Keyword(description="Name of the host")
    username: Optional[str] = odm.Keyword(description="Username to login with", optional=True)
    password: Optional[str] = odm.Keyword(description="Password to login with", optional=True)
    apikey_id: Optional[str] = odm.Keyword(description="ID of the API Key to use when connecting", optional=True)
    apikey_secret: Optional[str] = odm.Keyword(
        description="Secret data of the API Key to use when connecting", optional=True
    )
    scheme: Optional[str] = odm.Keyword(description="Scheme to use when connecting", optional=True, default="http")
    host: str = odm.Keyword(description="URL to connect to")

    def __repr__(self):
        result = ""

        if self.scheme:
            result += f"{self.scheme}://"

        username = os.getenv(f"{self.name.upper()}_HOST_USERNAME", self.username)
        password = os.getenv(f"{self.name.upper()}_HOST_PASSWORD", self.password)

        if username and password:
            result += f"{username}:{password}@"

        result += self.host

        return result


@odm.model(index=False, store=False, description="Datastore Configuration")
class Datastore(odm.Model):
    hosts: list[Host] = odm.List(odm.Compound(Host), description="List of hosts used for the datastore")
    ilm = odm.Compound(ILM, default=DEFAULT_ILM, description="Index Lifecycle Management Policy")
    type = odm.Enum({"elasticsearch"}, description="Type of application used for the datastore")


DEFAULT_DATASTORE = {
    "hosts": [
        {
            "name": "elastic",
            "username": "elastic",
            "password": "devpass",
            "scheme": "http",
            "host": "localhost:9200",
        }
    ],
    "ilm": DEFAULT_ILM,
    "type": "elasticsearch",
}


@odm.model(
    index=False,
    store=False,
    description="Model Definition for the Logging Configuration",
)
class Logging(odm.Model):
    log_level: str = odm.Enum(
        values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "DISABLED"],
        description="What level of logging should we have?",
    )
    log_to_console: bool = odm.Boolean(description="Should we log to console?")
    log_to_file: bool = odm.Boolean(description="Should we log to files on the server?")
    log_directory: str = odm.Keyword(description="If `log_to_file: true`, what is the directory to store logs?")
    log_to_syslog: bool = odm.Boolean(description="Should logs be sent to a syslog server?")
    syslog_host: str = odm.Keyword(description="If `log_to_syslog: true`, provide hostname/IP of the syslog server?")
    syslog_port: int = odm.Integer(description="If `log_to_syslog: true`, provide port of the syslog server?")
    export_interval: int = odm.Integer(description="How often, in seconds, should counters log their values?")
    log_as_json: bool = odm.Boolean(description="Log in JSON format?")


DEFAULT_LOGGING = {
    "log_directory": f"/var/log/{APP_NAME.replace('-dev', '')}/",
    "log_as_json": True,
    "log_level": "INFO",
    "log_to_console": True,
    "log_to_file": False,
    "log_to_syslog": False,
    "syslog_host": "localhost",
    "syslog_port": 514,
    "export_interval": 5,
}


@odm.model(index=False, store=False, description="Password Requirement")
class PasswordRequirement(odm.Model):
    lower: bool = odm.Boolean(description="Password must contain lowercase letters")
    number: bool = odm.Boolean(description="Password must contain numbers")
    special: bool = odm.Boolean(description="Password must contain special characters")
    upper: bool = odm.Boolean(description="Password must contain uppercase letters")
    min_length: int = odm.Integer(description="Minimum password length")


DEFAULT_PASSWORD_REQUIREMENTS = {
    "lower": False,
    "number": False,
    "special": False,
    "upper": False,
    "min_length": 12,
}


@odm.model(index=False, store=False, description="Internal Authentication Configuration")
class Internal(odm.Model):
    enabled: bool = odm.Boolean(description="Internal authentication allowed?")
    failure_ttl: int = odm.Integer(description="How long to wait after `max_failures` before re-attempting login?")
    max_failures: int = odm.Integer(description="Maximum number of fails allowed before timeout")
    password_requirements: PasswordRequirement = odm.Compound(
        PasswordRequirement,
        default=DEFAULT_PASSWORD_REQUIREMENTS,
        description="Password requirements",
    )


DEFAULT_INTERNAL = {
    "enabled": True,
    "failure_ttl": 60,
    "max_failures": 5,
    "password_requirements": DEFAULT_PASSWORD_REQUIREMENTS,
}


@odm.model(index=False, store=False)
class OAuthAutoProperty(odm.Model):
    field: str = odm.Keyword(description="Field to apply `pattern` to")
    pattern: str = odm.Keyword(description="Regex pattern for auto-prop assignment")
    type: str = odm.Enum(
        OAUTH_AUTO_PROPERTY_TYPE,
        description="Type of property assignment on pattern match",
    )
    value: str = odm.Keyword(description="Assigned property value")


@odm.model(index=False, store=False, description="OAuth Provider Configuration")
class OAuthProvider(odm.Model):
    auto_create: bool = odm.Boolean(default=True, description="Auto-create users if they are missing")
    auto_sync: bool = odm.Boolean(default=False, description="Should we automatically sync with OAuth provider?")
    auto_properties: list[OAuthAutoProperty] = odm.List(
        odm.Compound(OAuthAutoProperty),
        default=[],
        description="Automatic role and classification assignments",
    )
    uid_randomize: bool = odm.Boolean(
        default=False,
        description="Should we generate a random username for the authenticated user?",
    )
    uid_randomize_digits: int = odm.Integer(
        default=0,
        description="How many digits should we add at the end of the username?",
    )
    uid_randomize_delimiter: str = odm.Keyword(
        default="-",
        description="What is the delimiter used by the random name generator?",
    )
    uid_regex: Optional[str] = odm.Optional(
        odm.Keyword(),
        description="Regex used to parse an email address and capture parts to create a user ID out of it",
    )
    uid_format: Optional[str] = odm.Optional(
        odm.Keyword(),
        description="Format of the user ID based on the captured parts from the regex",
    )
    client_id: Optional[str] = odm.Optional(
        odm.Keyword(),
        description="ID of your application to authenticate to the OAuth provider",
    )
    client_secret: Optional[str] = odm.Optional(
        odm.Keyword(),
        description="Password to your application to authenticate to the OAuth provider",
    )
    request_token_url: Optional[str] = odm.Optional(odm.Keyword(), description="URL to request token")
    request_token_params: Optional[str] = odm.Optional(odm.Keyword(), description="Parameters to request token")
    required_groups: list[str] = odm.List(
        odm.Keyword(),
        default=[],
        description="The groups the JWT must contain in order to allow access",
    )
    role_map: dict[str, str] = odm.Mapping(
        odm.Keyword(),
        default={},
        description="A mapping of OAuth groups to howler roles",
    )
    access_token_url: Optional[str] = odm.Optional(odm.Keyword(), description="URL to get access token")
    access_token_params: Optional[str] = odm.Optional(odm.Keyword(), description="Parameters to get access token")
    authorize_url: Optional[str] = odm.Optional(odm.Keyword(), description="URL used to authorize access to a resource")
    authorize_params: Optional[str] = odm.Optional(
        odm.Keyword(), description="Parameters used to authorize access to a resource"
    )
    api_base_url: Optional[str] = odm.Optional(
        odm.Keyword(), description="Base URL for downloading the user's and groups info"
    )
    audience: Optional[str] = odm.Optional(
        odm.Keyword(),
        description="The audience to validate against. Only must be set if audience is different than the client id.",
    )
    scope: str = odm.Keyword(description="The scope to validate against")
    picture_url: Optional[str] = odm.Optional(odm.Keyword(), description="URL for downloading the user's profile")
    groups_url: Optional[str] = odm.Optional(
        odm.Keyword(),
        description="URL for accessing additional data about the user's groups",
    )
    groups_key: Optional[str] = odm.Optional(
        odm.Keyword(),
        description="Path to the list of groups in the response returned from groups_url",
    )
    iss: Optional[str] = odm.Optional(odm.Keyword(), description="Optional issuer field for JWT validation")
    jwks_uri: str = odm.Keyword(description="URL used to verify if a returned JWKS token is valid")
    user_get: Optional[str] = odm.Optional(odm.Keyword(), description="Path from the base_url to fetch the user info")


DEFAULT_OAUTH_PROVIDERS = {}


@odm.model(index=False, store=False, description="OAuth Configuration")
class OAuth(odm.Model):
    enabled: bool = odm.Boolean(description="Enable use of OAuth?")
    gravatar_enabled: bool = odm.Boolean(description="Enable gravatar?")
    providers: dict[str, OAuthProvider] = odm.Mapping(
        odm.Compound(OAuthProvider),
        default=DEFAULT_OAUTH_PROVIDERS,
        description="OAuth provider configuration",
    )
    strict_apikeys: bool = odm.Boolean(
        description="Only allow apikeys that last as long as the access token used to log in",
        default=False,
    )


DEFAULT_OAUTH = {
    "enabled": False,
    "strict_apikeys": False,
    "gravatar_enabled": True,
    "providers": DEFAULT_OAUTH_PROVIDERS,
}


@odm.model(index=False, store=False, description="Authentication Methods")
class Auth(odm.Model):
    allow_apikeys: bool = odm.Boolean(description="Allow API keys?")
    allow_extended_apikeys: bool = odm.Boolean(description="Allow extended API keys?")
    max_apikey_duration_amount: Optional[int] = odm.Integer(
        description="Amount of unit of maximum duration for API keys", optional=True
    )
    max_apikey_duration_unit: Optional[str] = odm.Enum(
        values=["seconds", "minutes", "hours", "days", "weeks"],
        description="Unit of maximum duration for API keys",
        optional=True,
    )
    internal: Internal = odm.Compound(
        Internal,
        default=DEFAULT_INTERNAL,
        description="Internal authentication settings",
    )
    oauth: OAuth = odm.Compound(OAuth, default=DEFAULT_OAUTH, description="OAuth settings")


DEFAULT_AUTH = {
    "allow_apikeys": True,
    "allow_extended_apikeys": True,
    "internal": DEFAULT_INTERNAL,
    "oauth": DEFAULT_OAUTH,
}


@odm.model(index=False, store=False)
class APMServer(odm.Model):
    server_url: Optional[str] = odm.Optional(odm.Keyword(), description="URL to API server")
    token: Optional[str] = odm.Optional(odm.Keyword(), description="Authentication token for server")


DEFAULT_APM_SERVER = {"server_url": None, "token": None}


@odm.model(index=False, store=False, description="Metrics Configuration")
class Metrics(odm.Model):
    apm_server: APMServer = odm.Compound(APMServer, default=DEFAULT_APM_SERVER, description="APM server configuration")


DEFAULT_METRICS = {
    "apm_server": DEFAULT_APM_SERVER,
}


@odm.model(index=False, store=False, description="Retention Configuration")
class Retention(odm.Model):
    enabled: bool = odm.Boolean(
        default=True,
        description=(
            "Whether to enable the hit retention limit. If enabled, hits will "
            "be purged after the specified duration."
        ),
    )
    limit_unit: str = odm.Enum(
        values=[
            "days",
            "seconds",
            "microseconds",
            "milliseconds",
            "minutes",
            "hours",
            "weeks",
        ],
        description="The unit to use when computing the retention limit",
        default="days",
    )
    limit_amount: int = odm.Integer(
        default=350,
        description="The number of limit_units to use when computing the retention limit",
    )
    crontab: str = odm.Keyword(
        default="0 0 * * *",
        description="The crontab that denotes how often to run the retention job",
    )


DEFAULT_RETENTION = {
    "enabled": True,
    "limit_unit": "days",
    "limit_amount": 350,
    "crontab": "0 0 * * *",
}


@odm.model(index=False, store=False, description="System Configuration")
class System(odm.Model):
    type: str = odm.Enum(values=["production", "staging", "development"], description="Type of system")
    retention: Retention = odm.Compound(Retention, default=DEFAULT_RETENTION, description="Retention Configuration")


DEFAULT_SYSTEM = {"type": "development"}


@odm.model(index=False, store=False, description="UI Configuration")
class UI(odm.Model):
    audit: bool = odm.Boolean(description="Should API calls be audited and saved to a separate log file?")
    banner: dict[str, str] = odm.Optional(
        odm.Mapping(odm.Keyword()),
        description="Banner message display on the main page (format: {<language_code>: message})",
    )
    banner_level: str = odm.Enum(
        values=["info", "warning", "success", "error"],
        description="Banner message level",
    )
    debug: bool = odm.Boolean(description="Enable debugging?")
    static_folder: Optional[str] = odm.Keyword(
        optional=True, description="The directory where static assets are stored."
    )
    discover_url: Optional[str] = odm.Optional(odm.Keyword(), description="Discover URL")
    email: Optional[str] = odm.Optional(odm.Email(), description="Assemblyline admins email address")
    enforce_quota: bool = odm.Boolean(description="Enforce the user's quotas?")
    secret_key: str = odm.Keyword(description="Flask secret key to store cookies, etc.")
    validate_session_ip: bool = odm.Boolean(
        description="Validate if the session IP matches the IP the session was created from"
    )
    validate_session_useragent: bool = odm.Boolean(
        description="Validate if the session useragent matches the useragent the session was created with"
    )
    websocket_url: str = odm.Keyword(
        optional=True,
        description="The url to hit when emitting websocket events on the cluster",
    )


DEFAULT_UI = {
    "audit": True,
    "banner": None,
    "banner_level": "info",
    "debug": False,
    "discover_url": None,
    "email": None,
    "enforce_quota": True,
    "secret_key": os.environ.get("FLASK_SECRET_KEY", "This is the default flask secret key... you should change this!"),
    "validate_session_ip": True,
    "validate_session_useragent": True,
    "static_folder": os.path.dirname(__file__) + "/../../../static",
}


@odm.model(index=False, store=False, description="Howler Core Component Configuration")
class Core(odm.Model):
    metrics: Metrics = odm.Compound(
        Metrics,
        default=DEFAULT_METRICS,
        description="Configuration for Metrics Collection",
    )

    redis: Redis = odm.Compound(Redis, default=DEFAULT_REDIS, description="Configuration for Redis instances")


DEFAULT_CORE = {"metrics": DEFAULT_METRICS, "redis": DEFAULT_REDIS}


@odm.model(index=False, store=False, description="Howler Deployment Configuration")
class Config(odm.Model):
    auth: Auth = odm.Compound(Auth, default=DEFAULT_AUTH, description="Authentication module configuration")
    core: Core = odm.Compound(Core, default=DEFAULT_CORE, description="Core component configuration")
    datastore: Datastore = odm.Compound(Datastore, default=DEFAULT_DATASTORE, description="Datastore configuration")
    logging: Logging = odm.Compound(Logging, default=DEFAULT_LOGGING, description="Logging configuration")
    system: System = odm.Compound(System, default=DEFAULT_SYSTEM, description="System configuration")
    ui: UI = odm.Compound(UI, default=DEFAULT_UI, description="UI configuration parameters")


DEFAULT_CONFIG = {
    "auth": DEFAULT_AUTH,
    "core": DEFAULT_CORE,
    "datastore": DEFAULT_DATASTORE,
    "logging": DEFAULT_LOGGING,
    "system": DEFAULT_SYSTEM,
    "ui": DEFAULT_UI,
}


if __name__ == "__main__":
    # When executed, the config model will print the default values of the configuration
    import yaml

    logging.info(yaml.safe_dump(Config(DEFAULT_CONFIG).as_primitives()))
