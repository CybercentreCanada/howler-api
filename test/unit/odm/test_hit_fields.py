import json
from hashlib import md5

from howler.services import hit_service


def test_build_ecs_alert():
    user_hash = md5(json.dumps({"test": "potato"}).encode()).hexdigest()

    hit, warnings = hit_service.convert_hit(
        {
            "howler.analytic": "ECS",
            "destination.autonomous_systems.number": 1,
            "destination.autonomous_systems.organization_name": "Test LLC",
            "destination.user.domain": "example.com",
            "destination.user.email": "user@example.com",
            "destination.user.full_name": "Example User",
            "destination.user.group.domain": "example.com",
            "destination.user.group.id": "group_id",
            "destination.user.group.name": "Example Group",
            "destination.user.hash": user_hash,
            "destination.user.id": "user_id",
            "destination.user.name": "User name",
            "destination.user.roles": ["user", "admin"],
            "observer.egress.zone": "Z",
            "observer.host_name": "TY",
            "observer.ingress.zone": "TZ",
            "observer.ip": ["127.0.0.1", "8.8.8.8"],
            "observer.mac": ["mac-address-1", "mac-address-2"],
            "observer.name": "test",
            "observer.product": "tester",
            "observer.serial_number": "1A34ABC45",
            "observer.type": "public",
            "observer.vendor": "porttest",
            "observer.version": "123.234.456",
            "rule.author": "TT",
            "rule.category": "C",
            "rule.description": "testing description",
            "rule.id": 1,
            "rule.license": "T",
            "rule.name": "test",
            "rule.reference": "Y",
            "rule.ruleset": "TR",
            "rule.uuid": 0,
            "rule.version": "1.0.0",
            "source.autonomous_systems.number": 1,
            "source.autonomous_systems.organization_name": "Test LLC",
            "source.user.domain": "example.com",
            "source.user.email": "user@example.com",
            "source.user.full_name": "Example User",
            "source.user.group.domain": "example.com",
            "source.user.group.id": "group_id",
            "source.user.group.name": "Example Group",
            "source.user.hash": user_hash,
            "source.user.id": "user_id",
            "source.user.name": "User name",
            "source.user.roles": ["user", "admin"],
        },
        unique=False,
    )

    assert hit.destination.autonomous_systems.number == 1
    assert hit.destination.user.name == "User name"
    assert hit.source.user.name == "User name"
    assert hit.observer.ingress.zone == "TZ"
    assert hit.rule.version == "1.0.0"
    assert hit.source.user.hash == user_hash
    assert hit.observer.ip[1] == "8.8.8.8"
    assert hit.observer.mac[1] == "mac-address-2"

    assert len(warnings) == 0
