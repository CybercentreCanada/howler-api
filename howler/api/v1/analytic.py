from typing import Any, Optional

from flask import request

from howler.api import (
    bad_request,
    forbidden,
    make_subapi_blueprint,
    no_content,
    not_found,
    ok,
)
from howler.common.exceptions import HowlerException
from howler.common.loader import datastore
from howler.common.logging import get_logger
from howler.datastore.exceptions import DataStoreException
from howler.datastore.operations import OdmHelper
from howler.odm.models.analytic import Analytic, Comment, Notebook
from howler.odm.models.user import User
from howler.security import api_login
from howler.services import analytic_service

MAX_COMMENT_LEN = 5000
SUB_API = "analytic"
analytic_api = make_subapi_blueprint(SUB_API, api_version=1)
analytic_api._doc = "Manage the analytics that create hits"

logger = get_logger(__file__)

analytic_helper = OdmHelper(Analytic)


@analytic_api.route("/", methods=["GET"])
@api_login(required_priv=["R"])
def get_analytics(**kwargs):
    """
    Get a list of analytics used to create hits in howler

    Variables:
    None

    Optional Arguments:
    None

    Result Example:
    [
        ...analytics    # A list of analytics
    ]
    """

    return ok(datastore().analytic.search("*:*", as_obj=False)["items"])


@analytic_api.route("/<id>", methods=["GET"])
@api_login(required_priv=["R"])
def get_analytic(id, **kwargs):
    """
    Get a specific analytic

    Variables:
    id => The id of the analytic to retrieve

    Optional Arguments:
    None

    Result Example:
    {
        ...analytic     # The requested analytic
    }
    """

    try:
        if not analytic_service.does_analytic_exist(id):
            return not_found(err="Analytic does not exist")

        return ok(analytic_service.get_analytic(id, as_obj=False))
    except ValueError as e:
        return bad_request(err=str(e))


@analytic_api.route("/<id>", methods=["PUT"])
@api_login(required_priv=["R", "W"])
def update_analytic(id, user: User, **kwargs):
    """
    Update an analytic

    Variables:
    id => The id of the analytic to modify

    Optional Arguments:
    None

    Data Block:
    {
        ...analytic     # The new data to add
    }

    Result Example:
    {
        ...analytic     # The updated analytic data
    }
    """

    storage = datastore()

    if not storage.analytic.exists(id):
        return not_found(err="This analytic does not exist")

    new_data = request.json

    if not new_data:
        return bad_request(err="You must provide updated data.")

    try:
        existing_analytic: Analytic = storage.analytic.get_if_exists(id)

        existing_analytic.description = new_data.get(
            "description", existing_analytic.description
        )

        storage.analytic.save(existing_analytic.analytic_id, existing_analytic)

        return ok(existing_analytic.as_primitives())
    except HowlerException as e:
        return bad_request(err=str(e))


@analytic_api.route("/<id>/comments", methods=["POST"])
@api_login(audit=False, required_priv=["W"])
def add_comment(id, user: dict[str, Any], **kwargs):
    """
    Add a comment

    Variables:
    id  => id of the analytic to add a comment to

    Optional Arguments:
    None

    Data Block:
    {
        detection: "Detection to comment on (optional)",
        value: "New comment value"
    }

    Result Example:
    {
        ...analytic            # The new data for the analytic
    }
    """
    comment = request.json
    if not isinstance(comment, dict):
        return bad_request(err="Incorrect data format!")

    comment_data = comment.get("value")
    if not comment_data:
        return bad_request(err="Value cannot be empty.")

    if len(comment_data) > MAX_COMMENT_LEN:
        return bad_request(err="Comment is too long.")

    if not analytic_service.does_analytic_exist(id):
        return not_found(err="Analytic %s does not exist" % id)

    analytic: Analytic = analytic_service.get_analytic(id, as_obj=True)

    try:
        analytic.comment.append(
            Comment(
                {
                    "user": user["uname"],
                    "value": comment_data,
                    "detection": comment.get("detection", None),
                }
            )
        )

        datastore().analytic.save(analytic.analytic_id, analytic)
    except DataStoreException as e:
        return bad_request(err=str(e))

    analytic = analytic_service.get_analytic(id)

    return ok(analytic)


