#!/usr/bin/env python
from pathlib import Path

from typing import Any
from celery import Celery
from logging import Logger
from decouple import config
from PIL import ImageFont, Image, ImageDraw
from celery.utils.log import get_task_logger

from src.template import EmailTemplate
from src.custom_email import ZohoEmailer
from src.custom_draw import add_custom_text


email_username = str(config("EMAIL_USERNAME"))
email_password = str(config("EMAIL_PASSWORD"))


BASE_DIR = Path(__file__).resolve().parent.parent.parent
logger = get_task_logger(__name__)


def generate_2025_preconference_certificate(
    logger: Logger, data: dict[str, Any]
) -> str:

    person_name = data.get("name")
    email = data.get("email")
    first_name = data.get("first_name")
    cert_id = data.get("certificate_id")
    logger.info(f"Data: {data} {cert_id}")

    if not person_name:
        raise ValueError("Missing required field: 'name'")

    name_length = len(person_name)
    if name_length <= 30:
        font_size = 80
    elif name_length <= 40:
        font_size = 70
    elif name_length <= 50:
        font_size = 60
    else:
        font_size = 50

    try:
        font = ImageFont.truetype(
            BASE_DIR / Path("assets/fonts/Birthstone-Regular.ttf"), font_size
        )
    except OSError:

        font = ImageFont.load_default(font_size)
        print("Warning: arial.ttf not found, using default font.")

    text_position = (310, 520)
    template_path = BASE_DIR / Path("assets/media/pre_conference_certificate.jpg")
    if not template_path.exists():
        raise FileNotFoundError(
            "Certificate template not found: certificate_template.png",
            f"{template_path}",
        )

    with Image.open(template_path) as img:
        img = img.convert("RGB")
        draw = ImageDraw.Draw(img)
        stroke_width = 1
        stroke_fill = "#1A693D"

        draw.text(
            text_position,
            person_name.strip().upper(),
            font=font,
            fill="#1A693D",
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
            # anchor="mm",
        )
        small_font = ImageFont.load_default(20)
        add_custom_text(img, draw, small_font, str(cert_id), (80, 490), True)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        output_path = Path(
            f"pdf_uploads/preconference/{person_name.replace(' ', '_')}_certificate.pdf"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PDF", resolution=100.0)

        mailer = ZohoEmailer(email_username, email_password)
        mailer.send_email(
            str(email),
            "Preconference Certificate",
            html_body=EmailTemplate.preconference_template(str(first_name)),
            attachments=[str(output_path)],
        )

    return str(output_path)


def create_preconference_certificate(app: Celery):

    logger = get_task_logger(__name__)
    logger.info("Task created")

    @app.task(
        bind=True,
        name="certification.preconference_certificate",
        autoretry_for=(Exception,),
        retry_backoff=True,
        retry_jitter=True,
        max_retries=5,
        acks_late=True,
        reject_on_worker_lost=True,
    )
    def create_certificates(self, **kwargs):
        logger.info("Performing Task")
        logger.info(f"Processing preconference certificate for: {kwargs.get('name')}")
        try:
            generate_2025_preconference_certificate(logger, kwargs)
            logger.info(f"Certificate created successfully for {kwargs.get('name')}")
        except Exception as e:
            logger.error(f"Failed for {kwargs.get('name')}: {e}", exc_info=True)
            raise

    return create_certificates
