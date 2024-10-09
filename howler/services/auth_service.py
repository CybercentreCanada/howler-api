import base64
import hashlib
from datetime import datetime
from typing import Optional, Union

import elasticapm
from flask import request

import howler.services.jwt_service as jwt_service
import howler.services.user_service as user_service
from howler.common.exceptions import (
    AccessDeniedException,
    AuthenticationException,
    HowlerException,
    InvalidDataException,
)
from howler.common.loader import datastore
from howler.common.logging import get_logger
from howler.config import config, redis
from howler.odm.models.user import User
from howler.remote.datatypes.queues.named import NamedQueue
from howler.remote.datatypes.set import ExpiringSet
from howler.security.utils import generate_random_secret, verify_password

logger = get_logger(__file__)

nonpersistent_config: dict[str, Union[str, int]] = {
    "host": config.core.redis.nonpersistent.host,
    "port": config.core.redis.nonpersistent.port,
    "ttl": config.auth.internal.failure_ttl,
}


def _get_token_store(user: str) -> ExpiringSet:
    """Get an expiring redis set in which to add a token

    Args:
        user (str): The user the token corresponds to

    Returns:
        ExpiringSet: The set in which we'll store the token
    """
    return ExpiringSet(f"token_{user}", host=redis, ttl=60 * 60)  # 1 Hour expiry


def _get_priv_store(user: str, token: str) -> ExpiringSet:
    """Get an expiring redis set in which to add the privileges

    Args:
        user (str): The user the token corresponds to
        token (str): The token the privileges correspond to

    Returns:
        ExpiringSet: The set in which we'll store the privileges
    """
    return ExpiringSet(
        # For security reasons, we won't save the whole token in redis. Just in case :)
        f"token_priv_{user}_{token[:10]}",
        host=redis,
        # 1 Hour expiry
        ttl=60 * 60,
    )


def create_token(user: str, priv: list[str]) -> str:
    """Generate a new token associated with the given user with the given privileges

    Args:
        user (str): The user to create the token as
        priv (list[str]): The privileges to give the token

    Returns:
        str: The new token
    """
    token = hashlib.sha256(str(generate_random_secret()).encode("utf-8", errors="replace")).hexdigest()

    _get_token_store(user).add(token)
    priv_store = _get_priv_store(user, token)
    priv_store.pop_all()
    priv_store.add(",".join(priv))

    return token


def check_token(user: str, token: str) -> Optional[list[str]]:
    """Check if a token exists, and return its list of privileges

    Args:
        user (str): The user corresponding to the token to check
        token (str): The token

    Returns:
        Optional[list[str]]: The list of privileges associated with the token
    """
    if _get_token_store(user).exist(token):
        members = _get_priv_store(user, token).members()
        if len(members) > 0:
            priv_str = members[0]
            return priv_str.split(",")

    return None


def validate_token(username: str, token: str) -> Optional[list[str]]:
    """This function identifies the user via the internal token functionality

    Args:
        username (str): The username corresponding to the provided token
        token (str): The token generated by our API to check for

    Raises:
        AuthenticationException: Invalid token

    Returns:
        tuple[Optional[User], Optional[list[str]]]: The user odm object and privileges, if validated
    """
    if token:
        priv = check_token(username, token)
        if priv:
            return priv

        raise AuthenticationException("Invalid token")

    return None


@elasticapm.capture_span(span_type="authentication")
def bearer_auth(
    data: str, skip_jwt: bool = False, skip_internal: bool = False
) -> tuple[Optional[User], Optional[list[str]]]:
    """This function handles Bearer type Authorization headers.

    Args:
        data (str): The corresponding data in the Authorization header.

    Returns:
        tuple[Optional[User], Optional[list[str]]]: The user odm object and privileges, if validated
    """
    if "." in data:
        if not skip_jwt:
            try:
                jwt_data = jwt_service.decode(data, validate_audience=True)
            except HowlerException as e:
                raise AuthenticationException(
                    "Something went wrong when decoding your key. Please reauthenticate.",
                    cause=e,
                )

            cur_user = user_service.parse_user_data(jwt_data, jwt_service.get_provider(data))

            if cur_user:
                logger.debug("User successfully authenticated using JWT.")

                return cur_user, ["R", "W", "E"]

            return None, None
        else:
            raise InvalidDataException("Not a valid authentication type for this endpoint.")
    else:
        if not skip_internal:
            [username, token] = data.split(":", maxsplit=1)

            privs = validate_token(username, token)

            if privs is not None:
                return datastore().user.get(username), privs

            return None, None
        else:
            raise InvalidDataException("Not a valid authentication type for this endpoint.")


