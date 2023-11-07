import base64
import json
import os
import uuid

import pytest
from conftest import APIError, get_api_data

from howler.datastore.howler_store import HowlerDatastore
from howler.odm.helper import create_users_with_username
from howler.odm.models.hit import Hit
from howler.odm.random_data import create_hits, wipe_analytics, wipe_hits
from howler.odm.randomizer import (
    get_random_filename,
    get_random_hash,
    get_random_ip,
    get_random_iso_date,
)
from howler.services import hit_service
from howler.utils.dict_utils import flatten

valid_hit_data = [
    {
        "howler": {
            "id": str(uuid.uuid4()),
            "analytic": "A test hit 1",
            "assignment": "user",
            "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
            "score": "0.8",
            "labels": {"assignments": ["test", "test2"], "generic": ["test", "test2"]},
            "votes": {"benign": {}, "obscure": {}, "malicious": {}},
        },
    },
    {
        "howler": {
            "id": str(uuid.uuid4()),
            "analytic": "A test hit 2",
            "assignment": "user",
            "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
            "score": "0.2",
            "labels": {
                "assignments": ["test", "banana"],
                "generic": ["test", "banana"],
            },
            "votes": {"benign": {}, "obscure": {}, "malicious": {}},
        },
    },
    {
        "howler": {
            "id": str(uuid.uuid4()),
            "analytic": "A test hit 3",
            "assignment": "user",
            "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
            "score": "0.4",
            "labels": {"assignments": ["test"], "generic": ["test"]},
            "votes": {"benign": {}, "obscure": {}, "malicious": {}},
        },
    },
    {
        "howler": {
            "id": str(uuid.uuid4()),
            "analytic": "A test assigned hit 1",
            "assignment": "admin",
            "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
            "score": "0.8",
            "labels": {"assignments": ["test"], "generic": ["test"]},
            "votes": {"benign": {}, "obscure": {}, "malicious": {}},
        },
    },
    {
        "howler": {
            "id": str(uuid.uuid4()),
            "analytic": "A test assigned hit 2",
            "assignment": "admin",
            "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
            "score": "0.8",
            "labels": {"assignments": ["test"], "generic": ["test"]},
            "votes": {"benign": {}, "obscure": {}, "malicious": {}},
        },
    },
    {
        "howler": {
            "id": str(uuid.uuid4()),
            "analytic": "A test assigned hit 3",
            "assignment": "admin",
            "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
            "score": "0.8",
            "labels": {"assignments": ["test"], "generic": ["test"]},
            "votes": {"benign": {}, "obscure": {}, "malicious": {}},
        },
    },
    {
        "howler": {
            "id": "assign-test",
            "analytic": "assign-test",
            "assignment": "unassigned",
            "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
            "score": "0.8",
            "labels": {"assignments": [], "generic": []},
        },
    },
    {
        "howler": {
            "id": "transition-open-not-assigned",
            "analytic": "transition-open-not-assigned",
            "assignment": "unassigned",
            "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bc",
            "score": "0",
            "status": "open",
            "labels": {"assignments": [], "generic": []},
        },
    },
    {
        "howler": {
            "id": "transition-open-assigned",
            "analytic": "transition-open-assigned",
            "assignment": "donald",
            "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bd",
            "score": "0",
            "status": "open",
            "labels": {"assignments": [], "generic": []},
        },
    },
    {
        "howler": {
            "id": "transition-open-do-not-modify",
            "analytic": "transition-open-do-not-modify",
            "assignment": "unassigned",
            "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bd",
            "score": "0",
            "status": "open",
            "labels": {"assignments": [], "generic": []},
        },
    },
    {
        "howler": {
            "id": "transition-in-progress-to-hold",
            "analytic": "transition-in-progress-to-hold",
            "assignment": "donald",
            "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48be",
            "score": "0",
            "status": "in-progress",
            "labels": {"assignments": [], "generic": []},
        },
    },
    {
        "howler": {
            "id": "transition-in-progress-to-complete",
            "analytic": "transition-in-progress-to-complete",
            "assignment": "donald",
            "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48be",
            "score": "0",
            "status": "in-progress",
            "labels": {"assignments": [], "generic": []},
        },
    },
    {
        "howler": {
            "id": "transition-on-hold",
            "analytic": "transition-on-hold",
            "assignment": "donald",
            "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bc",
            "score": "0",
            "status": "on-hold",
            "labels": {"assignments": [], "generic": []},
        },
    },
]

