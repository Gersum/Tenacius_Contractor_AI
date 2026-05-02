from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "memo.md"
OUTPUT = ROOT / "memo.pdf"

PAGE_MARKERS = ("[[PAGE 1]]", "[[PAGE 2]]")
TITLE = "Tenacious-Bench Final Memo"
MARGIN = 54
WIDTH, HEIGHT = LETTER
BODY_FONT = "Helvetica"
BODY_SIZE = 10.5
LINE_GAP = 3.5
HEADER_SIZE = 18
SECTION_SIZE = 12.5
PAGE_LABEL_SIZE = 12


def _split_pages(text: str) -> list[list[str]]:
    markers = list(PAGE_MARKERS)
    positions = []
    for marker in markers:
        pos = text.find(marker)
        if pos == -1:
            raise ValueError(f"Missing page marker: {marker}")
        positions.append((marker, pos))
    positions.sort(key=lambda item: item[1])

    pages: list[list[str]] = []
    for idx, (marker, start) in enumerate(positions):
        content_start = start + len(marker)
        content_end = positions[idx + 1][1] if idx + 1 < len(positions) else len(text)
        body = text[content_start:content_end].strip("\n")
        pages.append(body.splitlines())
    return pages


def _draw_wrapped(c: canvas.Canvas, text: str, x: float, y: float, width: float, *, font: str, size: float) -> float:
    c.setFont(font, size)
    avg_char_width = pdfmetrics.stringWidth("abcdefghijklmnopqrstuvwxyz", font, size) / 26
    max_chars = max(25, int(width / max(avg_char_width, 0.1)))
    lines = wrap(text, width=max_chars, break_long_words=False, break_on_hyphens=False)
    for line in lines:
        c.drawString(x, y, line)
        y -= size + LINE_GAP
    return y


def render() -> Path:
    text = SOURCE.read_text()
    lines = [line.rstrip() for line in text.splitlines()]
    if not lines or lines[0].strip() != TITLE:
        raise ValueError("memo.md must begin with the expected title line.")

    pages = _split_pages(text)
    if len(pages) != 2:
        raise ValueError(f"Expected exactly 2 pages in memo.md, found {len(pages)}.")

    c = canvas.Canvas(str(OUTPUT), pagesize=LETTER)

    for index, page_lines in enumerate(pages, start=1):
        y = HEIGHT - MARGIN
        c.setTitle(TITLE)
        c.setFont("Helvetica-Bold", HEADER_SIZE)
        c.drawString(MARGIN, y, TITLE)
        y -= HEADER_SIZE + 6

        c.setFont("Helvetica-Bold", PAGE_LABEL_SIZE)
        c.drawString(MARGIN, y, page_lines[0])
        y -= PAGE_LABEL_SIZE + 8

        for raw in page_lines[1:]:
            line = raw.strip()
            if not line:
                y -= BODY_SIZE + 2
                continue
            if y < MARGIN + 40:
                raise ValueError(f"Page {index} overflowed; tighten memo content.")
            if line == "Executive summary" or line == "Decision details" or line == "Production recommendation" or line == "Evidence anchors" or line == "What Tenacious-Bench v0.1 still does not capture" or line == "Public-signal lossiness" or line == "Honest unresolved training failure" or line == "Kill-switch trigger":
                c.setFont("Helvetica-Bold", SECTION_SIZE)
                c.drawString(MARGIN, y, line)
                y -= SECTION_SIZE + 4
                continue
            if line.startswith("- "):
                bullet = u"\u2022 "
                bullet_x = MARGIN + 2
                text_x = MARGIN + 14
                c.setFont(BODY_FONT, BODY_SIZE)
                c.drawString(bullet_x, y, bullet)
                y = _draw_wrapped(c, line[2:], text_x, y, WIDTH - MARGIN - text_x, font=BODY_FONT, size=BODY_SIZE)
                y -= 1
                continue
            y = _draw_wrapped(c, line, MARGIN, y, WIDTH - 2 * MARGIN, font=BODY_FONT, size=BODY_SIZE)
            y -= 2

        c.setFont(BODY_FONT, 9)
        c.drawRightString(WIDTH - MARGIN, MARGIN - 8, f"Page {index} of 2")
        c.showPage()

    c.save()
    return OUTPUT


if __name__ == "__main__":
    path = render()
    print(path)