@elasticapm.capture_span(span_type="authentication")
def validate_apikey(
    username: str, apikey: str, impersonator: Optional[User] = None
) -> tuple[Optional[User], Optional[list[str]]]:
    """This function identifies the user via the internal API key functionality.

    Args:
        username (str): The username corresponding to the provided api key
        apikey (str): The apikey used to authenticate as the user
        impersonator (Optional[str]): The user who wants to impersonate as the provided username. Defaults to None.

    Raises:
        AccessDeniedException: Api Key authentication was disabled, or the api was not valid for impersonation,
                               or it was an impersonation api key incorrectly provided in the Authorization header.

    Returns:
        tuple[Optional[User], Optional[list[str]]]: The user odm object and privileges, if validated
    """
    if config.auth.allow_apikeys and apikey:
        user_data: User = datastore().user.get_if_exists(username)
        if user_data:
            try:
                # Get the name and secret data of the api key we are validating
                name, apikey_password = apikey.split(":", 1)
                key = user_data.apikeys.get(name, None)

                # Does the key actually exist?
                if not key:
                    raise AuthenticationException("API Key does not exist")

                if key.expiry_date is not None:
                    if key.expiry_date.replace(tzinfo=None) < datetime.utcnow():
                        raise AuthenticationException("Key is expired")

                # Handle impersonation. Basically, make sure that either:
                # a) someone is trying to impersonate as this user, and the apikey can be used for that, AND the
                #    impersonator is on the list of people allowed to use it
                # b) The user is not being impersonated, and the api key isn't specifically meant for impersonation
                if impersonator and ("I" not in key.acl or impersonator["uname"] not in key.agents):
                    raise AccessDeniedException("Not a valid impersonation api key")
                elif not impersonator and "I" in key.acl:
                    raise AccessDeniedException(
                        "Cannot use impersonation key in normal Authorization Header! "
                        + "Provide your credentials and supply it in the X-Impersonating header instead."
                    )

                # If the key can be used for whichever purpose, actually validate the secret data
                if verify_password(apikey_password, key.password):
                    return user_data, key.acl
            except ValueError:
                pass

        return None, None
    else:
        raise AccessDeniedException("API Key authentication disabled")


def validate_userpass(username: str, password: str) -> tuple[Optional[User], Optional[list[str]]]:
    """This function identifies the user via the user/pass functionality

    Args:
        username (str): The username corresponding to the provided password
        password (str): The password used to authenticate as the user

    Raises:
        AccessDeniedException: Username/Password authentication is currently disabled

    Returns:
        tuple[Optional[User], Optional[list[str]]]: The user odm object and privileges, if validated
    """
    if config.auth.internal.enabled and username and password:
        user = datastore().user.get(username)
        if user:
            if verify_password(password, user.password):
                return user, ["R", "W", "E"]

        return None, None
    else:
        raise AccessDeniedException("Username/Password authentication disabled")


def decode_b64(b64_str: str) -> str:
    """Decode a base64 string into plain text.

    Args:
        b64_str (str): The base64 string

    Raises:
        InvalidDataException: The data was not base64.

    Returns:
        str: A plain text representation of the data.
    """
    try:
        return base64.b64decode(b64_str).decode("utf-8")
    except UnicodeDecodeError as e:
        raise InvalidDataException("Basic authentication data must be base64 encoded") from e


@elasticapm.capture_span(span_type="authentication")
def basic_auth(
    data: str, is_base64: bool = True, skip_apikey: bool = False, skip_password: bool = False
) -> tuple[Optional[User], Optional[list[str]]]:
    """This function handles Basic type Authorization headers.

    Args:
        data (str): The corresponding data in the Authorization header.
        is_base64 (bool, optional): Whether the provided data is base64 encoded. Defaults to True.
        skip_apikey (bool, optional): Whether to skip apikey validation. Defaults to False.
        skip_password (bool, optional): Whether to skip password validation. Defaults to False.

    Raises:
        AuthenticationException: The login information is invalid, or the maximum password retry for the account
                                 has been reached.

    Returns:
        tuple[Optional[User], Optional[list[str]]]: The user odm object and privileges, if validated
    """
    key_pair = decode_b64(data) if is_base64 else data

    [username, data] = key_pair.split(":", maxsplit=1)

    validated_user = None
    if not skip_apikey:
        validated_user, priv = validate_apikey(username, data)

    # Bruteforce protection
    auth_fail_queue: NamedQueue = NamedQueue(f"ui-failed-{username}", **nonpersistent_config)  # type: ignore
    if auth_fail_queue.length() >= config.auth.internal.max_failures:
        # Failed 'max_failures' times, stop trying... This will timeout in 'failure_ttl' seconds
        raise AuthenticationException(
            "Maximum password retry of {retry} was reached. "
            "This account is locked for the next {ttl} "
            "seconds...".format(
                retry=config.auth.internal.max_failures,
                ttl=config.auth.internal.failure_ttl,
            )
        )

    if not validated_user and not skip_password:
        validated_user, priv = validate_userpass(username, data)

    if not validated_user:
        auth_fail_queue.push(
            {
                "remote_addr": request.remote_addr,
                "host": request.host,
                "full_path": request.full_path,
            }
        )
        raise AuthenticationException("Invalid login information")

    return validated_user, priv