# Only this data will be used in an attempt to create a Hit
invalid_hit_data = [
    {"id": "invalid_hit_1", "jibberish_fild": "Value that doesn't matter"},
    {},
    {"array": []},
]

hit_data_with_original = {
    "howler": {
        "id": "transition-on-hold",
        "analytic": "transition-on-hold",
        "assignment": "donald",
        "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bc",
        "score": "0",
        "status": "on-hold",
        "labels": {"assignments": [], "generic": []},
        "data": [
            {"extra": True, "whatever": {"hi": "hello"}},
            json.dumps({"extra": True, "whatever": {"hi": "hello"}}),
        ],
    },
}


usernames = ["donald", "huey", "louie", "dewey"]


@pytest.fixture(scope="module")
def datastore(datastore_connection: HowlerDatastore):
    try:
        wipe_hits(datastore_connection)
        create_users_with_username(datastore_connection, usernames)

        # Create hits for get_hit test
        for hit in valid_hit_data:
            datastore_connection.hit.save(hit["howler"]["id"], hit)

        create_hits(datastore_connection, hit_count=10)

        # Commit changes to DataStore
        datastore_connection.hit.commit()

        yield datastore_connection
    finally:
        wipe_hits(datastore_connection)
        wipe_analytics(datastore_connection)


# noinspection PyUnusedLocal
def test_create_tools_hits(datastore: HowlerDatastore, login_session):
    session, host = login_session

    tool_name = "test"
    map = {
        "analytic": ["howler.analytic"],
        "file.sha256": ["file.hash.sha256", "howler.hash"],
        "file.name": ["file.name"],
        "src_ip": ["source.ip", "related.ip"],
        "dest_ip": ["destination.ip", "related.ip"],
        "time.created": ["event.start"],
        "time.completed": ["event.end"],
        "raw": ["howler.data"],
        "zone": ["cloud.availability_zone"],
    }
    hits = []
    for _ in range(10):
        hits.append(
            {
                "src_ip": get_random_ip(),
                "dest_ip": get_random_ip(),
                "file": {"name": get_random_filename(), "sha256": get_random_hash(64)},
                "time": {
                    "created": get_random_iso_date(),
                    "completed": get_random_iso_date(),
                },
                "zone": "deprecated",
            }
        )

    for hit in hits:
        hit["raw"] = {**hit}

    res = get_api_data(
        session,
        f"{host}/api/v1/tools/{tool_name}/hits",
        data=json.dumps({"map": map, "hits": hits}),
        method="POST",
    )

    assert len(res) == len(hits)
    for hit in res:
        assert "warn" in hit
        assert "error" in hit
        assert "id" in hit
        assert hit["error"] is None
        assert isinstance(hit["id"], str)


def test_create_tools_hits_broken_map(datastore: HowlerDatastore, login_session):
    session, host = login_session

    tool_name = "test"
    # Test broken map
    broken_map = {
        "file.sha256": ["file.sha256"],
    }
    hits = []
    for _ in range(10):
        hits.append(
            {
                "src_ip": get_random_ip(),
                "dest_ip": get_random_ip(),
                "file": {"name": get_random_filename(), "sha256": get_random_hash(64)},
                "time": {
                    "created": get_random_iso_date(),
                    "completed": get_random_iso_date(),
                },
            }
        )
    with pytest.raises(APIError):
        get_api_data(
            session,
            f"{host}/api/v1/tools/{tool_name}/hits",
            data=json.dumps({"map": broken_map, "hits": hits}),
            method="POST",
        )


def test_create_tools_hits_invalid_hits(datastore: HowlerDatastore, login_session):
    session, host = login_session

    tool_name = "test"
    map = {
        "analytic": ["howler.analytic"],
        "file.sha256": ["file.hash.sha256", "howler.hash"],
        "file.name": ["file.name"],
        "src_ip": ["source.ip", "related.ip"],
        "dest_ip": ["destination.ip", "related.ip"],
        "time.created": ["event.start"],
        "time.completed": ["event.end"],
    }
    # Test invalid data
    invalid_hits = [
        {
            "src_ip": get_random_filename(),
            "dest_ip": get_random_iso_date(),
            "file": {"name": get_random_ip(), "sha256": get_random_iso_date()},
            "time": {
                "created": get_random_ip(),
                "completed": get_random_hash(64),
            },
        }
    ]

    with pytest.raises(APIError):
        get_api_data(
            session,
            f"{host}/api/v1/tools/{tool_name}/hits",
            data=json.dumps({"map": map, "hits": invalid_hits}),
            method="POST",
        )


