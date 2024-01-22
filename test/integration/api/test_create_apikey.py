import base64
import re
from datetime import datetime, timedelta
from urllib.parse import urlsplit
import jwt

import pytest
import requests
from conftest import APIError, get_api_data
from flask import json
from howler.config import config
from howler.datastore.howler_store import HowlerDatastore
from utils.oauth_credentials import get_token

ALPHABET = [chr(x + 65) for x in range(26)] + [str(x) for x in range(10)]


@pytest.fixture(scope="module")
def datastore(datastore_connection: HowlerDatastore):
    return datastore_connection


def test_add_delete_apikey(datastore: HowlerDatastore, login_session):
    session, host = login_session

    result: str = get_api_data(
        session,
        f"{host}/api/v1/auth/apikey",
        data=json.dumps(
            {
                "name": "tester",
                "priv": ["R"],
                "expiry_date": (datetime.now() + timedelta(days=1)).isoformat(),
            }
        ),
        method="POST",
    )["apikey"]

    req_result = requests.get(
        f"{host}/api/v1/user/whoami",
        headers={
            "Authorization": f"Basic {base64.b64encode(f'admin:{result}'.encode()).decode('utf-8')}"
        },
    )

    assert req_result.ok

    get_api_data(
        session,
        f"{host}/api/v1/auth/apikey/tester",
        method="DELETE",
    )

    req_result = requests.get(
        f"{host}/api/v1/user/whoami",
        headers={
            "Authorization": f"Basic {base64.b64encode(f'admin:{result}'.encode()).decode('utf-8')}"
        },
    )

    assert not req_result.ok


@pytest.mark.skipif(
    not config.auth.max_apikey_duration_amount
    or not config.auth.max_apikey_duration_unit,
    reason="Can only be run when max expiry is set!",
)
def test_past_max_expiry(datastore: HowlerDatastore, login_session):
    session, host = login_session

    key_expiry = (
        datetime.now()
        + timedelta(
            **{
                config.auth.max_apikey_duration_unit: config.auth.max_apikey_duration_amount
                + 10
            }
        )
    ).isoformat()

    with pytest.raises(APIError) as err:
        get_api_data(
            session,
            f"{host}/api/v1/auth/apikey",
            data=json.dumps(
                {
                    "name": "tester",
                    "priv": ["R"],
                    "expiry_date": key_expiry,
                }
            ),
            method="POST",
        )

    assert str(err.value).startswith("400: Expiry date must be before")


def test_invalid_apikey_expiry(datastore: HowlerDatastore, login_session):
    session, host = login_session

    with pytest.raises(APIError) as err:
        get_api_data(
            session,
            f"{host}/api/v1/auth/apikey",
            data=json.dumps(
                {
                    "name": "badexpiry",
                    "priv": ["R"],
                    "expiry_date": "2023, Feb 14th 10:00am",
                }
            ),
            method="POST",
        )

    assert str(err.value).startswith("400: Invalid expiry date format")
