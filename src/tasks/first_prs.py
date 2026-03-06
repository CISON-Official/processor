#!/usr/bin/env python3
from pathlib import Path
from typing import Callable

from celery import Celery
from PIL import ImageFont, Image, ImageDraw
from celery.utils.log import get_task_logger


BASE_DIR = Path(__file__).resolve().parent.parent.parent
logger = get_task_logger(__name__)


def custom_task(data: dict[str, str]) -> None:
    person_name = data.get("name")
    email = data.get("email")

    if not person_name:
        raise ValueError("Missing required field: 'name'")
    if not email:
        raise ValueError("Missing required field: 'email'")

    name_length = len(person_name)
    if name_length <= 30:
        font_size = 100
    elif name_length <= 40:
        font_size = 90
    elif name_length <= 50:
        font_size = 80
    else:
        font_size = 70

    try:
        font = ImageFont.truetype(
            BASE_DIR / Path("assets/fonts/Birthstone-Regular.ttf"), font_size
        )
    except OSError:

        font = ImageFont.load_default(font_size)
        print("Warning: arial.ttf not found, using default font.")

    # text_position = (130, 600)
    template_path = BASE_DIR / Path("assets/media/Certificate of Attendance - Navy and Sage Green Design (1).png")
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

        img_w, _ = img.size
        bbox = draw.textbbox((0, 0), person_name.strip().upper(), font=font)
        text_width, _ = bbox[2] - bbox[0], bbox[3] - bbox[1]

        x = (img_w - text_width) / 2 -bbox[0]

        draw.text(
            (x, 570),
            person_name.strip().upper(),
            font=font,
            fill="#1A693D",
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
            # anchor="mm",
        )
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        output_path = Path(
            f"pdf_uploads/first_prs_2026/{person_name.replace(' ', '_')}_certificate.pdf"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PDF", resolution=100.0)


def create_first_prs_2026_certificate(app: Celery) -> Callable:

    logger = get_task_logger(__name__)
    logger.info("First PRS Task Created")

    @app.task(
        bind=True,
        name="certification.first_prs_2026",
        autoretry_for=(Exception,),
        retry_backoff=True,
        retry_jitter=True,
        max_retries=5,
        acks_late=True,
        reject_on_worker_lost=True,
    )
    def create_certificates(self, **kwargs):
        logger.info("Performing Task")
        logger.info(f"Creating PRS Certificates for: {kwargs.get('name')}")
        try:
            custom_task(kwargs)
            logger.info(f"Certificate created successfully for {kwargs.get('name')}")
        except Exception as e:
            logger.error(f"Failed for {kwargs.get('name')}: {e}", exc_info=True)
            raise

    return create_certificates
