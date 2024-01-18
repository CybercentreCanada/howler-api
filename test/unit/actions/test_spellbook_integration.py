from pathlib import Path
from mock import MagicMock, patch

import pytest
from howler.common.loader import datastore
from howler.actions.spellbook import execute
from howler.datastore.howler_store import HowlerDatastore
from howler.odm.models.hit import Hit
from howler.odm.models.user import User
from howler.odm.random_data import create_hits, wipe_hits
from howler.odm.randomizer import random_model_obj


@pytest.fixture(scope="module", autouse=True)
def setup_datastore(datastore_connection: HowlerDatastore):
    try:
        wipe_hits(datastore_connection)
        create_hits(datastore_connection, hit_count=1)
        datastore_connection.hit.commit()

        yield datastore_connection
    finally:
        wipe_hits(datastore_connection)


@patch("howler.actions.spellbook.get_spellbook_client")
def test_execute(mock_client: MagicMock, datastore_connection):
    mock_user = random_model_obj(User)

    mock_spbk_client = MagicMock()
    mock_spbk_client.jobs = MagicMock()
    mock_spbk_client.jobs.trigger = MagicMock()

    mock_client.return_value = mock_spbk_client

    result = execute(
        "howler.id:*",
        "test_dag_id",
        user=mock_user,
        request_id="doesn't matter",
        **{"param_val": "howler.id", "other_val": "bananarama"}
    )

    hit = datastore_connection.hit.search("howler.id:*", fl="howler.id")["items"][0]

    mock_client.assert_called_once()
    mock_spbk_client.jobs.trigger.assert_called_once_with(
        dag_id="test_dag_id",
        param={"param_val": [hit.howler.id], "other_val": "bananarama"},
    )

    assert len(result) == 1

    assert result[0]["outcome"] == "success"
    assert result[0]["title"] == "Executed Successfully"
    assert result[0]["query"] == "howler.id:*"
    assert "SPBK_HOST" in result[0]["message"]
    assert "AF_HOST" in result[0]["message"]
    assert (
        "Your job has been triggered based on the hits matching the query"
        in result[0]["message"]
    )


def test_execute_failed():
    result = execute("howler.analytic:T^R&*H%^J&G%^E", "dag_id_thing")

    assert len(result) == 1

    result = result[0]

    assert result["outcome"] == "error"
    assert result["title"] == "Failed to Execute"
    assert "Unknown exception occurred: " in result["message"]
