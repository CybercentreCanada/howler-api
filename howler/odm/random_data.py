import json
import os
import random
import sys
from datetime import datetime
from random import choice, randint, sample
import time
from typing import Callable

from howler.actions import OPERATIONS
from howler.common import loader
from howler.common.logging import get_logger
from howler.datastore.howler_store import HowlerDatastore
from howler.helper.oauth import VALID_CHARS
from howler.odm.base import Keyword
from howler.odm.helper import generate_useful_hit
from howler.odm.models.action import Action
from howler.odm.models.analytic import Analytic, Comment, Notebook
from howler.odm.models.hit import Hit
from howler.odm.models.howler_data import Assessment, HitStatusTransition
from howler.odm.models.template import Template
from howler.odm.models.user import User
from howler.odm.models.view import View
from howler.odm.randomizer import get_random_user, get_random_word, random_model_obj
from howler.security.utils import get_password_hash
from howler.services import analytic_service, hit_service

classification = loader.get_classification()

logger = get_logger(__file__)


def create_users(ds):
    admin_pass = os.getenv("DEV_ADMIN_PASS", "admin") or "admin"
    user_pass = os.getenv("DEV_USER_PASS", "user") or "user"
    shawnh_pass = "shawn-h"

    admin_hash = get_password_hash(admin_pass)

    admin_view = View(
        {
            "title": "view.assigned_to_me",
            "query": "howler.assignment:admin",
            "type": "readonly",
            "owner": "admin",
        }
    )
    user_data = User(
        {
            "apikeys": {
                "devkey": {"acl": ["R", "W", "E"], "password": admin_hash},
                "readonly": {"acl": ["R"], "password": admin_hash},
                "readonly1": {"acl": ["R"], "password": admin_hash},
                "impersonate": {"acl": ["R", "I"], "password": admin_hash},
                "readonly2": {"acl": ["R"], "password": admin_hash},
                "readonly3": {"acl": ["R"], "password": admin_hash},
                "write1": {"acl": ["W"], "password": admin_hash},
                "write2": {"acl": ["W"], "password": admin_hash},
                "both": {"acl": ["R", "W"], "password": admin_hash},
                "read_extended": {"acl": ["R", "E"], "password": admin_hash},
                "write_extended": {"acl": ["W", "E"], "password": admin_hash},
                "expired": {
                    "acl": ["R", "W", "E"],
                    "password": admin_hash,
                    "expiry_date": "2023-05-30T05:12:28.566Z",
                },
                "not_expired": {
                    "acl": ["R", "W", "E"],
                    "password": admin_hash,
                    "expiry_date": datetime.now().replace(year=3000).isoformat(),
                },
            },
            "classification": classification.RESTRICTED,
            "name": "Michael Scott",
            "email": "admin@howler.cyber.gc.ca",
            "password": admin_hash,
            "uname": "admin",
            "type": ["admin", "user", "automation_basic", "automation_advanced"],
            "groups": [
                "USERS",
                "DASI2B",
                "APA2B",
                "DASI2",
                "APA2",
                "APA",
                "CDC",
                "CCCS",
                "Analytical_Platform_Users",
            ],
            "favourite_views": [admin_view.view_id],
        }
    )
    ds.user.save("admin", user_data)
    ds.user_avatar.save(
        "admin",
        "https://static.wikia.nocookie.net/theoffice/images/b/be/Character_-_MichaelScott.PNG",
    )
    ds.view.save(admin_view.view_id, admin_view)

    if "pytest" not in sys.modules:
        logger.info(f"\t{user_data.uname}:{admin_pass}")

    user_hash = get_password_hash(user_pass)

    user_view = View(
        {
            "title": "view.assigned_to_me",
            "query": "howler.assignment:user",
            "type": "readonly",
            "owner": "user",
        }
    )

    user_data = User(
        {
            "name": "Dwight Schrute",
            "email": "user@howler.cyber.gc.ca",
            "apikeys": {
                "devkey": {"acl": ["R", "W"], "password": user_hash},
                "impersonate_admin": {
                    "acl": ["R", "W", "I"],
                    "agents": ["admin", "goose"],
                    "password": user_hash,
                },
                "impersonate_potato": {
                    "acl": ["R", "W", "I"],
                    "agents": ["potato"],
                    "password": user_hash,
                },
            },
            "password": user_hash,
            "uname": "user",
            "favourite_views": [user_view.view_id],
        }
    )
    ds.user.save("user", user_data)
    ds.user_avatar.save(
        "user",
        "https://static.wikia.nocookie.net/theoffice/images/c/c5/Dwight_.jpg",
    )
    ds.view.save(user_view.view_id, user_view)

    if "pytest" not in sys.modules:
        logger.info(f"\t{user_data.uname}:{user_pass}")

    shawnh_view = View(
        {
            "title": "view.assigned_to_me",
            "query": "howler.assignment:shawnh",
            "type": "readonly",
            "owner": "shawn-h",
        }
    )
    shawn_data = User(
        {
            "name": "Shawn Hannigans",
            "email": "shawn.hannigans@howler.com",
            "apikeys": {},
            "type": ["admin", "user"],
            "groups": ["group1", "group2"],
            "password": get_password_hash(shawnh_pass),
            "uname": "shawn-h",
            "favourite_views": [shawnh_view.view_id],
        }
    )

    shawn_data.favourite_views.append(shawnh_view.view_id)
    ds.user.save("shawn-h", shawn_data)
    ds.view.save(shawnh_view.view_id, shawnh_view)

    if "pytest" not in sys.modules:
        logger.info(f"\t{shawn_data.uname}:{shawnh_pass}")

    ds.user.commit()
    ds.user_avatar.commit()
    ds.view.commit()


