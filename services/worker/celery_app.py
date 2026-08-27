from __future__ import annotations

import os
import sys

# Allow the worker to import the API package for shared models/config.
API_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "api")
if API_PATH not in sys.path:
    sys.path.insert(0, API_PATH)

from celery import Celery  # noqa: E402

from app.config import get_settings  # noqa: E402

settings = get_settings()

celery = Celery(
    "guill_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["worker.tasks"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
    worker_send_task_events=True,
)


@celery.task
def ping() -> str:
    return "pong"
