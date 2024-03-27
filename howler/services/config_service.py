from datetime import datetime
from math import ceil
from typing import Optional

from flask import request
from howler.services import jwt_service
import howler.services.hit_service as hit_service
from howler.common.loader import get_lookups
from howler.config import CLASSIFICATION, config, get_branch, get_commit, get_version
from howler.helper.discover import get_apps_list
from howler.helper.search import list_all_fields
from howler.odm.models.howler_data import Assessment, Escalation, HitStatus, Scrutiny
from howler.odm.models.user import User
from howler.utils.str_utils import default_string_value

classification_definition = CLASSIFICATION.get_parsed_classification_definition()

lookups = get_lookups()
apps = get_apps_list()


def get_configuration(user: User):
    """Get system configration data for the Howler API

    Args:
        user (User): The user making the request
    """

    amount, unit = (
        config.auth.max_apikey_duration_amount,
        config.auth.max_apikey_duration_unit,
    )

    if config.auth.oauth.strict_apikeys:
        auth_header: Optional[str] = request.headers.get("Authorization", None)

        if auth_header and auth_header.startswith("Bearer") and "." in auth_header:
            oauth_token = auth_header.split(" ")[1]
            data = jwt_service.decode(
                oauth_token,
                validate_audience=False,
                options={"verify_signature": False},
            )
            amount, unit = (
                ceil(
                    (
                        datetime.fromtimestamp(data["exp"]) - datetime.now()
                    ).total_seconds()
                ),
                "seconds",
            )

    return {
        "lookups": {
            "howler.status": HitStatus.list(),
            "howler.scrutiny": Scrutiny.list(),
            "howler.escalation": Escalation.list(),
            "howler.assessment": Assessment.list(),
            "transitions": {
                status: hit_service.get_transitions(status)
                for status in HitStatus.list()
            },
            **lookups,
        },
        "configuration": {
            "auth": {
                "allow_apikeys": config.auth.allow_apikeys,
                "allow_extended_apikeys": config.auth.allow_extended_apikeys,
                "max_apikey_duration_amount": amount,
                "max_apikey_duration_unit": unit,
                "oauth_providers": [
                    name
                    for name, p in config.auth.oauth.providers.items()
                    if default_string_value(
                        p.client_secret, env_name=f"{name.upper()}_CLIENT_SECRET"
                    )
                ],
                "internal": {"enabled": config.auth.internal.enabled},
            },
            "system": {
                "type": config.system.type,
                "version": get_version(),
                "branch": get_branch(),
                "commit": get_commit(),
                "retention": {
                    "enabled": config.system.retention.enabled,
                    "limit_unit": config.system.retention.limit_unit,
                    "limit_amount": config.system.retention.limit_amount,
                },
            },
            "ui": {
                "apps": apps,
                "banner": config.ui.banner,
                "banner_level": config.ui.banner_level,
            },
            "features": {
            },
        },
        "c12nDef": classification_definition,
        "indexes": list_all_fields(
            "admin" in user["type"] if user is not None else False
        ),
    }
