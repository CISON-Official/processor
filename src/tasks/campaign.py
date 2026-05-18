#!/usr/bin/env python3
from time import sleep
from random import randint
from logging import Logger
from email.header import Header
from email.utils import formataddr
from email.mime.text import MIMEText

from celery import Celery
from decouple import config
from celery.utils.log import get_task_logger
from src.zoho_main import send_campaign

email_username = str(config("ZOHO_CAMPAIGN_USERNAME"))
email_password = str(config("EMAIL_PASSWORD"))


def send_campaign_email(logger: Logger, data: dict[str, str]) -> None:
    # time_to_wait = randint(1, 500)

    # print(f"waiting for {time_to_wait} secs")

    # logger.info(f"Waiting for {time_to_wait}")
    # sleep(time_to_wait)

    email, template, title = data.get("email"), data.get("template"), data.get("title")

    msg = MIMEText(str(template), "html", "utf-8")
    msg["Subject"] = Header(str(title), "utf-8")  # type: ignore
    msg["From"] = formataddr(
        (
            str(
                Header(
                    "Charactered Institute of Statisticians of Nigeria (CISON)", "utf-8"
                )
            ),
            email_username,
        )
    )
    msg["To"] = email  # type: ignore

    if not email or not template or not title:
        raise Exception("Email, title or template is not set")

    send_campaign(title, email, msg)


def create_campaign_email(app: Celery):

    logger = get_task_logger(__name__)
    logger.info("Task created")

    @app.task(
        bind=True,
        name="email.campaign_email",
        autoretry_for=(Exception,),
        retry_backoff=True,
        retry_jitter=True,
        max_retries=5,
        acks_late=True,
        reject_on_worker_lost=True,
    )
    def create_task(self, **kwargs):
        logger.info("Performing Task")
        try:
            send_campaign_email(logger, kwargs)
            logger.info(f"Certificate created successfully for {kwargs.get('name')}")
        except Exception as e:
            logger.error(f"Failed for {kwargs.get('name')}: {e}", exc_info=True)
            logger.error(
                "Failed to send email to %s" % kwargs.get("email"), exc_info=True
            )
            # raise

    return create_task
