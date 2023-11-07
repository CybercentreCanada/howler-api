import pytest
from conftest import get_api_data

from howler.odm.random_data import create_users, wipe_users

TEST_SIZE = 10
collections = ["user"]


@pytest.fixture(scope="module")
def datastore(datastore_connection):
    ds = datastore_connection
    try:
        u = ds.user.get("user")
        for x in range(TEST_SIZE - 2):
            u.name = f"TEST_{x}"
            ds.user.save(u.name, u)
        ds.user.commit()
        yield ds
    finally:
        wipe_users(ds)
        create_users(ds)


# noinspection PyUnusedLocal
def test_deep_search(datastore, login_session):
    session, host = login_session

    params = {"query": "id:*", "rows": 5}
    for collection in collections:
        params["deep_paging_id"] = "*"
        res = []
        while True:
            resp = get_api_data(
                session, f"{host}/api/v1/search/{collection}/", params=params
            )
            res.extend(resp["items"])
            if len(resp["items"]) == 0 or "next_deep_paging_id" not in resp:
                break
            params["deep_paging_id"] = resp["next_deep_paging_id"]
        assert len(res) >= TEST_SIZE


# noinspection PyUnusedLocal
def test_facet_search(datastore, login_session):
    session, host = login_session

    for collection in collections:
        resp = get_api_data(session, f"{host}/api/v1/search/facet/{collection}/name/")
        assert len(resp) == TEST_SIZE
        for v in resp.values():
            assert isinstance(v, int)


# noinspection PyUnusedLocal
def test_grouped_search(datastore, login_session):
    session, host = login_session

    for collection in collections:
        resp = get_api_data(session, f"{host}/api/v1/search/grouped/{collection}/name/")
        assert resp["total"] >= TEST_SIZE
        for v in resp["items"]:
            assert v["total"] == 1 and "value" in v


# noinspection PyUnusedLocal
def test_histogram_search(datastore, login_session):
    session, host = login_session

    # TODO: Data histogram can't be tested until we have an index witha date
    date_hist_map = {}

    for collection in collections:
        hist_field = date_hist_map.get(collection, None)
        if not hist_field:
            continue

        resp = get_api_data(
            session, f"{host}/api/v1/search/histogram/{collection}/{hist_field}/"
        )
        for k, v in resp.items():
            assert k.startswith("2") and k.endswith("Z") and isinstance(v, int)

    int_hist_map = {"user": "api_quota"}

    for collection in collections:
        hist_field = int_hist_map.get(collection, "archive_ts")
        if not hist_field:
            continue

        resp = get_api_data(
            session, f"{host}/api/v1/search/histogram/{collection}/{hist_field}/"
        )
        for k, v in resp.items():
            assert isinstance(int(k), int) and isinstance(v, int)


# noinspection PyUnusedLocal
def test_get_fields(datastore, login_session):
    session, host = login_session

    for collection in collections:
        resp = get_api_data(session, f"{host}/api/v1/search/fields/{collection}/")
        for v in resp.values():
            assert sorted(list(v.keys())) == sorted(
                [
                    "default",
                    "indexed",
                    "list",
                    "stored",
                    "type",
                    "description",
                    "deprecated",
                    "deprecated_description",
                ]
            )


# noinspection PyUnusedLocal
def test_search(datastore, login_session):
    session, host = login_session

    for collection in collections:
        resp = get_api_data(
            session, f"{host}/api/v1/search/{collection}/", params={"query": "id:*"}
        )
        assert TEST_SIZE <= resp["total"] >= len(resp["items"])


# noinspection PyUnusedLocal
def test_stats_search(datastore, login_session):
    session, host = login_session

    int_map = {"user": "api_quota"}

    for collection in collections:
        field = int_map.get(collection, False)
        if not field:
            continue

        resp = get_api_data(
            session, f"{host}/api/v1/search/stats/{collection}/{field}/"
        )
        assert sorted(list(resp.keys())) == ["avg", "count", "max", "min", "sum"]
        for v in resp.values():
            assert isinstance(v, int) or isinstance(v, float)
