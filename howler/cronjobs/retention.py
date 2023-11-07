from datetime import datetime, timedelta
from typing import Any
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.triggers.cron import CronTrigger

from howler.common.logging import get_logger
from howler.config import DEBUG, config

logger = get_logger(__file__)


def execute():
    from howler.common.loader import datastore

    delta_kwargs = {
        config.system.retention.limit_unit: config.system.retention.limit_amount
    }

    cutoff = (datetime.now() - timedelta(**delta_kwargs)).strftime("%Y-%m-%d")

    logger.info("Removing hits older than %s", cutoff)

    ds = datastore()

    ds.hit.delete_by_query(f"event.created:{{* TO {cutoff}}}")
    ds.hit.commit()

    logger.debug("Deletion complete")


def setup_job(sched: BaseScheduler):
    if not config.system.retention.enabled:
        if not DEBUG or config.system.type == "production":
            logger.warn(
                "Retention cronjob disabled! This is not recommended for a production settings."
            )

        return

    logger.info(
        f"Initializing retention cronjob with cron {config.system.retention.crontab}"
    )

    if DEBUG:
        _kwargs: dict[str, Any] = {"next_run_time": datetime.now()}
    else:
        _kwargs = {}

    if sched.get_job("retention"):
        logger.info("Retention job already running!")
        return

    sched.add_job(
        id="retention",
        func=execute,
        trigger=CronTrigger.from_crontab(config.system.retention.crontab),
        **_kwargs,
    )
    sched.start()
    logger.debug("Initialization complete")
