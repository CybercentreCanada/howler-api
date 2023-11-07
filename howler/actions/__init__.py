import re
from typing import Any, Optional

import howler.actions.add_label as add_label
import howler.actions.change_field as change_field
import howler.actions.add_to_bundle as add_to_bundle
import howler.actions.change_field as change_field
import howler.actions.prioritization as prioritization
import howler.actions.remove_from_bundle as remove_from_bundle
import howler.actions.remove_label as remove_label
import howler.actions.spellbook as spellbook
import howler.actions.transition as transition
from howler.config import config

OPERATIONS = {
    add_label.OPERATION_ID: add_label,
    remove_label.OPERATION_ID: remove_label,
    transition.OPERATION_ID: transition,
    prioritization.OPERATION_ID: prioritization,
    change_field.OPERATION_ID: change_field,
    add_to_bundle.OPERATION_ID: add_to_bundle,
    remove_from_bundle.OPERATION_ID: remove_from_bundle,
}

if config.core.spellbook.enabled:
    OPERATIONS[spellbook.OPERATION_ID] = spellbook


def __sanitize_specification(spec: dict[str, Any]) -> dict[str, Any]:
    """Adapt the specification for use in the UI

    Args:
        spec (dict[str, Any]): The raw specification

    Returns:
        dict[str, Any]: The sanitized specification for use in the UI
    """
    return {
        **spec,
        "description": {
            **spec["description"],
            "long": re.sub(r"\n +(request_id|query).+", "", spec["description"]["long"])
            .replace("\n    ", "\n")
            .replace("Args:", "Args:\n"),
        },
        "steps": [
            {**step, "args": {k: list(v) for k, v in step["args"].items()}}
            for step in spec["steps"]
        ],
    }


def __sanitize_report(report: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate identical entries with different queries

    Args:
        report (list[dict[str, Any]]): The unsanitized, verbose report

    Returns:
        list[dict[str, Any]]: The sanitized, concise report
    """
    by_message: dict[str, Any] = {}

    for entry in report:
        # if these three keys match, we should merge the queries that use them both. For example, when multiple hits
        # fail to transition for the same reason.
        key = f"{entry['title']}==={entry['message']}==={entry['outcome']}"

        if key in by_message:
            by_message[key].append(f'({entry["query"]})')
        else:
            by_message[key] = [f'({entry["query"]})']

    sanitized: list[dict[str, Any]] = []
    for key, queries in by_message.items():
        (title, message, outcome) = key.split("===")

        sanitized.append(
            {
                "query": " OR ".join(queries),
                "outcome": outcome,
                "title": title,
                "message": message,
            }
        )

    return sanitized


def execute(
    operation_id: str,
    query: str,
    user: dict[str, Any],
    request_id: Optional[str] = None,
    **kwargs,
) -> list[dict[str, Any]]:
    """Execute a specification

    Args:
        operation_id (str): The id of the operation to run
        query (str): The query to run this action on
        user (dict[str, Any]): The user running this action
        request_id (str, None): A user-provided ID, can be used to track the progress of their excecution via websockets

    Returns:
        list[dict[str, Any]]: A report on the execution
    """
    automation = OPERATIONS.get(operation_id, None)

    if automation is None:
        return [
            {
                "query": query,
                "outcome": "error",
                "title": "Unknown Action",
                "message": f"The operation ID provided ({operation_id}) does not match any enabled operations.",
            }
        ]

    missing_roles = set(automation.specification()["roles"]) - set(user["type"])
    if missing_roles:
        return [
            {
                "query": query,
                "outcome": "error",
                "title": "Insufficient permissions",
                "message": (
                    f"The operation ID provided ({operation_id}) requires permissions you do not have "
                    f"({', '.join(missing_roles)}). Contact HOWLER Support for more information."
                ),
            }
        ]

    report = automation.execute(query=query, request_id=request_id, user=user, **kwargs)

    return __sanitize_report(report)


def specifications() -> list[dict[str, Any]]:
    """A list of specifications for the available operations

    Returns:
        list[dict[str, Any]]: A list of specifications
    """
    return [
        __sanitize_specification(automation.specification())
        for automation in OPERATIONS.values()
    ]
