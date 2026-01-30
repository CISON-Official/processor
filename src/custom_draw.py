#!/usr/bin/env python3

from PIL import Image, ImageDraw, ImageFont


def add_custom_text(
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
            "RGBA", (int(text_width + 300), int(text_height + 30)), (0, 0, 0, 0)
        )
        draw_text = ImageDraw.Draw(text_image)
        draw_text.text((0, 0), text=text, font=font, fill="black")
        rotated_text = text_image.rotate(90.0, expand=True)
        img.paste(rotated_text, position, rotated_text)
        return
    draw.text(position, text, "black", font, spacing=2)
