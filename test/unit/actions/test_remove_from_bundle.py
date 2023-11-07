from pathlib import Path

import pytest
from howler.common.loader import datastore
from howler.actions.remove_from_bundle import execute
from howler.datastore.howler_store import HowlerDatastore
from howler.odm.models.hit import Hit
from howler.odm.models.user import User
from howler.odm.random_data import wipe_hits
from howler.odm.randomizer import random_model_obj


@pytest.fixture(scope="module", autouse=True)
def setup_datastore(datastore_connection: HowlerDatastore):
    try:
        wipe_hits(datastore_connection)
        datastore_connection.hit.commit()

        yield datastore_connection
    finally:
        wipe_hits(datastore_connection)


def test_execute_no_bundle_id():
    result = execute("howler.id:*", "not_a_valid_id")

    assert len(result) == 1

    result = result[0]

    assert result["outcome"] == "error"
    assert result["title"] == "Invalid Bundle"
    assert (
        result["message"]
        == "Either a hit with ID not_a_valid_id does not exist, or it is not a bundle."
    )


def test_execute():
    bundle: Hit = random_model_obj(Hit)
    bundle.howler.is_bundle = True
    bundle.howler.hits = []
    datastore().hit.save(bundle.howler.id, bundle)

    for i in range(2):
        hit: Hit = random_model_obj(Hit)
        hit.howler.analytic = "TestingRemoveFromBundle"
        if i == 0:
            hit.howler.bundles = [bundle.howler.id]
            bundle.howler.hits.append(hit.howler.id)
        else:
            hit.howler.is_bundle = False
            hit.howler.bundles = []
        datastore().hit.save(hit.howler.id, hit)

    datastore().hit.commit()

    result = execute("howler.analytic:TestingRemoveFromBundle", bundle.howler.id)

    assert len(result) == 2

    print(result)

    assert result[0]["outcome"] == "skipped"
    assert result[0]["title"] == "Skipped Hit not in Bundle"
    assert result[0]["query"].startswith("howler.id:(")
    assert result[0]["message"] == "These hits already are not in the bundle."

    assert result[1]["outcome"] == "success"
    assert result[1]["title"] == "Executed Successfully"
    assert (
        result[1]["message"]
        == f"Matching hits removed from bundle with id {bundle.howler.id}"
    )


def test_execute_failed():
    bundle: Hit = random_model_obj(Hit)
    bundle.howler.is_bundle = True
    bundle.howler.hits = []
    datastore().hit.save(bundle.howler.id, bundle)

    for i in range(3):
        hit: Hit = random_model_obj(Hit)
        hit.howler.analytic = "TestingRemoveFromBundle"
        if i == 0:
            hit.howler.is_bundle = True
        elif i == 1:
            hit.howler.bundles = [bundle.howler.id]
            bundle.howler.hits.append(hit.howler.id)
        datastore().hit.save(hit.howler.id, hit)

    datastore().hit.commit()

    result = execute("howler.analytic:T^R&*H%^J&G%^E", bundle.howler.id)

    assert len(result) == 1

    result = result[0]

    assert result["outcome"] == "error"
    assert result["title"] == "Failed to Execute"
    assert "Failed to parse query " in result["message"]
