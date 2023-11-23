from howler.common.loader import datastore
from howler.datastore.operations import OdmHelper
from howler.odm.models.action import VALID_TRIGGERS
from howler.odm.models.hit import Hit
from howler.services import hit_service
from howler.utils.str_utils import sanitize_lucene_query

hit_helper = OdmHelper(Hit)

OPERATION_ID = "add_to_bundle"


def execute(query: str, bundle_id=None, **kwargs):
    """Add a set of hits matching the query to the specified bundle.

    Args:
        query (str): The query containing the matching hits
        bundle_id (str): The `howler.id` of the bundle to add the hits to.
    """

    report = []

    bundle_hit = hit_service.get_hit(bundle_id, as_odm=True)
    if not bundle_hit or not bundle_hit.howler.is_bundle:
        report.append(
            {
                "query": query,
                "outcome": "error",
                "title": "Invalid Bundle",
                "message": f"Either a hit with ID {bundle_id} does not exist, or it is not a bundle.",
            }
        )
        return report

    ds = datastore()

    skipped_hits_bundles = ds.hit.search(
        f"({query}) AND howler.is_bundle:true",
        fl="howler.id",
    )["items"]

    if len(skipped_hits_bundles) > 0:
        report.append(
            {
                "query": f"({query}) AND howler.is_bundle:true",
                "outcome": "skipped",
                "title": "Skipped Bundles",
                "message": "Bundles cannot be added to a bundle.",
            }
        )

    skipped_hits_already_added = ds.hit.search(
        f"({query}) AND (howler.bundles:{sanitize_lucene_query(bundle_id)})",
        fl="howler.id",
    )["items"]

    if len(skipped_hits_already_added) > 0:
        report.append(
            {
                "query": f"({query}) AND (howler.bundles:{sanitize_lucene_query(bundle_id)})",
                "outcome": "skipped",
                "title": "Skipped Hits",
                "message": f"These hits have already been added to the specified bundle.",
            }
        )

    try:
        safe_query = f"({query}) AND (-howler.bundles:({sanitize_lucene_query(bundle_id)}) AND howler.is_bundle:false)"

        matching_hits = ds.hit.search(safe_query)["items"]
        if len(matching_hits) < 1:
            report.append(
                {
                    "query": safe_query,
                    "outcome": "skipped",
                    "title": "No Matching Hits",
                    "message": f"There were no hits matching this query.",
                }
            )
            return report

        ds.hit.update_by_query(
            safe_query,
            [
                hit_helper.list_add(
                    f"howler.bundles", sanitize_lucene_query(bundle_id), if_missing=True
                )
            ],
        )

        hit_service.update_hit(
            bundle_id,
            [
                hit_helper.list_add(f"howler.hits", h["howler"]["id"], if_missing=True)
                for h in matching_hits
            ],
        )

        report.append(
            {
                "query": safe_query.replace("-howler.bundles", "howler.bundles"),
                "outcome": "success",
                "title": "Executed Successfully",
                "message": f"The specified bundle has had all matching hits added.",
            }
        )
    except Exception as e:
        report.append(
            {
                "query": query,
                "outcome": "error",
                "title": "Failed to Execute",
                "message": f"Unknown exception occurred: {str(e)}",
            }
        )

    return report


def specification():
    return {
        "id": OPERATION_ID,
        "title": "Add to Bundle",
        "i18nKey": f"operations.{OPERATION_ID}",
        "description": {
            "short": "Add a set of hits to a bundle",
            "long": execute.__doc__,
        },
        "roles": ["automation_basic"],
        "steps": [
            {
                "args": {"bundle_id": []},
                "options": {},
                "validation": {
                    "warn": {
                        "query": "howler.bundles:($bundle_id) OR howler.is_bundle:true"
                    },
                    "error": {
                        "query": "howler.id:$bundle_id AND howler.is_bundle:false",
                        "message": "The bundle id given must be a bundle.",
                    },
                },
            }
        ],
        "triggers": VALID_TRIGGERS,
    }
