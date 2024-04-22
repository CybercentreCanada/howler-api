import sys

import requests

from howler.common.logging import get_logger
from howler.config import config

logger = get_logger(__file__)


def get_apps_list() -> list[dict[str, str]]:
    """Get a list of apps from the discovery service

    Returns:
        list[dict[str, str]]: A list of other apps
    """
    apps = []

    if "pytest" in sys.modules:
        logger.info("Skipping discovery, running in a test environment")

    if config.ui.discover_url:
        try:
            resp = requests.get(
                config.ui.discover_url,
                headers={"accept": "application/json"},
                timeout=5,
            )
            if resp.ok:
                data = resp.json()
                for app in data["applications"]["application"]:
                    try:
                        url = app["instance"][0]["hostName"]

                        if "howler" not in url:
                            apps.append(
                                {
                                    "alt": app["instance"][0]["metadata"]["alternateText"],
                                    "name": app["name"],
                                    "img_d": app["instance"][0]["metadata"]["imageDark"],
                                    "img_l": app["instance"][0]["metadata"]["imageLight"],
                                    "route": url,
                                    "classification": app["instance"][0]["metadata"]["classification"],
                                }
                            )
                    except Exception:
                        logger.exception(f"Failed to parse get app: {str(app)}")
            else:
                logger.warning(f"Invalid response from server for apps discovery: {config.ui.discover_url}")
        except Exception:
            logger.exception(f"Failed to get apps from discover URL: {config.ui.discover_url}")

    return sorted(apps, key=lambda k: k["name"])
