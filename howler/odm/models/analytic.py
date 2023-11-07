# mypy: ignore-errors
from typing import Optional

from howler import odm


@odm.model(index=True, store=True, description="Comment definition.")
class Comment(odm.Model):
    id = odm.UUID(description="A unique ID for the comment")
    timestamp = odm.Date(
        description="Timestamp at which the comment took place.", default="NOW"
    )
    modified = odm.Date(
        description="Timestamp at which the comment was last edited.", default="NOW"
    )
    detection: Optional[str] = odm.Keyword(
        description="The detection the comment applies to, if it applies to a particular detection",
        optional=True,
    )
    value = odm.Text(description="The comment itself.")
    user = odm.Keyword(description="User ID who created the comment.")
    reactions: dict[str, str] = odm.Mapping(
        odm.Keyword(),
        default={},
        description="A list of reactions to the comment",
    )


@odm.model(index=True, store=True, description="Model of analytics")
class Analytic(odm.Model):
    analytic_id: str = odm.UUID(description="A UUID for this analytic")
    name: str = odm.Keyword(description="The name of the analytic.")
    owner: str = odm.Keyword(
        description="The username of the user who owns this analytic."
    )
    contributors: list[str] = odm.List(
        odm.Keyword(),
        description="A list of users who have contributed to this analytic.",
        default=[],
    )
    description: Optional[str] = odm.Text(
        description="A markdown description of the analytic", optional=True
    )
    detections: list[str] = odm.List(
        odm.Keyword(),
        description="The detections which this analytic contains.",
        default=[],
    )
    comment: list[Comment] = odm.List(
        odm.Compound(Comment),
        default=[],
        description="A list of comments with timestamps and attribution.",
    )
    correlation: Optional[str] = odm.Keyword(
        description="A correlation query", optional=True
    )
    correlation_type: Optional[str] = odm.Optional(
        odm.Enum(values=["lucene", "eql", "sigma"], description="Type of correlation")
    )
    correlation_crontab: Optional[str] = odm.Keyword(
        description="The interval for the correlation to run at", optional=True
    )