@analytic_api.route("/<id>/comments/<comment_id>", methods=["PUT"])
@api_login(audit=False, required_priv=["W"])
def edit_comment(id, comment_id: str, user: dict[str, Any], **kwargs):
    """
    Edit a comment

    Variables:
    id          => id of the analytic the comment belongs to
    comment_id  => id of the comment we are editing

    Optional Arguments:
    None

    Data Block:
    {
        value: "New comment value"
    }

    Result Example:
    {
        ...analytic            # The new data for the analytic
    }
    """
    updated_comment = request.json
    if not isinstance(updated_comment, dict):
        return bad_request(err="Incorrect data format")

    if not analytic_service.does_analytic_exist(id):
        return not_found(err=f"Analytic {id} does not exist")

    comment_data: Optional[str] = updated_comment.get("value")
    if not comment_data:
        return bad_request(err="Value cannot be empty.")

    if len(comment_data) > MAX_COMMENT_LEN:
        return bad_request(err="Comment is too long.")

    analytic: Analytic = analytic_service.get_analytic(id, as_obj=True)

    comment: Optional[Comment] = next(
        (c for c in analytic.comment if c.id == comment_id), None
    )

    if not comment:
        return not_found(err=f"Comment {comment_id} does not exist")

    if comment.user != user["uname"]:
        return forbidden(err="Cannot edit comment that wasn't made by you.")

    comment["value"] = comment_data
    comment["modified"] = "NOW"

    analytic.comment = [c if c.id != comment.id else comment for c in analytic.comment]

    try:
        datastore().analytic.save(analytic.analytic_id, analytic)
    except DataStoreException as e:
        return bad_request(err=str(e))

    return ok(analytic.as_primitives())


@analytic_api.route("/<id>/comments/<comment_id>/react", methods=["PUT"])
@api_login(audit=False, required_priv=["W"])
def react_comment(id, comment_id: str, user: dict[str, Any], **kwargs):
    """
    React to a comment

    Variables:
    id          => id of the analytic the comment belongs to
    comment_id  => id of the comment we are editing

    Optional Arguments:
    None

    Data Block:
    {
        type: "thumbsup"
    }

    Result Example:
    {
        ...analytic            # The new data for the analytic
    }
    """

    data = request.json
    if not isinstance(data, dict):
        return bad_request(err="Incorrect data format")

    react_data: Optional[str] = data.get("type")
    if not react_data:
        return bad_request(err="Type cannot be empty.")

    if not analytic_service.does_analytic_exist(id):
        return not_found(err=f"Analytic {id} does not exist")

    analytic: Analytic = analytic_service.get_analytic(id, as_obj=True)

    for comment in analytic.comment:
        if comment.id == comment_id:
            comment["reactions"] = {
                **comment.get("reactions", {}),
                user["uname"]: react_data,
            }

    datastore().analytic.save(analytic.analytic_id, analytic)

    return ok(analytic.as_primitives())


@analytic_api.route("/<id>/comments/<comment_id>/react", methods=["DELETE"])
@api_login(audit=False, required_priv=["W"])
def remove_react_comment(id, comment_id: str, user: dict[str, Any], **kwargs):
    """
    React to a comment

    Variables:
    id          => id of the analytic the comment belongs to
    comment_id  => id of the comment we are editing

    Optional Arguments:
    None

    Result Example:
    {
        ...analytic            # The new data for the analytic
    }
    """
    if not analytic_service.does_analytic_exist(id):
        return not_found(err=f"Analytic {id} does not exist")

    analytic: Analytic = analytic_service.get_analytic(id, as_obj=True)

    for comment in analytic.comment:
        if comment.id == comment_id:
            reactions = comment.get("reactions", {})
            reactions.pop(user["uname"], None)
            comment["reactions"] = {**reactions}

    datastore().analytic.save(analytic.analytic_id, analytic)

    return ok(analytic.as_primitives())


