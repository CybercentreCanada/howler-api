from flask import request

from howler.api import (
    bad_request,
    conflict,
    created,
    forbidden,
    make_subapi_blueprint,
    no_content,
    not_found,
    ok,
)
from howler.common.exceptions import HowlerException
from howler.common.loader import datastore
from howler.common.logging import get_logger
from howler.datastore.operations import OdmHelper
from howler.odm.models.template import Template
from howler.odm.models.user import User
from howler.security import api_login

SUB_API = "template"
template_api = make_subapi_blueprint(SUB_API, api_version=1)
template_api._doc = "Manage the different templates created for viewing hits"

logger = get_logger(__file__)

template_helper = OdmHelper(Template)


@template_api.route("/", methods=["GET"])
@api_login(required_priv=["R"])
def get_templates(**kwargs):
    """
    Get a list of templates the user can use to render hits

    Variables:
    None

    Optional Arguments:
    None

    Result Example:
    [
        ...templates    # A list of templates the user can use
    ]
    """

    try:
        return ok(
            datastore().template.search(
                f"type:global OR owner:{kwargs['user']['uname']}",
                as_obj=False,
                rows=10000,
            )["items"]
        )
    except ValueError as e:
        return bad_request(err=str(e))


@template_api.route("/", methods=["POST"])
@api_login(required_priv=["R", "W"])
def create_template(**kwargs):
    """
    Create a new template

    Variables:
    None

    Optional Arguments:
    None

    Data Block:
    {
        "analytic": "analytic name"             # The analytic this template applies to
        "detection": "detection name"           # The detection this template applies to
        "type": "global"                        # The type of template to create
        "keys": ["howler.id", "howler.hash"]    # The keys to show when this template matches a hit
    }

    Result Example:
    {
        ...template            # The new template data
    }
    """

    template_data = request.json
    if not isinstance(template_data, dict):
        return bad_request(err="Invalid data format")

    if "keys" not in template_data:
        return bad_request(
            err="You must specify a list of keys when creating a template!"
        )

    storage = datastore()

    try:
        template = Template(template_data)

        if template.type == "personal":
            template.owner = kwargs["user"]["uname"]
        else:
            template.owner = None

        query_str = f"analytic:{template.analytic} AND type:{template.type}"

        if template.type == "personal":
            query_str += f" AND owner:{template.owner}"

        if template.detection:
            query_str += f" AND detection:{template.detection}"
        else:
            query_str += " AND -_exists_:detection"

        if storage.template.search(query_str)["total"] > 0:
            return conflict(err="A template covering this case already exists.")

        storage.template.save(template.template_id, template)
        return created(template.as_primitives())
    except HowlerException as e:
        return bad_request(err=str(e))


@template_api.route("/<id>", methods=["DELETE"])
@api_login(required_priv=["W"])
def delete_template(id, user: User, **kwargs):
    """
    Delete a template

    Variables:
    id => The id of the template to delete

    Optional Arguments:
    None

    Data Block:
    None

    Result Example:
    {
        "success": true     # Did the deletion succeed?
    }
    """

    storage = datastore()

    if not storage.template.exists(id):
        return not_found(err="This template does not exist")

    existing_template: Template = storage.template.get_if_exists(id)

    if existing_template.type == "personal" and existing_template.owner != user.uname:
        return forbidden(
            err="You cannot delete a personal template that is not owned by you."
        )

    if existing_template.type == "global" and "admin" not in user.type:
        return forbidden(
            err="You cannot delete a global template unless you are an administrator."
        )

    return no_content({"success": storage.template.delete(id)})


@template_api.route("/<id>", methods=["PUT"])
@api_login(required_priv=["R", "W"])
def update_template_fields(id, user: User, **kwargs):
    """
    Update a template's keys

    Variables:
    id => The id of the template to modify

    Optional Arguments:
    None

    Data Block:
    [
        "howler.id",
        "howler.hash"
    ]

    Result Example:
    {
        ...template     # The updated template data
    }
    """

    storage = datastore()

    if not storage.template.exists(id):
        return not_found(err="This template does not exist")

    new_fields = request.json
    if not isinstance(new_fields, list) or not all(
        isinstance(f, str) for f in new_fields
    ):
        return bad_request(err="List of new fields must be a list of strings.")

    existing_template: Template = storage.template.get_if_exists(id)

    if existing_template.type == "personal" and existing_template.owner != user.uname:
        return forbidden(
            err="You cannot update a personal template that is not owned by you."
        )

    fields_to_add = set(new_fields) - set(existing_template.keys)
    fields_to_remove = set(existing_template.keys) - set(new_fields)

    logger.debug("Adding %s to template %s", fields_to_add, id)
    logger.debug("Removing %s from template %s", fields_to_remove, id)

    storage.template.update(
        existing_template.template_id,
        [
            *[template_helper.list_remove("keys", f) for f in fields_to_remove],
            *[template_helper.list_add("keys", f) for f in fields_to_add],
        ],
        version=False,
    )

    try:
        return ok(
            storage.template.get_if_exists(existing_template.template_id, as_obj=False)
        )
    except HowlerException as e:
        return bad_request(err=str(e))
