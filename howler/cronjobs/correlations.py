from datetime import datetime, timedelta
import hashlib
import json
import random
import re
import sys
from typing import Any, Optional
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.triggers.cron import CronTrigger
from howler.common.exceptions import HowlerValueError
from howler.common.loader import datastore

from sigma.backends.elasticsearch import LuceneBackend
from sigma.rule import SigmaRule
from yaml.scanner import ScannerError

from howler.common.logging import get_logger
from howler.config import DEBUG, HWL_ENABLE_CORRELATIONS, config
from howler.datastore.collection import ESCollection
from howler.datastore.exceptions import SearchException
from howler.datastore.operations import OdmHelper, OdmUpdateOperation
from howler.odm.models.analytic import Analytic
from howler.odm.models.hit import Hit
from howler.odm.models.howler_data import HitOperationType
from howler.services import hit_service

logger = get_logger(__file__)
hit_helper = OdmHelper(Hit)

__scheduler_instance: Optional[BaseScheduler] = None


def create_correlated_bundle(
    correlation: Analytic, query: str, correlated_hits: list[Hit]
):
    # We'll create a hash using the hashes of the children, and the analytic ID/current time
    bundle_hash = hashlib.sha256()
    bundle_hash.update(correlation.analytic_id.encode())
    bundle_hash.update(query.replace("now", datetime.now().isoformat()).encode())
    for match in correlated_hits:
        bundle_hash.update(match.howler.hash.encode())

    hashed = bundle_hash.hexdigest()

    # If a matching bundle exists already, just reused it (likely only ever lucene specific)
    existing_result = datastore().hit.search(f"howler.hash:{hashed}", rows=1)
    if existing_result["total"] > 0:
        logger.debug(f"Correlation hash {hashed} exists - skipping create")
        return existing_result["items"][0]

    child_ids = [match.howler.id for match in correlated_hits]

    correlated_bundle = Hit(
        {
            "howler.analytic": correlation.name,
            "howler.detection": "Correlation",
            "howler.score": 0.0,
            "howler.hash": hashed,
            "howler.is_bundle": True,
            "howler.hits": child_ids,
            "howler.data": [
                json.dumps(
                    {
                        "raw": correlation.correlation,
                        "sanitized": query,
                    }
                )
            ],
            "event.created": "NOW",
            "event.kind": "alert",
            "event.module": correlation.correlation_type,
            "event.provider": "howler",
            "event.reason": f"Children match {query}",
            "event.type": ["info"],
        }
    )
    correlated_bundle.event.id = correlated_bundle.howler.id

    datastore().hit.save(correlated_bundle.howler.id, correlated_bundle)

    if len(child_ids) > 0:
        datastore().hit.update_by_query(
            f"howler.id:({' OR '.join(child_ids)})",
            [
                hit_helper.list_add(
                    f"howler.bundles",
                    correlated_bundle.howler.id,
                    if_missing=True,
                ),
                OdmUpdateOperation(
                    ESCollection.UPDATE_APPEND,
                    "howler.log",
                    {
                        "timestamp": "NOW",
                        "key": "howler.bundles",
                        "explanation": f"This hit was correlated by the analytic '{correlation.name}'.",
                        "new_value": correlated_bundle.howler.id,
                        "previous_value": "None",
                        "type": HitOperationType.APPENDED,
                        "user": "Howler",
                    },
                ),
            ],
        )

    return correlated_bundle


