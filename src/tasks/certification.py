#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from typing import Any
from pathlib import Path
from datetime import datetime, timezone
from tempfile import NamedTemporaryFile

from celery import Celery
from PIL import Image, ImageDraw, ImageFont
from celery.utils.log import get_task_logger

from src.tasks.schema import CertificatePayload


BASE_DIR = Path(__file__).resolve().parent.parent.parent
logger = get_task_logger(__name__)


def generate_certificate_2025(data: dict[str, Any]) -> str:
    """
    Generates a personalized certificate using a PNG template and saves it.

    Args:
        data: Dictionary containing at least:
              - "name": The person's name to display
              - "certificate_name": Optional title or certificate type (used for font sizing)
              - Optional: "date" or other fields if you want to add more text

    Returns:
        str: Path to the generated certificate file
    """
    person_name = data.get("name")
    certificate_title = data.get("certificate_name", "")

    if not person_name:
        raise ValueError("Missing required field: 'name'")

    name_length = len(person_name)
    if name_length <= 30:
        font_size = 60
    elif name_length <= 40:
        font_size = 50
    elif name_length <= 50:
        font_size = 40
    else:
        font_size = 35

    try:
        font = ImageFont.truetype(
            BASE_DIR / Path("assets/fonts/Dynalight-Regular.ttf"), font_size
        )
    except OSError:

        font = ImageFont.load_default(font_size)
        print("Warning: arial.ttf not found, using default font.")

    text_position = (300, 400)
    template_path = BASE_DIR / Path("assets/media/certificate_template.png")
    if not template_path.exists():
        raise FileNotFoundError(
            "Certificate template not found: certificate_template.png",
            f"{template_path}",
        )

    with Image.open(template_path) as img:
        img = img.convert("RGB")
        draw = ImageDraw.Draw(img)
        stroke_width = 1
        stroke_fill = "green"

        draw.text(
            text_position,
            person_name.strip(),
            font=font,
            fill="green",
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
            anchor="mm",
        )

        small_font_size = 30
        small_font = ImageFont.load_default()

        if certificate_title:
            draw.text(
                (500, 600),
                certificate_title,
                font=small_font,
                fill="black",
                anchor="mm",
            )

        current_date = datetime.now(timezone.utc).strftime("%B %d, %Y")
        draw.text(
            (500, 1000),
            f"Date: {current_date}",
            font=small_font,
            fill="gray",
            anchor="mm",
        )

        output_path = Path(
            f"certificates/{person_name.replace(' ', '_')}_certificate.png"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)

        img.save(output_path, "PNG")

    upload_certificate_to_folder(output_path)

    return str(output_path)


def upload_certificate_to_folder(certificate_path: str | Path):
    """
    Uploads the generated certificate to a remote folder (e.g., cloud storage, SFTP, etc.).

    Args:
        certificate_path: Local path to the generated certificate file
    """
    certificate_path = Path(certificate_path)
    if not certificate_path.exists():
        raise FileNotFoundError(f"Certificate file not found: {certificate_path}")

    print(f"Uploaded certificate: {certificate_path}")


def create_certificates_task(app: Celery):
    logger = get_task_logger(__name__)
    logger.info("Task created")

    @app.task(
        bind=True,
        name="certification.first_tasks",
        autoretry_for=(Exception,),
        retry_backoff=True,
        retry_jitter=True,
        retry_kwargs={"max_retries": 5},
    )
    def create_certificates(self, **kwargs):
        logger.info("Performing Task")
        logger.info(f"Processing certificate for: {kwargs.get('name')}")
        try:
            generate_certificate_2025(kwargs)
            logger.info(f"Certificate created successfully for {kwargs.get('name')}")
        except Exception as e:
            logger.error(f"Failed for {kwargs.get('name')}: {e}", exc_info=True)
            raise

    return create_certificates
