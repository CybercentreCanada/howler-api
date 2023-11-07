import chevron
import requests
from flask import request
from hogwarts.auth.vault.vault_client import VaultClient

from howler.common.loader import APP_NAME
from howler.common.logging import get_logger
from howler.config import cache, config
from howler.odm.models.analytic import Analytic
from howler.odm.models.hit import Hit

logger = get_logger(__file__)


@cache.memoize(15 * 60)
def get_token(access_token: str):
    logger.info("This should be cached")
    obo_access_token = ""
    try:
        # use vault client to obo to nbgallery
        vault_client = VaultClient(url=config.core.vault_url)
        obo_access_token, _ = vault_client.on_behalf_of(
            config.core.notebook.scope,
            token=access_token,
            token_client_name=APP_NAME.replace("-dev", ""),
        )

    except Exception as error:
        raise Exception("Unexpected error while commucating with vault:", error)

    return obo_access_token


def get_nbgallery_nb(link: str):
    # /notebooks/1-example-nb
    # get the id (1)
    id = link.rsplit("/", 1)[-1].rsplit("-")[0]
    auth_data: str = request.headers.get("Authorization", None, type=str)
    auth_token = auth_data.split(" ")[1]

    # use obo token to retrieve notebook value
    notebook = requests.get(
        f"{config.core.notebook.url}/notebooks/{id}/download.json",
        headers={
            "accept": "application/json",
            "Authorization": f"Bearer {get_token(access_token=auth_token)}",
        },
        timeout=5,
    )

    if notebook.ok:
        notebook = notebook.json()

    name = notebook["metadata"]["gallery"]["title"]

    return (notebook, name)


def get_user_envs():
    auth_data: str = request.headers.get("Authorization", None, type=str)
    auth_token = auth_data.split(" ")[1]

    # get environment info from jupyterhub
    # how to get environment without nbgallery?
    # https://nbgallery.dev.analysis.cyber.gc.ca/environments.json
    env = requests.get(
        f"{config.core.notebook.url}/environments.json",
        headers={
            "accept": "application/json",
            "Authorization": f"Bearer {get_token(access_token=auth_token)}",
        },
        timeout=5,
    )

    if env.ok:
        env = env.json()
    else:
        raise Exception(f"NBGallery returned {env.status_code}")

    return env


def get_nb_information(nb_link: str, analytic: Analytic, hit: Hit = {}):
    # get notebook
    # only from nbgallery for now
    if "nbgallery" in nb_link:
        json_content, name = get_nbgallery_nb(nb_link)
    else:
        raise Exception("Invalid notebook source")

    try:
        # patch first node containing code with hit/analytic info
        cell_to_template = next(
            filter(lambda cell: cell["cell_type"] == "code", json_content["cells"])
        )
        # goal: support any field from a hit/analytic object
        cell_to_template["source"] = chevron.render(
            cell_to_template["source"], {"hit": hit, "analytic": analytic}
        )
    except StopIteration:
        raise Exception("Notebook doesn't contain a cell with code.")
    except Exception:
        raise Exception("Unexpected error while processing notebook.")

    return (json_content, name)
