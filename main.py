#!/usr/bin/env python3
import os
import random
from pathlib import Path

from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

from src.tasks.certification import create_certificates_task

BASE_DIR = Path(__file__).resolve().parent.parent

app = Celery('main', broker='amqp://localhost')
app.conf.timezone = 'Europe/London' # type: ignore
app.conf.broker_pool_limit = 1

app.conf.task_create_missing_queues = False

default_exchange = Exchange("default", type="direct")
certification_exchange = Exchange("certification", type="direct")
dlx_exchange = Exchange("dlx", type="direct")


queue_arguments = {
    "x-dead-letter-exchange": "dlx",
    "x-dead-letter-routing-key": "dead",
    "x-message-ttl": 600_000,  # 10 minutes
}

app.conf.task_queues = (
    Queue(
        "default",
        exchange=default_exchange,
        routing_key="default",
        queue_arguments=queue_arguments,
    ),
    Queue(
        "2025_certification",
        exchange=certification_exchange,
        routing_key="certification",
        queue_arguments=queue_arguments,
    ),
    Queue(
        "dlx",
        exchange=dlx_exchange,
        routing_key="dead",
    ),
)

app.conf.task_default_exchange = "default" # type: ignore

app.conf.task_routes = {
    "certification.*": {
        "queue": "2025_certification",
        "exchange": "certification",
        "routing_key": "certification",
    }
}

app.conf.beat_schedule = {
    "create-certification-periodic": {
        "task": "certification.first_tasks",
        "schedule": crontab(),
    }
}

@app.task(bind=True, max_retries=5)
def custom_retry_task(self):
    try:
        raise Exception("fail")
    except Exception as exc:
        delay = min(2 ** self.request.retries, 60)
        jitter = random.uniform(0, delay * 0.3)
        raise self.retry(exc=exc, countdown=delay + jitter)


@app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def resilient_task(self):
    print(f"Attempt {self.request.retries + 1}")
    raise Exception("Temporary failure")

create_certificates_task(app)
