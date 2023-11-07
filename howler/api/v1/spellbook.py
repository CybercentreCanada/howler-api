from flask import request
from howler.api import (
    bad_gateway,
    bad_request,
    make_subapi_blueprint,
    ok,
)
from howler.common.exceptions import HowlerAttributeError, HowlerRuntimeError
from howler.common.logging import get_logger
from howler.security import api_login

from hogwarts.spellbook.exceptions import SpellbookError

from howler.utils.spellbook import get_spellbook_client, get_spellbook_token

SUB_API = "spellbook"
spellbook_api = make_subapi_blueprint(SUB_API, api_version=1)
spellbook_api._doc = "Interact with spellbook"

logger = get_logger(__file__)


@spellbook_api.route("/", methods=["GET"])
@api_login(required_priv=["R"], required_method=["oauth"])
def get_jobs(**kwargs):
    """
    Get a list of jobs tagged with 'action' in spellbook

    Variables:
    None

    Optional Arguments:
    None

    Result Example:
    [
        ...jobs     # A list of jobs the user can use
    ]
    """

    try:
        spellbook = get_spellbook_client(kwargs["user"]["uname"])
    except (HowlerRuntimeError, HowlerAttributeError) as e:
        return bad_request(err=e.message)
    except SpellbookError:
        return bad_gateway(err="There was an error when communicating with spellbook.")

    # TODO: 404 errors with spellbook client act very funny
    # print(spellbook.jobs.get("spellbook_example_ingestor"))
    spellbook_response = spellbook.search.jobs(
        filters=[{"column": "tag_name", "operator": "like", "value": "action"}],
        limit=100,
    )

    if spellbook_response["reason"] == "OK":
        return ok(spellbook_response["data"]["items"])
    else:
        return bad_request(
            spellbook_response,
            err=spellbook_response["errorMessage"] or spellbook_response["reason"],
        )


@spellbook_api.route("/<dag_id>/params", methods=["GET"])
@api_login(required_priv=["R"], required_method=["oauth"])
def get_params(dag_id, **kwargs):
    """
    Get a list of DAG parameters for a particular spellbook job

    Variables:
    dag_id  => id of the dag to get the parameters of

    Optional Arguments:
    None

    Result Example:
    {
        "param1": {
            "value": "test",
            "schema": {
                "type": "string"
            }
        }
    }
    """

    try:
        spellbook_response = get_spellbook_client(kwargs["user"]["uname"]).jobs.params(
            dag_id
        )
    except (HowlerRuntimeError, HowlerAttributeError) as e:
        return bad_request(err=e.message)
    except SpellbookError:
        return bad_gateway(err="There was an error when communicating with spellbook.")

    if spellbook_response["reason"] == "OK":
        return ok(spellbook_response["data"])
    else:
        return bad_request(
            spellbook_response,
            err=spellbook_response["errorMessage"] or spellbook_response["reason"],
        )
