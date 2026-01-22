#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from typing import Any
from pathlib import Path
from tempfile import NamedTemporaryFile
from datetime import datetime, timezone, timedelta

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

    def add_custom(
        img: Image.Image,  # Add this parameter
        draw: ImageDraw.ImageDraw,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        text: str,
        position: tuple[int, int],
        rotated: bool = False,
    ) -> None:
        if rotated:
            bbox = font.getbbox(text)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            text_image = Image.new(
                "RGBA", (text_width + 300, text_height + 30), (0, 0, 0, 0)
            )
            draw_text = ImageDraw.Draw(text_image)
            draw_text.text(
                (0, 0), text=text, font=font, fill="black"
            )  # Also fixed this line
            rotated_text = text_image.rotate(90.0, expand=True)
            img.paste(rotated_text, position, rotated_text)  # Complete line 48
            return
        draw.text(position, text, "black", font, spacing=2)

    person_name = data.get("name")

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
            BASE_DIR / Path("assets/fonts/Dynalight-Regular.ttf"), font_size
        )
    except OSError:

        font = ImageFont.load_default(font_size)
        print("Warning: arial.ttf not found, using default font.")

    text_position = (130, 490)
    template_path = BASE_DIR / Path("assets/media/new_certificate_template.jpg")
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

        small_font_size = 22
        small_font = ImageFont.load_default(small_font_size)

        current_date = datetime.now(timezone.utc).strftime("%d/%m/%Y")
        expiry_date = datetime.now(timezone.utc) + timedelta(days=730)
        expiry_date = expiry_date.strftime("%d/%m/%Y")

        width, height = img.size
        height = 987

        membership_id = str(data.get("membership_id"))
        certificate_id = str(data.get("certificate_id"))

        add_custom(
            img, draw, small_font, membership_id, (130, height)
        )  # For membership ID
        add_custom(
            img,
            draw,
            small_font,
            "2025-" + str(data.get("certificate_id")),
            (605, 1000),
        )  # For Certificate ID
        add_custom(img, draw, small_font, current_date, (970, height))  # For Issue date
        add_custom(
            img, draw, small_font, expiry_date, (1484, 500), True
        )  # For Expiry date

        output_path = Path(
            f"certificates/{person_name.replace(' ', '_')}_certificate.png"
        )
        img.save(output_path, "PNG")

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        output_path_pdf = Path(f"pdf_upload/certificate_2025-{certificate_id}.pdf")

        output_path_pdf.parent.mkdir(parents=True, exist_ok=True)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        img.save(output_path_pdf, "PDF", resolution=100.0)

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


def create_membership_certificate(app: Celery):
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
