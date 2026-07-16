#!/usr/bin/env python3
from io import BytesIO

import segno
from PIL import Image


def generate_qr_image(url: str, scale: int = 8) -> BytesIO:
    """Generate QR code as PNG bytes"""
    # url_upper = url.upper()
    qr = segno.make(url, error="L", boost_error=False)
    buffer = BytesIO()
    qr.save(buffer, kind="png", scale=scale)
    buffer.seek(0)
    return buffer


def add_qr_to_template(
    main: Image.Image, sub: BytesIO, x_pos: int, y_pos: int, qr_size: tuple = (200, 200)
) -> Image.Image:
    """
    Overlays a resized QR code onto a background certificate image template.
    """
    qr = Image.open(sub).convert("RGBA").resize(qr_size, Image.Resampling.NEAREST)
    main.paste(qr, (x_pos, y_pos), qr)
    return main
