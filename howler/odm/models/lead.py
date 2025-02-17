# mypy: ignore-errors
from typing import Optional

from howler import odm
from howler.odm.howler_enum import HowlerEnum


class Formats(str, HowlerEnum):
    MARKDOWN = "markdown"

    def __str__(self) -> str:
        return self.value


@odm.model(
    index=True,
    store=True,
    description="The dossier object stores individual tabs/fields for a given alert.",
)
class LocalizedLabel(odm.Model):
    en: str = odm.Text(description="The english localization of a label")
    fr: str = odm.Text(description="The french localization of a label")


@odm.model(
    index=False,
    store=True,
    description="The dossier object stores individual tabs/fields for a given alert.",
)
class Lead(odm.Model):
    icon: Optional[str] = odm.Text(
        description="An optional icon to use in the tab display for this dossier.", optional=True
    )
    label: LocalizedLabel = odm.Compound(LocalizedLabel, description="Labels for the lead in the UI.")
    format: str = odm.Enum(values=Formats, description="The format of the lead. ")
    content: str = odm.Text(
        description="The data for the content. Could be a link, raw markdown text, or other valid lead format.",
    )
    metadata: Optional[str] = odm.Json(
        optional=True, description="Metadata associated with this dossier. Use varies based on format."
    )
