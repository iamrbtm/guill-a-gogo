from __future__ import annotations

import logging

from worker.celery_app import celery

logger = logging.getLogger("guill.worker")


@celery.task(bind=True, max_retries=3)
def send_invitation_email(self, email: str, link: str) -> None:
    # Phase 1 placeholder: wiring for async email delivery. The actual send
    # uses the API's EmailService via a shared helper; kept here so the worker
    # has a real, schedulable unit of work.
    logger.info("worker: would send invitation email to %s link=%s", email, link)


@celery.task
def refresh_provider_cache() -> None:
    """Scheduled job (Celery beat) skeleton.

    In Phase 3/5 this will refresh routing, fuel, weather, and road-condition
    caches. It is a no-op stub until those providers are implemented.
    """
    logger.info("worker: provider cache refresh (not yet implemented)")
