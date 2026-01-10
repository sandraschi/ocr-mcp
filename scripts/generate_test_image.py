import logging
logger = logging.getLogger(__name__)
from PIL import Image, ImageDraw, ImageFont
import os


def generate_sample():
    # Create a white image
    width, height = 800, 400
    image = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(image)

    # Text to render
    text_lines = [
        "OCR-MCP Verification Test",
        "Date: 2026-01-01",
        "Backend: Multi-Engine Test",
        "",
        "This is a sample document for testing OCR extraction.",
        "It contains multiple lines of text to verify",
        "segmentation and character recognition accuracy.",
        "",
        "Technical Specifications:",
        "- Tesseract 5.0+",
        "- PaddleOCR PP-OCRv5",
        "- EasyOCR v1.7",
        "- Florence-2-base",
    ]

    # Try to use a standard font, fallback to default
    try:
        # On Windows, Arial is usually available
        font = ImageFont.truetype("arial.ttf", 24)
        title_font = ImageFont.truetype("arial.ttf", 32)
    except Exception as e:
        font = ImageFont.load_default()
        title_font = font

    y_text = 20
    for i, line in enumerate(text_lines):
        f = title_font if i == 0 else font
        draw.text((40, y_text), line, font=f, fill="black")
        y_text += 30

    save_path = "tests/fixtures/test_sample.png"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    image.save(save_path)
    logger.info(f"Sample image created at: {os.path.abspath(save_path)}")


if __name__ == "__main__":
    generate_sample()
