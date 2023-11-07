from flask import request

from howler.api import internal_error, make_subapi_blueprint, ok, unauthorized
from howler.security import api_login
from howler.services.notebook_service import get_nb_information, get_user_envs

SUB_API = "notebook"
notebook_api = make_subapi_blueprint(SUB_API, api_version=1)
notebook_api._doc = "Get notebook information"


@notebook_api.route("/environments", methods=["GET"])
@api_login(required_priv=["R"], required_method=["oauth"])
def get_user_environments(**kwargs):
    """
    Get user's jupyter hub environments

    Variables:
    None

    Arguments:

    Result Example:
    {
        [
            Env1,
            Env2
        ]
    }
    """

    try:
        env = get_user_envs()
    except Exception:
        return internal_error(
            err="Failed to retrieve user's environments from nbgallery."
        )

    return ok({"envs": env})


@notebook_api.route("/notebook", methods=["POST"])
@api_login(required_priv=["R"], required_method=["oauth"])
def get_notebook(**kwargs):
    """
    Return patched notebook

    Variables:
    None

    Arguments:


    Data Block:
    {
        link: "https://nbgallery...",
        analytic: Analytic object,
        hit: Hit object
    }

    Result Example:
    {
        [
            Env1,
            Env2
        ]
    }
    """
    data = request.json
    link = data.get("link")
    analytic = data.get("analytic")
    hit = data.get("hit", None)

    try:
        json_content, name = get_nb_information(link, analytic, hit)
    except Exception as er:
        return internal_error(err=f"Failed to retrieve notebook from nbgallery. {er}")

    return ok({"nb_content": json_content, "name": name})
