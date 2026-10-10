"""Attachment renderers: small, deterministic PDFs (reportlab) and PNGs (Pillow)."""

from __future__ import annotations

import io
import textwrap


def pdf_bytes(heading: str, lines: list[str]) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, invariant=1)  # invariant -> reproducible bytes
    w, h = A4
    y = h - 60
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, heading)
    y -= 26
    c.setFont("Helvetica", 10)
    for line in lines:
        for part in (textwrap.wrap(line, 95) or [""]):
            if y < 60:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = h - 60
            c.drawString(50, y, part)
            y -= 15
    c.showPage()
    c.save()
    return buf.getvalue()


def png_bytes(heading: str, lines: list[str], style: str = "document") -> bytes:
    """style: document | sms | screenshot."""
    from PIL import Image, ImageDraw, ImageFont

    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 13)
    except OSError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
        except OSError:
            font = ImageFont.load_default()
    wrapped: list[str] = []
    width_chars = 44 if style == "sms" else 80
    for line in lines:
        wrapped.extend(textwrap.wrap(line, width_chars) or [""])
    W = 420 if style == "sms" else 760
    H = 70 + 16 * len(wrapped) + 30
    bg = (236, 239, 244) if style == "sms" else (255, 255, 255)
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 40], fill=(40, 52, 72) if style != "document" else (230, 230, 230))
    d.text((12, 14), heading, fill=(255, 255, 255) if style != "document" else (0, 0, 0), font=font)
    y = 56
    if style == "sms":
        d.rounded_rectangle([10, 50, W - 40, 60 + 16 * len(wrapped)], radius=10, fill=(255, 255, 255))
    for line in wrapped:
        d.text((20, y), line, fill=(20, 20, 20), font=font)
        y += 16
    d.text((12, H - 22), "SYNTHETIC - fictional exercise material", fill=(120, 120, 120), font=font)
    out = io.BytesIO()
    img.save(out, format="PNG", optimize=True)
    return out.getvalue()