def test_create_tools_hits_valid_hits_ignore_extra_values_true(
    datastore: HowlerDatastore, login_session
):
    session, host = login_session

    tool_name = "test"
    map = {
        "analytic": ["howler.analytic"],
        "file.sha256": ["file.hash.sha256", "howler.hash"],
        "file.name": ["file.name"],
        "src_ip": ["source.ip", "related.ip"],
        "dest_ip": ["destination.ip", "related.ip"],
        "time.created": ["event.start"],
        "time.completed": ["event.end"],
        "potato": ["potato"],
    }
    # Test extra data
    hits = [
        {
            "src_ip": get_random_ip(),
            "dest_ip": get_random_ip(),
            "file": {"name": get_random_filename(), "sha256": get_random_hash(64)},
            "time": {
                "created": get_random_iso_date(),
                "completed": get_random_iso_date(),
            },
            "potato": "unreal. absolutely phenominal",
        }
    ]

    res = get_api_data(
        session,
        f"{host}/api/v1/tools/{tool_name}/hits?ignore_extra_values=true",
        data=json.dumps({"map": map, "hits": hits}),
        method="POST",
    )

    assert len(res) == len(hits)
    for hit in res:
        assert "warn" in hit
        assert "error" in hit
        assert "id" in hit
        assert hit["error"] is None
        assert isinstance(hit["id"], str)


def test_create_tools_hits_valid_hits_ignore_extra_values_false(
    datastore: HowlerDatastore, login_session
):
    session, host = login_session

    tool_name = "test"
    map = {
        "analytic": ["howler.analytic"],
        "file.sha256": ["file.hash.sha256", "howler.hash"],
        "file.name": ["file.name"],
        "src_ip": ["source.ip", "related.ip"],
        "dest_ip": ["destination.ip", "related.ip"],
        "time.created": ["event.start"],
        "time.completed": ["event.end"],
        "potato": ["potato"],
    }
    # Test hit + extra data but not accepted (ignore_extra_values set to default/false)
    hits = [
        {
            "src_ip": get_random_ip(),
            "dest_ip": get_random_ip(),
            "file": {"name": get_random_filename(), "sha256": get_random_hash(64)},
            "time": {
                "created": get_random_iso_date(),
                "completed": get_random_iso_date(),
            },
            "potato": "unreal. absolutely phenominal",
        }
    ]

    with pytest.raises(APIError):
        get_api_data(
            session,
            f"{host}/api/v1/tools/{tool_name}/hits",
            data=json.dumps({"map": map, "hits": hits}),
            method="POST",
        )


def test_create_valid_hits(datastore, login_session):
    """Test that /api/v1/hit creates hits using valid data"""
    session, host = login_session

    data = [
        {
            "howler": {
                "analytic": "A test for creating a hit",
                "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
                "score": "0.8",
                "outline": {
                    "threat": "10.0.0.1",
                    "target": "asdf123",
                    "indicators": ["me.ps1"],
                    "summary": "This is a summary",
                },
            },
        },
        {
            "howler": {
                "analytic": "A test for creating a hit",
                "assignment": "donald",
                "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
                "score": "0.8",
                "outline": {
                    "threat": "10.0.0.2",
                    "target": "second target",
                    "indicators": ["test.ps1"],
                    "summary": "This is a summary",
                },
            },
        },
        {
            "event": {
                "reason": "To test the create endpoint with valid data.",
            },
            "howler": {
                "analytic": "A test for creating a hit",
                "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
                "score": "0.8",
                "outline": {
                    "threat": "10.0.0.3",
                    "target": "third target",
                    "indicators": ["test.ps1"],
                    "summary": "This is a summary",
                },
            },
        },
    ]

    # POST hits
    response = get_api_data(
        session=session, url=f"{host}/api/v1/hit/", data=json.dumps(data), method="POST"
    )
    assert len(response["invalid"]) == 0

    # All posts should be successful
    for i in range(len(data)):
        assert data[i]["howler"]["hash"] == response["valid"][i]["howler"]["hash"]
        assert data[i]["howler"]["outline"] is not None


