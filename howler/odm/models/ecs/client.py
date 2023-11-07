# mypy: ignore-errors
from typing import Optional

from howler import odm
from howler.odm.models.ecs.geo import Geo


@odm.model(
    index=True,
    store=True,
    description="Translated NAT sessions (e.g. internal client to internet).",
)
class Nat(odm.Model):
    ip = odm.Optional(odm.IP(description="Translated IP of source based NAT sessions."))
    port = odm.Optional(
        odm.Integer(description="Translated port of source based NAT sessions.")
    )


@odm.model(
    index=True,
    store=True,
    description="A client is defined as the initiator of a network connection "
    "for events regarding sessions, connections, or bidirectional flow records.",
)
class Client(odm.Model):
    address: Optional[str] = odm.Optional(
        odm.Keyword(
            description="Some event client addresses are defined ambiguously. The event will sometimes list an IP, "
            "a domain or a unix socket. You should always store the raw address in the .address field."
        )
    )
    bytes: Optional[int] = odm.Optional(
        odm.Integer(description="Bytes sent from the client to the server.")
    )
    domain: Optional[str] = odm.Optional(
        odm.Domain(description="The domain name of the client system.")
    )
    geo: Geo = odm.Optional(
        odm.Compound(
            Geo,
            description="Geo fields can carry data about a specific location related to an event.",
        )
    )
    ip: Optional[str] = odm.Optional(odm.IP(description="IP address of the client (IPv4 or IPv6)."))
    mac: Optional[str] = odm.Optional(odm.MAC(description="MAC address of the client."))
    nat: Nat = odm.Optional(
        odm.Compound(
            Nat,
            description="Translated NAT sessions (e.g. internal client to internet).",
        )
    )
    packets: Optional[int] = odm.Optional(
        odm.Integer(description="Packets sent from the destination to the source.")
    )
    port: Optional[int] = odm.Optional(odm.Integer(description="Port of the client."))
