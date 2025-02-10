import time
from typing import Optional

import elasticapm
import requests
from flask import request

from howler.api import bad_gateway, make_subapi_blueprint, ok
from howler.common.exceptions import AuthenticationException
from howler.common.logging import get_logger
from howler.common.swagger import generate_swagger_docs
from howler.config import cache, config
from howler.security import api_login

SUB_API = "borealis"
borealis_api = make_subapi_blueprint(SUB_API, api_version=1)
borealis_api._doc = "Proxy enrichment requests to borealis"

logger = get_logger(__file__)


@cache.memoize(15 * 60)
def get_token(access_token: str) -> str:
    """Get a borealis token based on the current howler token"""
    if not config.core.borealis.scope:
        logger.warning("No borealis scope provided, not using OBO")
        return access_token

    obo_access_token = access_token

    return obo_access_token


@generate_swagger_docs()
@borealis_api.route("/<path:path>", methods=["GET", "POST"])
@api_login(required_priv=["R"], required_method=["oauth"])
def proxy_to_borealis(path, **kwargs):
    """Proxy enrichment requests to Borealis

    Variables:
    None

    Arguments:
    None

    Data Block:
    Any

    Result Example:
    Borealis Responses
    """
    logger.info(
        "Proxying borealis request to path %s/%s?%s", config.core.borealis.url, path, request.query_string.decode()
    )

    auth_data: Optional[str] = request.headers.get("Authorization", None, type=str)

    if not auth_data:
        raise AuthenticationException("No Authorization header present")

    auth_token = auth_data.split(" ")[1]

    borealis_token = get_token(auth_token)

    start = time.perf_counter()
    with elasticapm.capture_span("borealis", span_type="http"):
        if request.method.lower() == "get":
            response = requests.get(
                f"{config.core.borealis.url}/{path}",
                headers={"Authorization": f"Bearer {borealis_token}", "Accept": "application/json"},
                params=request.args.to_dict(),
                timeout=60,
            )
        else:
            response = requests.post(
                f"{config.core.borealis.url}/{path}",
                json=request.json,
                headers={"Authorization": f"Bearer {borealis_token}", "Accept": "application/json"},
                params=request.args.to_dict(),
                timeout=60,
            )

    logger.debug(f"Request to borealis completed in {round(time.perf_counter() - start)}ms")

    if not response.ok:
        return bad_gateway(response.json(), err="Something went wrong when connecting to borealis")

    return ok(response.json()["api_response"])
