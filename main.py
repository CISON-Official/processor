#!/usr/bin/env python3

import random
import logging
from pathlib import Path

from celery import Celery
from celery.schedules import crontab
from celery.exceptions import Reject
from celery.signals import (
    after_setup_logger,
    after_setup_task_logger,
    task_revoked,
)
from kombu import Exchange, Queue

from src.logger import setup_celery_logging
from src.tasks.conference import create_conference_certificate
from src.tasks.certification import create_membership_certificate
from src.tasks.preconference import create_preconference_certificate
from src.tasks.email import create_email
from src.tasks.first_prs import create_first_prs_2026_certificate
from src.tasks.campaign import create_campaign_email
from src.tasks.second_prs import create_second_prs_2026_certificate

# -------------------------------------------------------------------
# Base config
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

BROKER_URL = "amqp://localhost"
TIMEZONE = "Europe/London"

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Celery app
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# Celery app
# -------------------------------------------------------------------

# Install redis via your virtual environment if selected: pip install redis
app = Celery("main", broker=BROKER_URL, backend="redis://localhost:6379/0")
app.conf.result_persistent = True
app.conf.update(
    timezone=TIMEZONE,
    broker_pool_limit=1,
    task_ignore_result=True,  # Suppresses result routing queues
    worker_gossip=False,  # Disables gossip
    worker_mingle=False,  # Disables startup synchronisation
    实时_worker_heartbeat=False,  # Shuts down heartbeat monitor checks
    # Reliability
    task_acks_late=True,
    worker_max_memory_per_child=120000,
    task_reject_on_worker_lost=True,
    task_create_missing_queues=False,
    result_expires=None,
    task_store_errors_even_if_ignored=True,
)


# -------------------------------------------------------------------
# Exchanges & Queues (with DLQ)
# -------------------------------------------------------------------

default_exchange = Exchange("default", type="direct")
certification_exchange = Exchange("certification", type="direct")
dlx_exchange = Exchange("dlx", type="direct")

QUEUE_ARGUMENTS = {
    "x-dead-letter-exchange": "dlx",
    "x-dead-letter-routing-key": "dead",
    "x-message-ttl": 600_000,
}

app.conf.task_queues = (
    Queue(
        "default",
        exchange=default_exchange,
        routing_key="default",
        queue_arguments=QUEUE_ARGUMENTS,
    ),
    Queue(
        "2025_certification",
        exchange=certification_exchange,
        routing_key="certification",
        queue_arguments=QUEUE_ARGUMENTS,
    ),
    Queue(
        "2026_first_prs",
        exchange=certification_exchange,
        routing_key="first_prs",
        queue_arguments=QUEUE_ARGUMENTS,
    ),
    Queue(
        "2026_second_prs",
        exchange=certification_exchange,
        routing_key="second_prs",
        queue_arguments=QUEUE_ARGUMENTS,
    ),
    Queue(
        "dlx",
        exchange=dlx_exchange,
        routing_key="dead",
    ),
)

app.conf.task_default_exchange = "default"

app.conf.task_routes = {
    "certification.*": {
        "queue": "2025_certification",
        "exchange": "certification",
        "routing_key": "certification",
    }
}

# -------------------------------------------------------------------
# Beat schedule
# -------------------------------------------------------------------

app.conf.beat_schedule = {
    "create-certification-periodic": {
        "task": "certification.first_tasks",
        "schedule": crontab(),
    }
}

# -------------------------------------------------------------------
# Logging hooks
# -------------------------------------------------------------------


@after_setup_logger.connect
def configure_worker_logger(**_):
    setup_celery_logging()


@after_setup_task_logger.connect
def configure_task_logger(**_):
    setup_celery_logging()


# -------------------------------------------------------------------
# Signals
# -------------------------------------------------------------------


@task_revoked.connect
def handle_task_revoked(sender=None, request=None, **_):
    task_id = request.id if request else "unknown"
    logger.warning("Task revoked: %s", task_id)


# -------------------------------------------------------------------
# Example retry patterns
# -------------------------------------------------------------------


@app.task(bind=True, max_retries=5, acks_late=True, reject_on_worker_lost=True)
def custom_retry_task(self):
    try:
        raise Exception("fail")
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            raise Reject(exc, requeue=False)

        delay = min(2**self.request.retries, 60)
        jitter = random.uniform(0, delay * 0.3)
        raise self.retry(exc=exc, countdown=delay + jitter)


@app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
    reject_on_worker_lost=True,
)
def resilient_task(self):
    logger.info("Attempt %s", self.request.retries + 1)

    if self.request.retries >= self.max_retries:
        raise Reject(Exception("Permanent failure"), requeue=False)

    raise Exception("Temporary failure")


# -------------------------------------------------------------------
# Task registration
# -------------------------------------------------------------------

create_membership_certificate(app)
create_conference_certificate(app)
create_preconference_certificate(app)
create_email(app)
create_first_prs_2026_certificate(app)
create_campaign_email(app)
create_second_prs_2026_certificate(app)