def test_create_invalid_hits(datastore: HowlerDatastore, login_session):
    """Test that /api/v1/hit fails when it receives invalid data"""
    session, host = login_session

    with pytest.raises(APIError):
        response = get_api_data(
            session=session,
            url=f"{host}/api/v1/hit/",
            data=json.dumps(invalid_hit_data),
            method="POST",
        )

        assert len(response["invalid"]) == len(invalid_hit_data)

        for invalid_hit in response["invalid"]:
            assert invalid_hit["error"] != ""


def test_create_with_howler_data_field(datastore: HowlerDatastore, login_session):
    session, host = login_session

    response = get_api_data(
        session=session,
        url=f"{host}/api/v1/hit/",
        data=json.dumps([hit_data_with_original, flatten(hit_data_with_original)]),
        method="POST",
    )

    assert len(response["valid"]) == 2

    for new_hit in response["valid"]:
        for entry in datastore.hit.get_if_exists(new_hit["howler"]["id"])["howler"][
            "data"
        ]:
            assert isinstance(entry, str)
            assert json.loads(entry)["extra"]


def test_convert_hit():
    odm, _ = hit_service.convert_hit(hit_data_with_original, True)

    assert odm.howler.id != hit_data_with_original["howler"]["id"]

    assert all(isinstance(entry, str) for entry in odm.howler.data)
    assert all(json.loads(entry)["extra"] for entry in odm.howler.data)


def test_same_hash(datastore: HowlerDatastore, login_session):
    session, host = login_session

    res = get_api_data(
        session=session,
        url=f"{host}/api/v1/hit/",
        data=json.dumps(
            [
                {"howler": {"analytic": "test", "score": 1}},
                {"howler": {"analytic": "test", "score": 1}},
            ]
        ),
        method="POST",
    )

    assert len(res["valid"]) == 2

    assert res["valid"][0]["howler"]["hash"] == res["valid"][1]["howler"]["hash"]


def test_create_invalid_hits_ignore_invalid_values_false(
    datastore: HowlerDatastore, login_session
):
    """Test that /api/v1/hit fails when it receives invalid data"""
    session, host = login_session

    hits = [
        {
            "howler": {
                "id": "test_create_hit_please_be_unique_1319929j",
                "analytic": "A test for creating a hit",
                "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
                "score": "0.8",
                "outline": {
                    "header": {
                        "threat": "10.0.0.3",
                        "target": "third target",
                        "indicators": ["test.ps1"],
                        "summary": "This is a summary",
                    }
                },
            },
            "potato": "I just think they're neat!",
        }
    ]
    with pytest.raises(APIError):
        response = get_api_data(
            session=session,
            url=f"{host}/api/v1/hit/?ignore_extra_values=false",
            data=json.dumps(hits),
            method="POST",
        )
        assert len(response["invalid"]) == len(hits)

        for invalid_hit in response["invalid"]:
            assert invalid_hit["error"] != ""


def test_create_invalid_hits_ignore_invalid_values_true(
    datastore: HowlerDatastore, login_session
):
    """Test that /api/v1/hit succeeds when it receives invalid data with ignore_extra_values set true"""
    session, host = login_session

    hits = [
        {
            "howler": {
                "analytic": "A test for creating a hit",
                "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
                "score": "0.8",
                "outline": {
                    "threat": "10.0.0.3",
                    "target": "third target",
                    "indicators": ["test.ps1"],
                    "summary": "This is a summary",
                },
            },
            "potato": "I just think they're neat!",
        }
    ]
    response = get_api_data(
        session=session,
        url=f"{host}/api/v1/hit?ignore_extra_values=true",
        data=json.dumps(hits),
        method="POST",
    )

    assert len(response["invalid"]) == 0

    # All posts should be successful
    for i in range(len(hits)):
        assert response["valid"][i]["howler"]["id"] is not None
        assert response["valid"][i].get("potato") is None


def test_validate_hits(datastore: HowlerDatastore, login_session):
    session, host = login_session

    copied_id = str(uuid.uuid4())
    valid_data = [
        {
            "howler": {
                "id": str(uuid.uuid4()),
                "analytic": "A test for creating a hit",
                "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
                "score": 0.8,
            },
        },
        {
            "howler": {
                "id": str(uuid.uuid4()),
                "analytic": "A test for creating a hit",
                "assignment": "donald",
                "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
                "score": 0.8,
            },
        },
        {
            "event": {
                "reason": "To test the create endpoint with valid data.",
                "id": copied_id,
            },
            "howler": {
                "id": copied_id,
                "analytic": "A test for creating a hit",
                "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
                "score": 0.8,
            },
        },
    ]

    data = [*valid_data, *invalid_hit_data]

    response = get_api_data(
        session=session,
        url=f"{host}/api/v1/hit/validate/",
        data=json.dumps(data),
        method="POST",
    )

    assert len(response["valid"]) == len(valid_data)
    assert len(response["invalid"]) == len(invalid_hit_data)


