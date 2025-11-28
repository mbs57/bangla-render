# bangla_render/renderer.py
import sys
from PySide6.QtGui import QImage, QPainter, QFont, QColor, QFontMetrics
from PySide6.QtCore import Qt, QRect
from PySide6.QtWidgets import QApplication


def _ensure_app():
    """Ensure a Qt application exists (required for rendering)."""
    return QApplication.instance() or QApplication(sys.argv)


def render_text(
    text,
    width=800,
    height=200,
    font_family="Noto Sans Bengali",
    font_size=48,
    output_path="bangla_text.png",
    color="black",
    bg="white",   # use "transparent" for no background
):
    _ensure_app()

    img = QImage(width, height, QImage.Format.Format_ARGB32)

    if bg == "transparent":
        img.fill(Qt.GlobalColor.transparent)
    else:
        img.fill(QColor(bg))

    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)

    font = QFont(font_family, font_size)
    painter.setFont(font)
    painter.setPen(QColor(color))

    # draw roughly centered vertically
    x = 10
    y = height // 2 + font_size // 2 - 5
    painter.drawText(x, y, text)

    painter.end()
    img.save(output_path)
    return output_path


def render_paragraph(
    text,
    width=800,
    height=300,
    font_family="Noto Sans Bengali",
    font_size=28,
    output_path="bangla_paragraph.png",
    align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
    color="black",
    bg="white",
    margin=40,
):
    _ensure_app()

    img = QImage(width, height, QImage.Format.Format_ARGB32)
    img.fill(QColor(bg))

    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)

    font = QFont(font_family, font_size)
    painter.setFont(font)
    painter.setPen(QColor(color))

    rect = QRect(margin, margin, width - 2 * margin, height - 2 * margin)
    flags = Qt.TextFlag.TextWordWrap | align

    painter.drawText(rect, int(flags), text)
    painter.end()

    img.save(output_path)
    return output_path


def render_text_qimage(
    text,
    font_family="Noto Sans Bengali",
    font_size=48,
    color="black",
    padding=10,
):
    """
    Render text to a transparent QImage, tightly cropped with padding.
    Used internally by the Matplotlib helpers.
    """
    _ensure_app()

    font = QFont(font_family, font_size)
    fm = QFontMetrics(font)

    rect = fm.boundingRect(text)

    w = rect.width() + 2 * padding
    h = rect.height() + 2 * padding

    img = QImage(w, h, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)

    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)
    painter.setFont(font)
    painter.setPen(QColor(color))

    x = padding - rect.left()
    y = padding - rect.top()
    painter.drawText(x, y, text)

    painter.end()
    return img
