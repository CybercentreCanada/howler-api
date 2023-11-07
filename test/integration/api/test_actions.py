import json
import re
import time
import warnings
from typing import Any
from uuid import uuid4

import pytest
from conftest import APIError, get_api_data

from howler.datastore.howler_store import HowlerDatastore
from howler.odm.random_data import create_actions, create_hits, wipe_actions, wipe_hits


@pytest.fixture(scope="module")
def datastore(datastore_connection):
    ds = datastore_connection

    try:
        wipe_hits(ds)
        wipe_actions(ds)
        create_hits(ds, hit_count=10)
        create_actions(ds)

        yield ds
    finally:
        wipe_hits(ds)
        wipe_actions(ds)


# noinspection PyUnusedLocal
def test_get_operations(datastore: HowlerDatastore, login_session):
    session, host = login_session

    resp = get_api_data(
        session,
        f"{host}/api/v1/action/operations",
    )

    for operation in resp:
        assert operation["id"]
        assert operation["title"]

        if not operation.get("i18nKey", None):
            warnings.warn(
                f"{operation['id']} is missing an i18nKey! Suggested: 'action.{operation['id']}'"
            )

        assert "description" in operation

        if not operation["description"].get("short", None):
            warnings.warn(f"{operation['id']} is missing a short description!")

        if not operation["description"].get("long", None):
            warnings.warn(f"{operation['id']} is missing a long description!")

        assert "steps" in operation

        for step in operation["steps"]:
            assert "args" in step
            assert len(list(step["args"].keys())) > 0

            for conditions in step["args"].values():
                assert isinstance(conditions, list)

                if len(conditions) > 0:
                    assert all(isinstance(c, str) for c in conditions)

            assert "options" in step

            for options in step["options"].values():
                assert isinstance(options, dict) or isinstance(options, list)


def test_execute_action_labels(datastore: HowlerDatastore, login_session):
    session, host = login_session

    req = {
        "request_id": str(uuid4()),
        "query": "howler.id:*",
        "operations": [
            {
                "operation_id": "add_label",
                "data_json": json.dumps({"category": "generic", "label": "potato"}),
            },
            {
                "operation_id": "remove_label",
                "data": {"category": "generic", "label": "potato"},
            },
        ],
    }

    resp = get_api_data(
        session,
        f"{host}/api/v1/action/execute",
        method="POST",
        data=json.dumps(req),
    )

    for report in resp.values():
        report = report[0]

        assert "query" in report
        assert report["query"] == "(howler.id:*)" or report["outcome"] == "skipped"

        assert "outcome" in report
        assert report["outcome"] in ["success", "skipped"]


def test_execute_action_labels_fail(datastore: HowlerDatastore, login_session):
    session, host = login_session

    req = {
        "request_id": str(uuid4()),
        "query": "howler.id:*",
        "operations": [
            {
                "operation_id": "add_label",
                "data_json": json.dumps(
                    {"category": "doesnexistandneverwill", "label": "potato"}
                ),
            },
            {
                "operation_id": "remove_label",
                "data": {"category": "doesnexistandneverwill", "label": "potato"},
            },
        ],
    }

    resp = get_api_data(
        session,
        f"{host}/api/v1/action/execute",
        method="POST",
        data=json.dumps(req),
    )

    for report in resp.values():
        assert len(report) == 1
        report = report[0]

        assert "query" in report
        assert report["query"] == "(howler.id:*)"

        assert "outcome" in report
        assert report["outcome"] == "error"

        assert "message" in report
        assert "'doesnexistandneverwill'" in report["message"]


