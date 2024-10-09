from howler import odm


@odm.model(
    index=True,
    store=True,
    description="Holds information like interface number, name, vlan, and zone to classify ingress traffic",
)
class Ingress(odm.Model):
    zone = odm.Optional(odm.Keyword(description="Network zone of incoming traffic as reported by observer"))