def test_get_hit(datastore: HowlerDatastore, login_session):
    """Test that /api/v1/hit/<id>/ returns the right hit."""
    session, host = login_session

    for hit in valid_hit_data[:2]:
        response = get_api_data(
            session,
            f"{host}/api/v1/hit/{hit['howler']['id']}/",
        )
        odmHit = datastore.hit.get(hit["howler"]["id"], as_obj=False, version=True)
        assert response == odmHit[0]


def test_get_assigned_hits(datastore: HowlerDatastore, login_session):
    """Test that /api/v1/hit/user endpoint returns all of a user's assigned hits."""
    session, host = login_session

    response = get_api_data(session, f"{host}/api/v1/hit/user/")

    odmHits = datastore.hit.search("howler.assignment:admin", as_obj=False)["items"]

    assert len(response) == len(odmHits)

    for odm in odmHits:
        match_found = False

        for hit in response:
            if hit == odm:
                match_found = True

        assert match_found


def test_add_labels(datastore: HowlerDatastore, login_session):
    session, host = login_session

    for hit in valid_hit_data[:2]:
        # get current hit
        current_hit: Hit = datastore.hit.get(hit["howler"]["id"])

        for label_set in current_hit.howler.labels.fields().keys():
            new_labels = ["apa2b", "cccs"]

            response = get_api_data(
                session=session,
                url=f"{host}/api/v1/hit/{hit['howler']['id']}/labels/{label_set}/",
                method="PUT",
                data=json.dumps({"value": new_labels}),
            )

            assert response["howler"]

            updated_hit: Hit = datastore.hit.get(hit["howler"]["id"])
            for label in new_labels:
                assert label in updated_hit.howler.labels[label_set]
                assert label in [log.new_value for log in updated_hit.howler.log]


def test_add_labels_existing(datastore: HowlerDatastore, login_session):
    session, host = login_session

    hit = valid_hit_data[0]
    # get current hit
    current_hit: Hit = datastore.hit.get(hit["howler"]["id"])

    for label_set in current_hit.howler.labels.fields().keys():
        existing_labels = current_hit[f"howler.labels.{label_set}"]

        if len(existing_labels) != 0:
            with pytest.raises(APIError) as err:
                get_api_data(
                    session=session,
                    url=f"{host}/api/v1/hit/{hit['howler']['id']}/labels/{label_set}/",
                    method="PUT",
                    data=json.dumps({"value": existing_labels}),
                )

            assert err.value.args[0].startswith("400: Cannot add duplicate labels:")


def test_remove_labels(datastore: HowlerDatastore, login_session):
    session, host = login_session

    for hit in valid_hit_data[:2]:
        # get current hit
        current_hit: Hit = datastore.hit.get(hit["howler"]["id"])

        for label_set in current_hit.howler.labels.fields().keys():
            remove_labels = current_hit[f"howler.labels.{label_set}"]

            if len(remove_labels) != 0:
                response = get_api_data(
                    session=session,
                    url=f"{host}/api/v1/hit/{hit['howler']['id']}/labels/{label_set}/",
                    method="DELETE",
                    data=json.dumps({"value": remove_labels}),
                )

                assert response["howler"]

                updated_hit: Hit = datastore.hit.get(hit["howler"]["id"])
                assert len(updated_hit.howler.labels[label_set]) == 0
                for removed_label in remove_labels:
                    assert removed_label in [
                        log.new_value for log in updated_hit.howler.log
                    ]


def test_add_labels_missing(datastore: HowlerDatastore, login_session):
    session, host = login_session

    hit = valid_hit_data[0]
    # get current hit
    new_assignments = ["apa2b", "cccs"]

    with pytest.raises(APIError) as err:
        get_api_data(
            session=session,
            url=f"{host}/api/v1/hit/{hit['howler']['id']}/labels/thisshouldneverexistlmao/",
            method="PUT",
            data=json.dumps({"value": new_assignments}),
        )

    assert err.value.args[0] == "404: Label set thisshouldneverexistlmao does not exist"


