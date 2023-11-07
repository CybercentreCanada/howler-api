from typing import Optional
from flask import request
from howler.common.exceptions import HowlerAttributeError, HowlerRuntimeError
from howler.common.loader import APP_NAME
from howler.common.logging import get_logger
from howler.remote.datatypes.set import ExpiringSet
from hogwarts.auth.vault.vault_client import VaultClient
from hogwarts.auth.vault.exceptions import VaultRequestException

from hogwarts.spellbook import SpellbookClient
from hogwarts.spellbook.exceptions import Unauthorized
from howler.config import config, redis, cache

logger = get_logger(__file__)


def _get_spellbook_token_store(user: str):
    """Get an expiring redis set in which to add a token

    Args:
        user (str): The user the token corresponds to

    Returns:
        ExpiringSet: The set in which we'll store the token
    """
    return ExpiringSet(f"spellbook_token_{user}", host=redis, ttl=60 * 60)


@cache.cached(timeout=60 * 60, key_prefix="_get_token_raw")
def _get_token_raw(user: str):
    spellbook_token_store = _get_spellbook_token_store(user)

    if spellbook_token_store.length() > 0:
        logger.debug("Using cached OBO token")
        return spellbook_token_store.rand_member()[0]

    return None


def get_spellbook_token(user: str, force_refresh=False):
    # Due to previous validation in api_login, we know this is type Bearer for oauth
    auth_data: str = request.headers.get("Authorization", None, type=str)
    auth_token = auth_data.split(" ")[1]

    try:
        obo_access_token = None
        if not force_refresh:
            obo_access_token = _get_token_raw(user)

        if obo_access_token is None:
            logger.info("Contacting vault for new OBO token")
            vault_client = VaultClient(url=config.core.vault_url)
            obo_access_token, _ = vault_client.on_behalf_of(
                config.core.spellbook.scope,
                auth_token,
                token_client_name=APP_NAME.replace("-dev", ""),
            )

            spellbook_token_store = _get_spellbook_token_store(user)
            spellbook_token_store.pop_all()
            spellbook_token_store.add(obo_access_token)

            return obo_access_token
    except VaultRequestException as e:
        logger.error(e)

        return None


def get_spellbook_client(
    user: Optional[str] = None, access_token: Optional[str] = None
):
    if access_token is None:
        if user is None:
            raise HowlerAttributeError("One of access_token/user must be provided.")

        try:
            access_token = get_spellbook_token(user)

            if access_token is None:
                access_token = get_spellbook_token(user, force_refresh=True)
        except Unauthorized:
            access_token = get_spellbook_token(user, force_refresh=True)

        if access_token is None:
            raise HowlerRuntimeError("There was an issue connecting to the vault.")

    logger.debug("Connecting to spellbook client at %s", config.core.spellbook.url)

    return SpellbookClient(
        token=access_token,
        spellbook_base_uri=config.core.spellbook.url,
    )
