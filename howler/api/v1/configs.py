import howler.services.config_service as config_service
from howler.api import make_subapi_blueprint, ok

SUB_API = "configs"
config_api = make_subapi_blueprint(SUB_API, api_version=1)
config_api._doc = "Read configuration data about the system"


@config_api.route("/", methods=["GET"])
def configs(**kwargs):
    """
    Return all of the configuration information about the deployment.

    Variables:
    None

    Arguments:
    None

    Result Example:
    {
        "lookups": {
            "status": [],
            "scrutiny": [],
            "escalation": [],
            "assessment": []
        },
        "configuration": {                          # Configuration block
            "auth": {                               # Authentication Configuration
                "allow_apikeys": True,              # Are APIKeys allowed for the user
                "allow_extended_apikeys": True,     # Allow user to generate extended access API Keys
            },
            "system": {                             # System Configuration
                "type": "production",               # Type of deployment
                "version": "4.1"                    # Howler version
            },
            "ui": {                                 # UI Configuration
                "apps": [],                         # List of apps shown in the apps switcher
                "banner": None,                     # Banner displayed on the submit page
                "banner_level": True,               # Banner color (info, success, warning, error)
            }
        },
        "c12nDef": {},                              # Classification definition block
        "indexes": {},                              # Search indexes definitions
    }

    """

    return ok(config_service.get_configuration(user=kwargs.get("user", None)))