def test_delete_hit(datastore: HowlerDatastore, login_session):
    """Test that DELETE /api/v1/hit/ endpoint deletes a hit"""
    session, host = login_session

    hits_to_delete = [
        {
            "howler": {
                "id": "test_delete__hit_please_be_unique_1291929u",
                "analytic": "A test for deleting a hit",
                "assignment": "donald",
                "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
                "score": "0.8",
            },
        },
        {
            "howler": {
                "id": "test_delete__hit_please_be_unique_1391929d",
                "analytic": "A test for deleting a hit",
                "assignment": "donald",
                "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
                "score": "0.8",
            },
        },
    ]

    # Create hits to then delete
    for hit in hits_to_delete:
        datastore.hit.save(hit["howler"]["id"], hit)

    hit_ids = [hit["howler"]["id"] for hit in hits_to_delete]

    # Assert that hits exist
    for id in hit_ids:
        assert datastore.hit.exists(id)

    get_api_data(
        session=session,
        url=f"{host}/api/v1/hit/",
        data=json.dumps(hit_ids),
        method="DELETE",
    )

    # Assert that hits do not exist
    for id in hit_ids:
        assert not datastore.hit.exists(id)


def test_delete_by_admin(datastore: HowlerDatastore, login_session):
    """Test that DELETE /api/v1/hit/ endpoint only deletes hits by admin"""
    session, host = login_session

    hits_to_delete = [
        {
            "howler": {
                "id": "test_delete__hit_please_be_unique_1291929u",
                "analytic": "A test for deleting a hit",
                "assignment": "donald",
                "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
                "score": "0.8",
            },
        },
        {
            "howler": {
                "id": "test_delete__hit_please_be_unique_1391929d",
                "analytic": "A test for deleting a hit",
                "assignment": "donald",
                "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
                "score": "0.8",
            },
        },
    ]

    # Create hits to then delete
    for hit in hits_to_delete:
        datastore.hit.save(hit["howler"]["id"], hit)

    hit_ids = [hit["howler"]["id"] for hit in hits_to_delete]

    # Assert that hits exist
    for id in hit_ids:
        assert datastore.hit.exists(id)

    with pytest.raises(APIError):
        get_api_data(
            session=session,
            url=f"{host}/api/v1/hit/",
            data=json.dumps(hit_ids),
            headers={
                "Authorization": f"Basic {base64.b64encode(b'user:devkey:user').decode('utf-8')}"
            },
            method="DELETE",
        )

    # Assert that hits do still exist
    for id in hit_ids:
        assert datastore.hit.exists(id)


def test_delete_existing_and_non_existing_hits(
    datastore: HowlerDatastore, login_session
):
    """Test that DELETE /api/v1/hit/ endpoint deletes all hits"""
    session, host = login_session

    hits_to_delete = [
        {
            "howler": {
                "id": "test_delete__hit_please_be_unique_1294929u",
                "analytic": "A test for deleting a hit",
                "assignment": "donald",
                "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
                "score": "0.2",
            },
        },
        {
            "howler": {
                "id": "test_delete__hit_please_be_unique_1391922d",
                "analytic": "A test for deleting a hit",
                "assignment": "donald",
                "hash": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
                "score": "0.8",
            },
        },
    ]

    non_existing_hit_ids = [
        "Inexistent_hit_to_delete_1",
        "Inexistent_hit_to_delete_2",
        "Inexistent_hit_to_delete_3",
    ]

    # Create hits to then delete
    for hit in hits_to_delete:
        datastore.hit.save(hit["howler"]["id"], hit)

    existing_hit_ids = [hit["howler"]["id"] for hit in hits_to_delete]
    hit_ids_to_delete = existing_hit_ids + non_existing_hit_ids

    # Assert that hits exist
    for id in existing_hit_ids:
        assert datastore.hit.exists(id)

    # Assert that hits do not exist
    for id in non_existing_hit_ids:
        assert not datastore.hit.exists(id)

    with pytest.raises(APIError) as err:
        get_api_data(
            session=session,
            url=f"{host}/api/v1/hit/",
            data=json.dumps(hit_ids_to_delete),
            method="DELETE",
        )

    assert err.value.args[0].startswith("404: Hit ids")
    assert err.value.args[0].endswith("not exist.")