def test_execute_transition_basic(datastore: HowlerDatastore, login_session):
    session, host = login_session

    req = {
        "request_id": str(uuid4()),
        "query": "howler.status:open",
        "operations": [
            {
                "operation_id": "transition",
                "data_json": json.dumps(
                    {
                        "status": "open",
                        "transition": "assign_to_other",
                        "assignee": "user",
                    }
                ),
            }
        ],
    }

    resp = get_api_data(
        session,
        f"{host}/api/v1/action/execute",
        method="POST",
        data=json.dumps(req),
    )

    for report in resp.values():
        assert len(report) == 1
        report = report[0]

        assert "query" in report
        assert report["query"].startswith("(howler.id:(")

        assert "outcome" in report
        assert report["outcome"] == "success"

        assert "message" in report
        assert report["message"].startswith(
            "The transition assign_to_other successfully executed on "
        )
        assert report["message"].endswith(" hits.")

        total = int(re.sub(r"^.+?(\d+).+$", r"\1", report["message"]))

        # Wait for updates to be applied across the server
        time.sleep(5)

        assert datastore.hit.search("howler.assignment:user")["total"] >= total


def test_execute_transition_skipped(datastore: HowlerDatastore, login_session):
    session, host = login_session

    req = {
        "request_id": str(uuid4()),
        "query": "howler.id:*",
        "operations": [
            {
                "operation_id": "transition",
                "data": {
                    "status": "open",
                    "transition": "assign_to_other",
                    "assignee": "goose",
                },
            }
        ],
    }

    resp = get_api_data(
        session,
        f"{host}/api/v1/action/execute",
        method="POST",
        data=json.dumps(req),
    )

    for report in resp.values():
        assert len(report) == 2

        # First report
        assert "query" in report[0]
        assert report[0]["query"].startswith("((")
        assert report[0]["query"].endswith(") AND -howler.status:open)")

        assert "outcome" in report[0]
        assert report[0]["outcome"] == "skipped"

        assert "message" in report[0]

        # Second report
        assert "query" in report[1]
        assert report[1]["query"].startswith("(howler.id:(")

        assert "outcome" in report[1]
        assert report[1]["outcome"] == "success"

        assert "message" in report[1]


def test_execute_transition_multiple(datastore: HowlerDatastore, login_session):
    session, host = login_session

    reqs = [
        {
            "request_id": str(uuid4()),
            "query": "howler.id:*",
            "operations": [
                {
                    "operation_id": "transition",
                    "data": {
                        "status": "open",
                        "transition": "assign_to_me",
                        "assignee": "admin",
                    },
                }
            ],
        },
        {
            "request_id": str(uuid4()),
            "query": "howler.id:*",
            "operations": [
                {
                    "operation_id": "transition",
                    "data": {
                        "status": "in-progress",
                        "transition": "assign_to_me",
                        "assignee": "admin",
                    },
                }
            ],
        },
        {
            "request_id": str(uuid4()),
            "query": "howler.id:*",
            "operations": [
                {
                    "operation_id": "transition",
                    "data": {"status": "in-progress", "transition": "release"},
                }
            ],
        },
        {
            "request_id": str(uuid4()),
            "query": "howler.id:*",
            "operations": [
                {
                    "operation_id": "transition",
                    "data": {
                        "status": "open",
                        "transition": "assess",
                        "assignee": "admin",
                        "assessment": "legitimate",
                    },
                }
            ],
        },
        {
            "request_id": str(uuid4()),
            "query": "howler.id:*",
            "operations": [
                {
                    "operation_id": "transition",
                    "data": {
                        "status": "on-hold",
                        "transition": "assess",
                        "assignee": "admin",
                        "assessment": "legitimate",
                    },
                }
            ],
        },
        {
            "request_id": str(uuid4()),
            "query": "howler.id:*",
            "operations": [
                {
                    "operation_id": "transition",
                    "data": {
                        "status": "in-progress",
                        "transition": "assess",
                        "assignee": "admin",
                        "assessment": "legitimate",
                    },
                }
            ],
        },
        {
            "request_id": str(uuid4()),
            "query": "howler.id:*",
            "operations": [
                {
                    "operation_id": "transition",
                    "data": {"status": "resolved", "transition": "re_evaluate"},
                }
            ],
        },
        {
            "request_id": str(uuid4()),
            "query": "howler.id:*",
            "operations": [
                {
                    "operation_id": "transition",
                    "data": {
                        "status": "in-progress",
                        "transition": "promote",
                    },
                }
            ],
        },
        {
            "request_id": str(uuid4()),
            "query": "howler.id:*",
            "operations": [
                {
                    "operation_id": "transition",
                    "data": {"status": "in-progress", "transition": "release"},
                }
            ],
        },
    ]

    for req in reqs:
        resp = get_api_data(
            session,
            f"{host}/api/v1/action/execute",
            method="POST",
            data=json.dumps(req),
        )

        for report in resp.values():
            for entry in report:
                assert entry["outcome"] in ["skipped", "success"]

                assert "query" in entry
                assert "title" in entry
                assert "message" in entry

    assert (
        datastore.hit.search("howler.status:open")["total"]
        == datastore.hit.search("howler.id:*")["total"]
    )

    assert (
        datastore.hit.search("howler.escalation:alert")["total"]
        == datastore.hit.search("howler.id:*")["total"]
    )


