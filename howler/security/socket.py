import functools
import json
import uuid
from typing import Optional

from flask import request
from jwt import InvalidTokenError

import howler.services.auth_service as auth_service
from howler.api import forbidden, ok, unauthorized
from howler.common.exceptions import AuthenticationException
from howler.common.logging import get_logger
from howler.helper.ws import ConnectionClosed, Server

logger = get_logger(__file__)


def ws_response(type, data={}, error=False, status=200, message=""):
    return json.dumps(
        {"error": error, "status": status, "message": message, "type": type, **data}
    )


def websocket_auth(
    required_type: Optional[list[str]] = None, required_priv: Optional[list[str]] = None
):
    """Authentication for a new websocket connection.

    Args:
        required_type (Optional[list[str]], optional): The type required to access this websocket endpoint.
            Defaults to None.
        required_priv (Optional[list[str]], optional): The privileges required to access this websocket endpoint.
            Defaults to None.
    """
    if required_type is None:
        required_type = ["user"]

    if required_priv is None:
        required_priv = ["R", "W"]

    def wrapper(f):
        @functools.wraps(f)
        def auth(*args, **kwargs):
            try:
                ws = Server(request.environ, ping_interval=5)
                ws_id = str(uuid.uuid4())

                auth_header = ws.receive()

                user, privs = auth_service.bearer_auth(auth_header)

                if not user:
                    raise AuthenticationException()

                if not set(required_priv) & set(privs):
                    logger.warn(f"{ws_id}: Authentication header is invalid")
                    ws.close(
                        1008,
                        ws_response(
                            "error",
                            error=True,
                            status=403,
                            message="The method you've used to login does not give you access to this API.",
                        ),
                    )
                    return forbidden()

                logger.info(f"{ws_id} authenticated as {user['uname']}")
                ws.send(
                    ws_response(
                        "info",
                        {
                            "message": f"Listener authenticated as {user['uname']}",
                            "id": ws_id,
                            "username": user["uname"],
                        },
                    )
                )

                f(ws, *args, ws_id=ws_id, username=user["uname"], privs=privs, **kwargs)
            except ConnectionClosed:
                logger.info(f"{ws_id}: Client closed connection")
            except (
                AuthenticationException,
                ValueError,
                InvalidTokenError,
            ):
                logger.warn(f"{ws_id}: Authentication header is invalid")
                ws.close(
                    1008,
                    ws_response(
                        "error",
                        error=True,
                        status=401,
                        message="Authentication header is invalid.",
                    ),
                )
                return unauthorized()
            finally:
                try:
                    ws.close()
                except:  # noqa: E722
                    pass
                finally:
                    ws.connected = False

                return ok()

        return auth

    return wrapper