@analytic_api.route("/<id>/comments", methods=["DELETE"])
@api_login(audit=False, required_priv=["W"])
def delete_comments(id, user: User, **kwargs):
    """
    Delete a set of comments

    Variables:
    id  => id of the analytic whose comments we are deleting

    Optional Arguments:
    None

    Data Block:
    [
        ...comment_ids
    ]

    Result Example:
    {
    }
    """

    if not analytic_service.does_analytic_exist(id):
        return not_found(err=f"Analytic {id} does not exist")

    comment_ids: list[str] = request.json or []

    if len(comment_ids) == 0:
        return bad_request(err="Supply at least one comment to delete.")

    analytic: Analytic = analytic_service.get_analytic(id, as_obj=True)

    new_comments = []
    for comment in analytic.comment:
        if comment.id in comment_ids:
            if ("admin" not in user["type"]) and comment.user != user["uname"]:
                return forbidden(err="You cannot delete the comment of someone else.")

            continue

        new_comments.append(comment)

    analytic.comment = new_comments

    try:
        datastore().analytic.save(analytic.analytic_id, analytic)
    except DataStoreException as e:
        return bad_request(err=str(e))

    return no_content()


@analytic_api.route("/<id>/notebooks", methods=["POST"])
@api_login(audit=False, required_priv=["W"])
def add_notebook(id, user: dict[str, Any], **kwargs):
    """
    Add a notebook

    Variables:
    id  => id of the analytic to add a notebook to

    Optional Arguments:
    None

    Data Block:
    {
        value: "New notebook link",
        name: "New notebook name",
        detection: "Detection to add a notebook about (optional)",
    }

    Result Example:
    {
        ...analytic            # The new data for the analytic
    }
    """
    data = request.json
    if not isinstance(data, dict):
        return bad_request(err="Incorrect data format")

    link = data.get("value")
    name = data.get("name")
    detection = data.get("detection", None)

    if not link or not name:
        return bad_request(err="Value/Name cannot be empty.")

    if "nbgallery." not in link:
        return bad_request(err="Only nbgallery is supported for now.")

    if not analytic_service.does_analytic_exist(id):
        return not_found(err="Analytic %s does not exist" % id)

    analytic: Analytic = analytic_service.get_analytic(id, as_obj=True)

    try:
        analytic.notebooks.append(
            Notebook(
                {
                    "user": user["uname"],
                    "name": name,
                    "value": link,
                    "detection": detection if detection else None,
                }
            )
        )

        datastore().analytic.save(analytic.analytic_id, analytic)
    except DataStoreException as e:
        return bad_request(err=str(e))

    analytic = analytic_service.get_analytic(id)

    return ok(analytic)


@analytic_api.route("/<id>/notebooks", methods=["DELETE"])
@api_login(audit=False, required_priv=["W"])
def delete_notebook(id, user: User, **kwargs):
    """
    Delete a notebook

    Variables:
    id  => id of the analytic whose notebook we are deleting

    Optional Arguments:
    None

    Data Block:
    [
        notebook_id
    ]

    Result Example:
    {
    }
    """

    if not analytic_service.does_analytic_exist(id):
        return not_found(err=f"Analytic {id} does not exist")

    notebook_ids: list[str] = request.json or []

    if len(notebook_ids) == 0:
        return bad_request(err="A notebook id is necessary for deletion.")

    analytic: Analytic = analytic_service.get_analytic(id, as_obj=True)

    new_notebooks = []
    for notebook in analytic.notebooks:
        if notebook.id in notebook_ids:
            if ("admin" not in user["type"]) and notebook.user != user["uname"]:
                return forbidden(err="You cannot delete the notebook of someone else.")

            continue

        new_notebooks.append(notebook)

    analytic.notebooks = new_notebooks

    try:
        datastore().analytic.save(analytic.analytic_id, analytic)
    except DataStoreException as e:
        return bad_request(err=str(e))

    return no_content()