def test_create_action_fails(datastore: HowlerDatastore, login_session):
    session, host = login_session

    req: dict[str, Any] = {}

    with pytest.raises(APIError) as err:
        get_api_data(
            session,
            f"{host}/api/v1/action",
            method="POST",
            data=json.dumps(req),
        )

    assert err.value.args[0] == "400: You must specify a name."

    req["name"] = ""

    with pytest.raises(APIError) as err:
        get_api_data(
            session,
            f"{host}/api/v1/action",
            method="POST",
            data=json.dumps(req),
        )

    assert err.value.args[0] == "400: Name cannot be empty."

    req["name"] = "Test Create action"

    with pytest.raises(APIError) as err:
        get_api_data(
            session,
            f"{host}/api/v1/action",
            method="POST",
            data=json.dumps(req),
        )

    assert err.value.args[0] == "400: You must specify a query."

    req["query"] = ""

    with pytest.raises(APIError) as err:
        get_api_data(
            session,
            f"{host}/api/v1/action",
            method="POST",
            data=json.dumps(req),
        )

    assert err.value.args[0] == "400: Query cannot be empty."

    req["query"] = "howler.id:*"

    with pytest.raises(APIError) as err:
        get_api_data(
            session,
            f"{host}/api/v1/action",
            method="POST",
            data=json.dumps(req),
        )

    assert err.value.args[0] == "400: You must specify a list of operations."

    req["operations"] = "banana"

    with pytest.raises(APIError) as err:
        get_api_data(
            session,
            f"{host}/api/v1/action",
            method="POST",
            data=json.dumps(req),
        )

    assert err.value.args[0] == "400: 'operations' must be a list of operations."

    req["operations"] = []

    with pytest.raises(APIError) as err:
        get_api_data(
            session,
            f"{host}/api/v1/action",
            method="POST",
            data=json.dumps(req),
        )

    assert err.value.args[0] == "400: You must specify at least one operation."


def test_create_action_success(datastore: HowlerDatastore, login_session):
    session, host = login_session

    req = {
        "name": "Test Create action",
        "owner_id": "admin",
        "query": "howler.id:*",
        "owner_id": "admin",
        "operations": [
            {
                "operation_id": "add_label",
                "data": {"category": "generic", "label": "test"},
            }
        ],
    }

    resp = get_api_data(
        session,
        f"{host}/api/v1/action",
        method="POST",
        data=json.dumps(req),
    )

    assert resp.get("action_id", None) is not None

    assert datastore.action.exists(resp["action_id"])


def test_update_action_success(datastore: HowlerDatastore, login_session):
    session, host = login_session

    action_id = datastore.action.search("*:*", rows=1)["items"][0]["action_id"]

    req = {
        "name": "Test Update action",
        "query": "howler.id:*",
        "owner_id": "admin",
        "operations": [
            {
                "operation_id": "add_label",
                "data": {"category": "generic", "label": "test"},
            }
        ],
    }

    resp = get_api_data(
        session,
        f"{host}/api/v1/action/{action_id}",
        method="PUT",
        data=json.dumps(req),
    )

    assert resp.get("name", None) is not None

    assert resp["name"] == "Test Update action"
