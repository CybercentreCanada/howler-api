from datetime import datetime, timedelta
import json
from math import ceil
import random
from hashlib import md5
from random import choice, sample
import sys

from howler.common.logging import get_logger
from howler.datastore.howler_store import HowlerDatastore
from howler.helper.discover import get_apps_list
from howler.odm.models.hit import Hit
from howler.odm.models.howler_data import Escalation, Link
from howler.odm.models.user import User
from howler.odm.randomizer import (
    get_random_filename,
    get_random_host,
    get_random_ip,
    get_random_user_agent,
    get_random_word,
    random_department,
    random_model_obj,
)
from howler.security.utils import get_password_hash
from howler.utils.uid import get_random_id


APPS = get_apps_list()
ESCALATIONS = Escalation.list()

logger = get_logger(__file__)


def generate_useful_hit(lookups, users, prune_hit=True):  # pragma: no cover
    hit: Hit = random_model_obj(Hit)

    rand_seed = random.random()

    timestamp = datetime.now() - timedelta(
        days=round(rand_seed * 30),
        hours=min(max(round(random.gauss(14, 3)), 0), 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )

    hit.event.created = timestamp.isoformat() + "Z"
    hit.event.provider = choice(["HBS", "NBS", "CBS", "AssemblyLine"])
    hit.timestamp = timestamp.isoformat() + "Z"

    hit.organization.name, hit.organization.id = random_department()
    hit.howler.outline.threat = get_random_ip()
    hit.howler.outline.target = get_random_host()
    hit.howler.outline.indicators = []
    for _ in range(round(rand_seed * 10)):
        hit.howler.outline.indicators.append(get_random_filename())

    hit.cloud.service.name = choice(
        [
            "Azure",
            "Amazon AWS",
            "Office365",
            "Google Drive",
            "Google Docs",
            "Microsoft Teams",
        ]
    )
    hit.aws.account.id = get_random_id()
    hit.aws.organization.id = get_random_id()
    hit.azure.subscription_id = get_random_id()
    hit.azure.tenant_id = get_random_id()
    hit.azure.resource_id = get_random_id()
    hit.gcp.project_id = get_random_id()
    hit.gcp.network_id = get_random_id()
    hit.gcp.service_account_id = get_random_id()
    hit.gcp.resource_id = get_random_id()
    hit.user.name = get_random_word()
    hit.user_agent.original = get_random_user_agent()
    hit.howler.analytic = choice(
        ["Password Checker", "Bad Guy Finder", "Exploit Patcher"]
    )
    hit.howler.detection = hit.threat.tactic.name

    for i in range(len(hit.howler.comment)):
        hit.howler.comment[i].user = choice(users)

    hit.howler.labels.assignments = sample(
        [
            "APA2B",
            "CCID1A",
            "ACE1C",
            "APA1B",
            "ADS4B",
            "ADS2A",
        ],
        1,
    )

    hit.howler.labels.generic = sample(
        [
            "Outlook",
            "Danger",
            "Drive",
            "Documentation",
            "Super Teams",
        ],
        ceil(rand_seed * 2),
    )

    hit.howler.labels.campaign = []
    hit.howler.labels.insight = []
    hit.howler.labels.victim = []
    hit.howler.labels.mitigation = []
    hit.howler.labels.operation = []
    hit.howler.labels.threat = []

    labelType = ceil(rand_seed * 6)
    if labelType == 1:
        hit.howler.labels.campaign = ["Bad event 2023-07"]
    elif labelType == 2:
        hit.howler.labels.insight = ["admin"]
    elif labelType == 3:
        hit.howler.labels.victim = ["Bobby's Ice-Cream"]
    elif labelType == 4:
        hit.howler.labels.mitigation = ["Blocked: google.com"]
    elif labelType == 5:
        hit.howler.labels.operation = ["OP_HOWLER"]
    else:
        hit.howler.labels.threat = ["Bad Mojo"]

    hit.event.id = hit.howler.id

    hit.howler.assessment = None
    hit.howler.rationale = None
    hit.howler.status = "open"
    hit.howler.assignment = "unassigned"
    hit.howler.escalation = choice([Escalation.HIT, Escalation.ALERT])

    hit.howler.outline.threat = choice(
        [
            hit.howler.outline.threat,
            hit.howler.outline.threat,
            hit.howler.outline.threat,
            f"{md5(hit.howler.outline.threat.encode()).hexdigest()}-thing.baduser.org",
        ]
    )

    hit.howler.outline.target = choice(
        [
            hit.howler.outline.target,
            hit.howler.outline.target,
            hit.howler.outline.target,
            f"{md5(hit.howler.outline.target.encode()).hexdigest()}.gc.ca",
        ]
    )

    hit.howler.data = [
        json.dumps(
            {
                "key": "value",
                "boolean": True,
                "number": 5,
                "float": 10.456,
                "array": ["a", "b", "c"],
            }
        ),
        json.dumps(
            {"key": "value1", "boolean": False, "number": 34, "float": 10678.098}
        ),
        "not json just a string",
        json.dumps(
            {
                "KQLQuery": (
                    "\n    let ioc_lookBack = 14d;\n    let deviceActionAllowed = datatable (action:string) [\n"
                    'NetworkIP\n    | parse kind=regex flags = U SourceZoneURI_CF with * "[\\\\s\\\\S-]+/" Department '
                    "summarize Summary=make_list(Source_Overview) by Indicator\n"
                ),
            }
        ),
    ]

    hit.howler.links = [
        Link(
            {
                "title": "Goose",
                "href": "https://en.wikipedia.org/wiki/Canada_goose",
                "icon": (
                    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/Canada_goose_on_Seedskadee_NWR"
                    "_%2827826185489%29.jpg/788px-Canada_goose_on_Seedskadee_NWR_%2827826185489%29.jpg"
                ),
            }
        )
    ]

    try:
        hit.howler.links.extend(
            Link(
                {
                    "title": get_random_word(),
                    "href": app["route"],
                    "icon": app["name"],
                }
            )
            for app in random.choices(APPS, k=5)
        )
    except IndexError:
        pass

    hit.howler.viewers = []
    hit.howler.hits = []
    hit.howler.bundles = []
    hit.howler.is_bundle = False

    for log in hit.howler.log:
        log.previous_version = get_random_id()

    if prune_hit:
        empty_hit = Hit({"howler": hit.howler})

        for key in hit.fields():
            if key in [
                "howler",
                "event",
                "related",
                "organization",
                "threat",
                "timestamp",
            ]:
                continue

            if hit.howler.analytic.lower() != "assemblyline":
                hit.assemblyline = None
            else:
                verdict = choice(["info", "malicious", "safe", "suspicious"])
                for host in hit.assemblyline.antivirus:
                    host.verdict = verdict
                for host in hit.assemblyline.behaviour:
                    host.verdict = verdict
                for host in hit.assemblyline.heuristic:
                    host.verdict = verdict
                for host in hit.assemblyline.yara:
                    host.verdict = verdict
                for host in hit.assemblyline.attribution:
                    host.verdict = verdict
                for item in hit.assemblyline.mitre.tactic:
                    item.verdict = verdict
                for item in hit.assemblyline.mitre.technique:
                    item.verdict = verdict

                if key in ["related", "file"]:
                    continue

            if round(rand_seed * 4) < 3:
                hit[key] = empty_hit[key]

    return hit


def create_users_with_username(ds: HowlerDatastore, usernames: list[str]):
    """Create basic users with username and password for testing puposes"""
    for username in usernames:
        user_data = User(
            {
                "name": f"{username}",
                "email": f"{username}@howler.cyber.gc.ca",
                "apikeys": {
                    "devkey": {
                        "acl": ["R", "W"],
                        "password": get_password_hash(username),
                    }
                },
                "password": get_password_hash(username),
                "uname": f"{username}",
            }
        )
        ds.user.save(username, user_data)

        if "pytest" not in sys.modules:
            logger.info(f"{username}:{username}")

    ds.user.commit()
    ds.user_avatar.commit()