def wipe_users(ds):
    ds.user.wipe()
    ds.user_avatar.wipe()


def create_templates(ds: HowlerDatastore):
    for _ in range(30):
        keys = sample(list(Hit.flat_fields().keys()), 5)

        for detection in ["Detection 1", "Detection 2", None]:
            template = Template(
                {
                    "analytic": choice(["COLISEUM", "HERETIC", "SecretAnalytic"]),
                    "detection": detection,
                    "type": "global",
                    "keys": keys,
                }
            )

            ds.template.save(
                template.template_id,
                template,
            )

    for analytic in ["COLISEUM", "HERETIC"]:
        template = Template(
            {
                "analytic": analytic,
                "type": "global",
                "keys": ["howler.id", "howler.hash"],
            }
        )

        ds.template.save(
            template.template_id,
            template,
        )

        template = Template(
            {
                "analytic": analytic,
                "owner": "admin",
                "type": "personal",
                "keys": ["howler.id", "howler.hash", "howler.analytic", "agent.id"],
            }
        )

        ds.template.save(
            template.template_id,
            template,
        )

        template = Template(
            {
                "analytic": analytic,
                "owner": "goose",
                "type": "personal",
                "keys": ["agent.id", "agent.type", "container.id"],
            }
        )

        ds.template.save(
            template.template_id,
            template,
        )

    ds.template.commit()


def wipe_templates(ds):
    ds.template.wipe()


def create_views(ds: HowlerDatastore):
    view = View(
        {
            "title": "CMT Hits",
            "query": "howler.analytic:cmt.*",
            "type": "global",
            "owner": "admin",
        }
    )

    ds.view.save(
        view.view_id,
        view,
    )

    view = View(
        {
            "title": "Howler Bundles",
            "query": "howler.is_bundle:true",
            "type": "readonly",
            "owner": "none",
        }
    )

    ds.view.save(
        view.view_id,
        view,
    )

    fields = Hit.flat_fields()
    key_list = [key for key in fields.keys() if type(fields[key]) == Keyword]
    for _ in range(10):
        query = f"{choice(key_list)}:*{choice(VALID_CHARS)}* OR {choice(key_list)}:*{choice(VALID_CHARS)}*"
        view = View(
            {
                "title": get_random_word(),
                "query": query,
                "type": "global",
                "owner": get_random_user(),
            }
        )

        ds.view.save(
            view.view_id,
            view,
        )

    ds.view.commit()


def wipe_views(ds):
    ds.view.wipe()


def create_hits(ds: HowlerDatastore, log=None, hit_count=200):
    lookups = loader.get_lookups()
    users = ds.user.search("*:*")["items"]
    for hit_idx in range(hit_count):
        hit = generate_useful_hit(lookups, [user["uname"] for user in users])

        if hit_idx + 1 == hit_count:
            hit.howler.analytic = "SecretAnalytic"
            hit.howler.detection = None

        ds.hit.save(hit.howler.id, hit)
        analytic_service.save_from_hit(hit)
        ds.analytic.commit()

        if choice([True, False, False]):
            user = choice(users)
            hit_service.transition_hit(
                hit.howler.id,
                HitStatusTransition.ASSESS,
                user,
                None,
                hit=hit,
                assessment=choice(Assessment.list()),
            )
        if hit_idx % 25 == 0 and "pytest" not in sys.modules:
            logger.info("\tCreated %s/%s", hit_idx, hit_count)

    if "pytest" not in sys.modules:
        logger.info("\tCreated %s/%s", hit_idx + 1, hit_count)


def create_bundles(ds: HowlerDatastore):
    lookups = loader.get_lookups()
    users = [user.uname for user in ds.user.search("*:*")["items"]]

    hits = {}

    for i in range(3):
        bundle_hit: Hit = generate_useful_hit(lookups, users)
        bundle_hit.howler.is_bundle = True

        for hit in ds.hit.search(
            "howler.is_bundle:false", rows=randint(3, 10), offset=(i * 2)
        )["items"]:
            if hit.howler.id not in hits:
                hits[hit.howler.id] = hit

            bundle_hit.howler.hits.append(hit.howler.id)
            hits[hit.howler.id].howler.bundles.append(bundle_hit.howler.id)

        analytic_service.save_from_hit(bundle_hit)
        ds.hit.save(bundle_hit.howler.id, bundle_hit)

    for hit in hits.values():
        ds.hit.save(hit.howler.id, hit)

    ds.hit.commit()