def test_hit_worklog(datastore: HowlerDatastore, login_session):
    session, host = login_session

    hit = valid_hit_data[0]

    # get current hit
    current_hit, version = datastore.hit.get(hit["howler"]["id"], version=True)

    current_worklog_len = len(current_hit.howler.log)

    get_api_data(
        session=session,
        url=f"{host}/api/v1/hit/{current_hit['howler']['id']}/comments",
        method="POST",
        data=json.dumps({"value": "hello", "version_no": None}),
        headers={
            "If-Match": version,
            "content-type": "application/json",
        },
    )

    updated_hit: Hit = datastore.hit.get(current_hit["howler"]["id"])
    assert len(updated_hit.howler.log) > current_worklog_len


@pytest.mark.skip(reason="AL test - doesn't need to be run")
def test_pull_from_assemblyline(datastore: HowlerDatastore, login_session):
    from assemblyline_client import get_client as get_al_client

    user = os.getenv("AL_USER", None)
    apikey = os.getenv("AL_APIKEY", None)

    if not (user and apikey):
        pytest.skip("Assemblyline credentials required to run this test!")

    host = "https://malware-stg.cyber.gc.ca"

    al = get_al_client(host, apikey=(user, apikey))

    al_entries = al.alert.list(rows=1)
    al_alert = al_entries["items"][0]

    al_hwl_map = {
        "analytic": ["howler.analytic"],
        "org_name": ["organization.name"],
        "framework": ["threat.framework"],
        "tactic_id": ["threat.tactic.id"],
        "tactic_name": ["threat.tactic.name"],
        "scanner_stats": ["threat.indicator.scanner_stats"],
        "file.md5": ["related.hash", "file.hash.md5"],
        "file.sha1": ["related.hash", "file.hash.sha1"],
        "file.sha256": ["related.hash", "file.hash.sha256", "howler.hash"],
        "al.uri_static": ["related.uri"],
        "al.uri_dynamic": ["related.uri"],
        "al.domain_static": ["related.hosts"],
        "al.domain_dynamic": ["related.hosts"],
        "alert_id": ["related.id"],
        "file.name": ["file.name"],
        "file.size": ["file.size"],
        "file.mime_type": ["file.mime_type"],
        "al.detailed.av": ["assemblyline.antivirus"],
        "al.detailed.attrib": ["assemblyline.attribution"],
        "al.detailed.behavior": ["assemblyline.behaviour"],
        "al.detailed.uri": ["assemblyline.uri"],
        "al.detailed.domain": ["assemblyline.domain"],
        "al.detailed.yara": ["assemblyline.yara"],
        "al.detailed.heuristic": ["assemblyline.heuristic"],
        "al.detailed.attack_category": ["assemblyline.mitre.tactic"],
        "al.detailed.attack_pattern": ["assemblyline.mitre.technique"],
    }

    al_alert["analytic"] = "AssemblyLine"
    al_alert["org_name"] = al_alert["metadata"].get("ministerial_authority", "Unknown")
    al_alert["framework"] = "MITRE ATT&CK"
    al_alert["tactic_id"] = "TA0001"
    al_alert["tactic_name"] = "Initial Access"  # TODO: Use howler to populate this
    al_alert["scanner_stats"] = len(al_alert["verdict"]["malicious"])

    session, host = login_session
    get_api_data(
        session,
        f"{host}/api/v1/hit/assemblyline/",
        data=json.dumps({"map": al_hwl_map, "hits": [al_alert]}),
        method="POST",
    )


def test_hit_warnings(datastore: HowlerDatastore, login_session):
    session, host = login_session

    result = get_api_data(
        session,
        f"{host}/api/v1/hit/",
        data=json.dumps(
            [
                {
                    "howler.analytic": "Bad.Name",
                    "howler.detection": "Bad.Detection",
                    "howler.score": 0.0,
                }
            ]
        ),
        method="POST",
    )

    assert len(result["warnings"]) == 2
    assert result["warnings"][0].startswith("The value Bad.Name")
    assert result["warnings"][1].startswith("The value Bad.Detection")

    result = get_api_data(
        session,
        f"{host}/api/v1/hit/",
        data=json.dumps(
            [
                {
                    "howler.analytic": "Good Name",
                    "howler.detection": "Good Detection",
                    "howler.score": 0.0,
                }
            ]
        ),
        method="POST",
    )

    assert len(result["warnings"]) == 0
