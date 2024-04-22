import logging
import os.path
from typing import Any

from authlib.integrations.flask_client import OAuth
from elasticapm.contrib.flask import ElasticAPM
from flask import Flask
from flask.logging import default_handler
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from howler.api.base import api
from howler.api.socket import socket_api
from howler.api.v1 import apiv1
from howler.api.v1.action import action_api
from howler.api.v1.analytic import analytic_api
from howler.api.v1.auth import auth_api
from howler.api.v1.configs import config_api
from howler.api.v1.help import help_api
from howler.api.v1.hit import hit_api
from howler.api.v1.search import search_api
from howler.api.v1.template import template_api
from howler.api.v1.tool import tool_api
from howler.api.v1.user import user_api
from howler.api.v1.view import view_api
from howler.common.logging import get_logger
from howler.config import (
    DEBUG,
    HWL_UNSECURED_UI,
    HWL_USE_JOB_SYSTEM,
    HWL_USE_REST_API,
    HWL_USE_WEBSOCKET_API,
    SECRET_KEY,
    cache,
    config,
)
from howler.error import errors
from howler.healthz import healthz

from howler.cronjobs import setup_jobs

logger = get_logger(__file__)

##########################
# App settings
current_directory = os.path.dirname(__file__)

app = Flask(
    "howler-api",
    static_url_path="/api/static",
    static_folder=config.ui.static_folder,
)
# Disable strict check on trailing slashes for endpoints
app.url_map.strict_slashes = False
app.config["JSON_SORT_KEYS"] = False

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/metrics": make_wsgi_app()})  # type: ignore[method-assign]

cache.init_app(app)

app.logger.setLevel(60)  # This completely turns off the flask logger
if HWL_UNSECURED_UI:
    app.config.update(SESSION_COOKIE_SECURE=False, SECRET_KEY=SECRET_KEY, PREFERRED_URL_SCHEME="http")
else:
    app.config.update(SESSION_COOKIE_SECURE=True, SECRET_KEY=SECRET_KEY, PREFERRED_URL_SCHEME="https")

app.register_blueprint(errors)
app.register_blueprint(healthz)

if HWL_USE_REST_API or DEBUG:
    logger.debug("Enabled REST API")
    app.register_blueprint(action_api)
    app.register_blueprint(analytic_api)
    app.register_blueprint(api)
    app.register_blueprint(apiv1)
    app.register_blueprint(auth_api)
    app.register_blueprint(config_api)
    app.register_blueprint(help_api)
    app.register_blueprint(hit_api)
    app.register_blueprint(search_api)
    app.register_blueprint(template_api)
    app.register_blueprint(tool_api)
    app.register_blueprint(user_api)
    app.register_blueprint(view_api)
else:
    logger.info("Disabled REST API")

if HWL_USE_WEBSOCKET_API or DEBUG:
    logger.debug("Enabled Websocket API")
    app.register_blueprint(socket_api)
else:
    logger.info("Disabled Websocket API")

if HWL_USE_JOB_SYSTEM or DEBUG:
    setup_jobs()


# Setup OAuth providers
if config.auth.oauth.enabled:
    providers = []
    for name, p in config.auth.oauth.providers.items():
        p: dict[str, Any] = p.as_primitives()

        # Set provider name
        p["name"] = name

        # Remove howler specific fields from oAuth config
        p.pop("auto_create", None)
        p.pop("auto_sync", None)
        p.pop("user_get", None)
        p.pop("auto_properties", None)
        p.pop("uid_regex", None)
        p.pop("uid_format", None)
        p.pop("user_groups", None)
        p.pop("user_groups_data_field", None)
        p.pop("user_groups_name_field", None)
        p.pop("app_provider", None)

        # Add the provider to the list of providers
        providers.append(p)

    if providers:
        oauth = OAuth()
        for p in providers:
            oauth.register(**p)
        oauth.init_app(app)

# Setup logging
app.logger.setLevel(logger.getEffectiveLevel())
app.logger.removeHandler(default_handler)
if logger.parent:
    for ph in logger.parent.handlers:
        app.logger.addHandler(ph)

# Setup APMs
if config.core.metrics.apm_server.server_url is not None:
    logger.info(f"Exporting application metrics to: {config.core.metrics.apm_server.server_url}")
    ElasticAPM(
        app,
        server_url=config.core.metrics.apm_server.server_url,
        service_name="howler_api",
    )

wlog = logging.getLogger("werkzeug")
wlog.setLevel(logging.WARNING)
if logger.parent:  # pragma: no cover
    for h in logger.parent.handlers:
        wlog.addHandler(h)


def main():
    app.jinja_env.cache = {}
    app.run(
        host="0.0.0.0",
        debug=DEBUG,
        port=int(os.getenv("FLASK_RUN_PORT", os.getenv("PORT", 5000))),
    )


if __name__ == "__main__":
    main()