def wipe_hits(ds):
    ds.hit.wipe()


def create_analytics(ds: HowlerDatastore, num_analytics=30):
    users = [user.uname for user in ds.user.search("*:*")["items"]]

    for analytic in ds.analytic.search("*:*")["items"]:
        for detection in analytic.detections:
            analytic.comment.append(
                Comment(
                    {
                        "value": f"Placeholder Comment - {detection}",
                        "user": random.choice(users),
                        "detection": detection,
                    }
                )
            )

        analytic.comment.append(
            Comment(
                {
                    "value": "Placeholder Comment - Analytic",
                    "user": random.choice(users),
                }
            )
        )

        analytic.notebooks.append(
            Notebook(
                {
                    "value": "Link to super notebook",
                    "name": "Super notebook",
                    "user": random.choice(users),
                }
            )
        )

        ds.analytic.save(analytic.analytic_id, analytic)

    for _ in range(num_analytics):
        a = random_model_obj(Analytic)
        ds.analytic.save(a.analytic_id, a)

    ds.analytic.commit()
    ds.hit.commit()


def wipe_analytics(ds):
    ds.analytic.wipe()


def create_actions(ds: HowlerDatastore, num_actions=30):
    fields = Hit.flat_fields()
    key_list = [key for key in fields.keys() if type(fields[key]) == Keyword]
    users = ds.user.search("*:*")["items"]

    operation_options = list(OPERATIONS.keys())
    if "transition" in operation_options:
        operation_options.remove("transition")
    if "spellbook" in operation_options:
        operation_options.remove("spellbook")

    for _ in range(num_actions):
        operations = []
        operation_ids = sample(operation_options, k=randint(1, len(operation_options)))
        for operation_id in operation_ids:
            action_data = {}

            for step in OPERATIONS[operation_id].specification()["steps"]:
                for key in step["args"].keys():
                    potential_values = step["options"].get(key, None)
                    if potential_values:
                        if isinstance(potential_values, dict):
                            action_data[key] = choice(
                                potential_values[choice(list(potential_values.keys()))]
                            )
                        else:
                            action_data[key] = choice(potential_values)
                    else:
                        action_data[key] = get_random_word()

            if operation_id == "prioritization":
                action_data["value"] = float(random.randint(0, 10000)) / 10

            operations.append(
                {"operation_id": operation_id, "data_json": json.dumps((action_data))}
            )

        action = Action(
            {
                "name": get_random_word(),
                "owner_id": choice([user["uname"] for user in users]),
                "query": f"{choice(key_list)}:*{choice(VALID_CHARS)}* OR {choice(key_list)}:*{choice(VALID_CHARS)}*",
                "operations": operations,
            }
        )

        ds.action.save(action.action_id, action)

    ds.action.commit()


def wipe_actions(ds: HowlerDatastore):
    ds.action.wipe()


def setup_hits(ds):
    os.environ["ELASTIC_HIT_SHARDS"] = "12"
    os.environ["ELASTIC_HIT_REPLICAS"] = "1"
    ds.hit.fix_shards()
    ds.hit.fix_replicas()


def setup_users(ds):
    os.environ["ELASTIC_USER_REPLICAS"] = "1"
    os.environ["ELASTIC_USER_AVATAR_REPLICAS"] = "1"
    ds.user.fix_replicas()
    ds.user_avatar.fix_replicas()


INDEXES: dict[str, tuple[Callable, list[Callable]]] = {
    "users": (wipe_users, [create_users]),
    "templates": (wipe_templates, [create_templates]),
    "views": (wipe_views, [create_views]),
    "hits": (wipe_hits, [create_hits, create_bundles]),
    "analytics": (wipe_analytics, [create_analytics]),
    "actions": (wipe_actions, [create_actions]),
}


if __name__ == "__main__":
    args = [*sys.argv]

    # Remove the file path
    args.pop(0)

    if "all" in args or len(args) < 1:
        logger.info("Adding test data to all indexes.")
        args = list(INDEXES.keys())
    else:
        logger.info("Adding test data to indexes: (%s).", ", ".join(args))

    ds = loader.datastore(archive_access=False)

    logger.info("Wiping existing data.")

    for index, operations in INDEXES.items():
        if index in args:
            # Wipe function
            operations[0](ds)

    logger.info("Running setup steps.")
    if "hits" in args:
        setup_hits(ds)

    if "users" in args:
        setup_users(ds)

    for index, operations in INDEXES.items():
        if index in args:
            logger.info(f"Creating {index}...")

            # Create functions
            for create_fn in operations[1]:
                create_fn(ds)

    logger.info("Done.")
