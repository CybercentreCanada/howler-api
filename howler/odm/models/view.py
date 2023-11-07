# mypy: ignore-errors
from typing import Literal, Union

from howler import odm


@odm.model(index=True, store=True, description="Model of views")
class View(odm.Model):
    view_id: str = odm.UUID(description="A UUID for this view")
    title: str = odm.Keyword(description="The name of this view.")
    query: str = odm.Keyword(description="The query to run in this view.")
    type: Union[Literal["personal"], Literal["global"], Literal["readonly"]] = odm.Enum(
        values=["personal", "global", "readonly"],
        description="The type of view",
    )
    owner: str = odm.Keyword(
        description="The person to whom this view belongs.",
        optional=True,
    )