def create_executor(correlation: Analytic):
    def execute():
        try:
            if not correlation.correlation or not correlation.correlation_type:
                logger.error(
                    "Invalid correlation %s! Skipping", correlation.analytic_id
                )
                return

            logger.info(
                "Executing correlation %s (%s)",
                correlation.name,
                correlation.analytic_id,
            )

            correlated_hits: Optional[list[Hit]] = None

            if correlation.correlation_type in ["lucene", "sigma"]:
                if correlation.correlation_type == "lucene":
                    query = re.sub(
                        r"\n+", " ", re.sub(r"#.+", "", correlation.correlation)
                    ).strip()
                else:
                    try:
                        rule = SigmaRule.from_yaml(correlation.correlation)
                    except ScannerError as e:
                        raise HowlerValueError(
                            f"Error when parsing yaml: {e.problem} {e.problem_mark}",
                            cause=e,
                        )

                    es_collection = datastore().hit
                    lucene_queries = LuceneBackend(
                        index_names=[es_collection.index_name]
                    ).convert_rule(rule)

                    query = " AND ".join([f"({q})" for q in lucene_queries])

                num_hits = datastore().hit.search(query, rows=1)["total"]
                if num_hits > 0:
                    bundle = create_correlated_bundle(correlation, query, [])
                    datastore().hit.update_by_query(
                        f"({query}) AND -howler.bundles:{bundle.howler.id}",
                        [
                            hit_helper.list_add(
                                "howler.bundles",
                                bundle.howler.id,
                                if_missing=True,
                            ),
                            OdmUpdateOperation(
                                ESCollection.UPDATE_APPEND,
                                "howler.log",
                                {
                                    "timestamp": "NOW",
                                    "key": "howler.bundles",
                                    "explanation": f"This hit was correlated by the analytic '{correlation.name}'.",
                                    "new_value": bundle.howler.id,
                                    "previous_value": "None",
                                    "type": HitOperationType.APPENDED,
                                    "user": "Howler",
                                },
                            ),
                        ],
                    )

                    datastore().hit.commit()

                    child_hits: list[Hit] = datastore().hit.search(
                        f"howler.bundles:{bundle.howler.id}", rows=1000, fl="howler.id"
                    )["items"]
                    datastore().hit.update_by_query(
                        f"howler.id:{bundle.howler.id}",
                        [
                            hit_helper.list_add(
                                "howler.hits", hit.howler.id, if_missing=True
                            )
                            for hit in child_hits
                        ],
                    )

            elif correlation.correlation_type == "eql":
                query = correlation.correlation

                result = datastore().hit.raw_eql_search(
                    query, rows=25, fl=",".join(Hit.flat_fields().keys())
                )

                if len(result["sequences"]) > 0:
                    for sequence in result["sequences"]:
                        if len(sequence) > 0:
                            create_correlated_bundle(correlation, query, sequence)

                correlated_hits = result["items"]

            else:
                raise HowlerValueError(
                    f"Unknown correlation type: {correlation.correlation_type}"
                )

            if correlated_hits and len(correlated_hits) > 0:
                create_correlated_bundle(correlation, query, correlated_hits)
        except Exception as e:
            logger.debug(e, exc_info=True)
            if __scheduler_instance:
                __scheduler_instance.remove_job(
                    f"correlation_{correlation.analytic_id}"
                )
            # TODO: Allow restarting of correlations
            logger.critical(
                f"Correlation {correlation.name} ({correlation.analytic_id}) has been stopped, due to an exception: {type(e)}",
                exc_info=True,
            )

    return execute


def register_correlations(new_correlation: Optional[Analytic] = None):
    global __scheduler_instance
    if not __scheduler_instance:
        logger.error("Scheduler instance does not exist!")
        return

    if "pytest" in sys.modules:
        logger.info("Skipping registration, running in a test environment")
        return

    if new_correlation:
        if __scheduler_instance.get_job(f"correlation_{new_correlation.analytic_id}"):
            logger.info(
                f"Updating existing correlation: {new_correlation.analytic_id} on interval {new_correlation.correlation_crontab}"
            )

            # remove the existing job
            __scheduler_instance.remove_job(
                f"correlation_{new_correlation.analytic_id}"
            )
        else:
            logger.info(
                f"Registering new correlation: {new_correlation.analytic_id} on interval {new_correlation.correlation_crontab}"
            )
        correlations = [new_correlation]
    else:
        logger.debug("Registering correlations")
        correlations: list[Analytic] = datastore().analytic.search(
            "_exists_:correlation"
        )["items"]

    total_initialized = 0
    for correlation in correlations:
        job_id = f"correlation_{correlation.analytic_id}"
        interval = correlation.correlation_crontab or f"{random.randint(0, 59)} * * * *"

        if __scheduler_instance.get_job(job_id):
            logger.debug(f"Correlation {job_id} already running!")
            return

        logger.debug(
            f"Initializing correlation cronjob with:\tJob ID: {job_id}\tCorrelation Name: {correlation.name}\tCrontab: {interval}"
        )

        if DEBUG or new_correlation:
            _kwargs: dict[str, Any] = {"next_run_time": datetime.now()}
        else:
            _kwargs = {}

        total_initialized += 1
        __scheduler_instance.add_job(
            id=job_id,
            func=create_executor(correlation),
            trigger=CronTrigger.from_crontab(interval),
            **_kwargs,
        )

    logger.info(f"Initialized {total_initialized} correlations")


def setup_job(sched: BaseScheduler):
    if not DEBUG and not HWL_ENABLE_CORRELATIONS:
        logger.debug("Correlation integration disabled")
        return

    logger.debug("Correlation integration enabled")

    global __scheduler_instance
    __scheduler_instance = sched

    register_correlations()

    logger.debug("Initialization complete")
