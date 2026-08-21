#!/usr/bin/env python3
"""Build embedded-font vector artwork for Paper 4.

The artwork is generated with ReportLab primitives only. No source-page
images are used, and all values are copied from the frozen publication tables.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parent
FIGURES = ROOT / "figures"
MIN_VECTOR_FONT = 0.0


def register_fonts() -> None:
    configured = os.environ.get("GEOLOGPARSER_DEJAVU_FONT_DIR")
    candidates = [Path(configured)] if configured else []
    candidates.extend(
        [
            Path(r"C:\Windows\Fonts"),
            Path(r"C:\Users\lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\share\fonts"),
            Path("/usr/share/fonts/truetype/dejavu"),
            Path("/usr/local/share/fonts/truetype/dejavu"),
            Path("/usr/share/fonts/dejavu"),
            Path.home() / ".fonts",
        ]
    )
    regular = next((p / "DejaVuSans.ttf" for p in candidates if (p / "DejaVuSans.ttf").exists()), None)
    bold = next((p / "DejaVuSans-Bold.ttf" for p in candidates if (p / "DejaVuSans-Bold.ttf").exists()), None)
    if regular is None or bold is None:
        raise FileNotFoundError("DejaVu Sans fonts are required for embedded vector artwork")
    pdfmetrics.registerFont(TTFont("PaperSans", str(regular)))
    pdfmetrics.registerFont(TTFont("PaperSans-Bold", str(bold)))


def rgb(hex_color: str) -> tuple[float, float, float]:
    return tuple(int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5))


def set_fill(c: canvas.Canvas, color: str) -> None:
    c.setFillColorRGB(*rgb(color))


def set_stroke(c: canvas.Canvas, color: str, width: float = 1.0) -> None:
    c.setStrokeColorRGB(*rgb(color))
    c.setLineWidth(width)


def draw_text(c: canvas.Canvas, x: float, y: float, value: str, size: float = 10,
              bold: bool = False, align: str = "left", color: str = "#0f172a") -> None:
    size = max(size, MIN_VECTOR_FONT)
    c.setFont("PaperSans-Bold" if bold else "PaperSans", size)
    set_fill(c, color)
    if align == "center":
        c.drawCentredString(x, y, value)
    elif align == "right":
        c.drawRightString(x, y, value)
    else:
        c.drawString(x, y, value)


def draw_multiline(c: canvas.Canvas, x: float, y: float, value: str, size: float = 10,
                   bold: bool = False, color: str = "#0f172a", leading: float | None = None) -> None:
    size = max(size, MIN_VECTOR_FONT)
    leading = max(leading or 0, size * 1.15)
    for index, line_value in enumerate(value.split("\n")):
        draw_text(c, x, y - index * leading, line_value, size, bold, "center", color)


def box(c: canvas.Canvas, x: float, y: float, w: float, h: float, fill: str,
        stroke: str = "#334155", width: float = 1.0) -> None:
    set_fill(c, fill)
    set_stroke(c, stroke, width)
    c.rect(x, y, w, h, fill=1, stroke=1)


def line(c: canvas.Canvas, x1: float, y1: float, x2: float, y2: float,
         stroke: str = "#475569", width: float = 1.0, dash: bool = False) -> None:
    set_stroke(c, stroke, width)
    c.setDash(5, 4) if dash else c.setDash()
    c.line(x1, y1, x2, y2)
    c.setDash()


def arrow(c: canvas.Canvas, x1: float, y1: float, x2: float, y2: float,
          stroke: str = "#475569", width: float = 1.4) -> None:
    line(c, x1, y1, x2, y2, stroke, width)
    angle = math.atan2(y2 - y1, x2 - x1)
    length = 9
    left = (x2 - length * math.cos(angle - 0.45), y2 - length * math.sin(angle - 0.45))
    right = (x2 - length * math.cos(angle + 0.45), y2 - length * math.sin(angle + 0.45))
    set_fill(c, stroke)
    path = c.beginPath()
    path.moveTo(x2, y2)
    path.lineTo(*left)
    path.lineTo(*right)
    path.close()
    c.drawPath(path, fill=1, stroke=0)


def new_page(path: Path, width: float, height: float) -> canvas.Canvas:
    return canvas.Canvas(
        str(path),
        pagesize=(width, height),
        pageCompression=1,
        initialFontName="PaperSans",
        initialFontSize=10,
    )


def finish(c: canvas.Canvas) -> None:
    c.showPage()
    c.save()


def node(c: canvas.Canvas, x: float, y: float, w: float, h: float, title: str,
         body: str, fill: str) -> None:
    box(c, x, y, w, h, fill)
    title_lines = title.split("\n")
    title_leading = 20
    title_y = y + h - 22
    draw_multiline(c, x + w / 2, title_y, title, 11, True, "#0f172a", title_leading)
    body_y = title_y - title_leading * (len(title_lines) - 1) - 22
    draw_multiline(c, x + w / 2, body_y, body, 9, False, "#334155", 17)


def fig1() -> None:
    global MIN_VECTOR_FONT
    MIN_VECTOR_FONT = 18.0
    c = new_page(FIGURES / "Figure_1.pdf", 1090, 360)
    draw_text(c, 545, 332, "One chain: capability -> evidence -> decision -> support consequence", 15, True, "center")
    draw_text(c, 35, 300, "RQ1 / CAPABILITY", 10, True, color="#1d4ed8")
    draw_text(c, 290, 300, "RQ2 / ASSURANCE", 10, True, color="#15803d")
    draw_text(c, 860, 300, "RQ3 / CONSEQUENCE", 10, True, color="#4338ca")
    node(c, 25, 160, 185, 82, "Modern VLM", "high-recall proposal\nimage -> intervals", "#dbeafe")
    node(c, 240, 160, 185, 82, "Independent", "evidence\npage + bbox", "#dcfce7")
    node(c, 455, 160, 185, 82, "Structural checks", "units; order\ncolumn ownership", "#fef3c7")
    node(c, 655, 202, 185, 70, "ACCEPT", "auditable row", "#bbf7d0")
    node(c, 655, 112, 185, 80, "NEEDS\nREVIEW", "proposal + reason", "#fee2e2")
    node(c, 860, 160, 220, 82, "Database + support", "accepted rows ->\nsupport mask", "#e0e7ff")
    arrow(c, 210, 201, 240, 201); arrow(c, 425, 201, 455, 201)
    arrow(c, 640, 201, 655, 237); arrow(c, 640, 201, 655, 152)
    arrow(c, 840, 237, 860, 201); arrow(c, 840, 152, 860, 201)
    box(c, 455, 52, 185, 58, "#f1f5f9", "#64748b")
    draw_text(c, 547, 84, "Legacy recovery", 10, True, "center")
    draw_text(c, 547, 65, "harm analysis only", 8.5, False, "center", "#334155")
    line(c, 547, 160, 547, 110, "#64748b", 1.0, True)
    draw_text(c, 545, 25, "Dashed branch: legacy sequence reconstruction is secondary harm analysis, not the main assurance path.", 9, False, "center", "#475569")
    finish(c)


def axes(c: canvas.Canvas, x: float, y: float, w: float, h: float, ylabel: str,
         xlabel: str, ymax: float, ticks: list[tuple[float, str]], ymin: float = 0.0) -> None:
    line(c, x, y, x, y + h, "#334155", 1.0)
    line(c, x, y, x + w, y, "#334155", 1.0)
    c.saveState()
    c.translate(x - 43, y + h / 2)
    c.rotate(90)
    draw_text(c, 0, 0, ylabel, 9, False, "center")
    c.restoreState()
    draw_text(c, x + w / 2, y - 36, xlabel, 9, False, "center")
    for value, label in ticks:
        yy = y + h * (value - ymin) / (ymax - ymin)
        line(c, x, yy, x + w, yy, "#d8dee9", 0.45)
        draw_text(c, x - 7, yy - 3, label, 8.5, False, "right", "#334155")


def bar(c: canvas.Canvas, x: float, y: float, w: float, h: float, value: float,
        ymax: float, fill: str, label: str = "", hatch: bool = False) -> None:
    height = h * value / ymax
    box(c, x, y, w, height, fill, fill, 0.35)
    if hatch:
        set_stroke(c, "#ffffff", 0.7)
        start = x - height
        while start < x + w:
            c.line(start, y, start + height, y + height)
            start += 7
    if label:
        draw_text(c, x + w / 2, y + height + 6, label, 8.5, False, "center")


def fig2() -> None:
    global MIN_VECTOR_FONT
    MIN_VECTOR_FONT = 18.0
    c = new_page(FIGURES / "Figure_2.pdf", 1100, 560)
    draw_text(c, 550, 532, "Capability and transport are separate evidence questions", 15, True, "center")
    draw_text(c, 250, 495, "Familiar source: five record-disjoint cohorts", 11, True, "center")
    draw_text(c, 250, 468, "Published manual-transcription Gold", 9.5, False, "center", "#334155")
    draw_text(c, 780, 495, "Source shift: declared evidence tiers", 11, True, "center")
    draw_text(c, 780, 468, "Source-agreement/stress panels; not pooled with Gold", 9.5, False, "center", "#334155")
    axes(c, 70, 100, 360, 280, "Boundary-pair interval F1", "", 1.0,
         [(0, "0"), (.25, ".25"), (.5, ".50"), (.75, ".75"), (1, "1.00")])
    qwen = [.932, .896, .918, .917, .903]
    rapid = [.390, .450, .383, .428, .389]
    for i, (a, b, lab) in enumerate(zip(qwen, rapid, ["v001", "v002", "v003", "v004", "v005"])):
        xx = 90 + i * 65
        bar(c, xx, 100, 21, 280, a, 1.0, "#2563eb", f"{a:.3f}")
        bar(c, xx + 27, 100, 21, 280, b, 1.0, "#94a3b8")
        draw_text(c, xx + 24, 70, lab, 9, False, "center")
    box(c, 90, 430, 14, 14, "#2563eb", "#2563eb", .2)
    draw_text(c, 114, 429, "Qwen3.8-27B-FP8", 9, False)
    box(c, 90, 402, 14, 14, "#94a3b8", "#94a3b8", .2)
    draw_text(c, 114, 401, "RapidOCR positioned", 9, False)
    axes(c, 520, 100, 520, 280, "Boundary-pair interval F1", "", 1.0,
         [(0, "0"), (.25, ".25"), (.5, ".50"), (.75, ".75"), (1, "1.00")])
    vals = [.577, .679, .857, .038, .041, 1.0]
    labs = ["Qwen", "RapidOCR", "Tess.", "RapidOCR", "Tess.", "RapidOCR"]
    cols = ["#2563eb", "#94a3b8", "#64748b", "#cbd5e1", "#cbd5e1", "#64748b"]
    for i, (v, lab, col) in enumerate(zip(vals, labs, cols)):
        xx = 540 + i * 82
        bar(c, xx, 100, 45, 280, v, 1.0, col, f"{v:.3f}")
        draw_text(c, xx + 22, 70, lab, 8.2, False, "center")
    draw_text(c, 644, 40, "Swissgeol", 8.5, True, "center", "#334155")
    draw_text(c, 849, 40, "BGS", 8.5, True, "center", "#334155")
    draw_text(c, 972, 40, "Raft River", 8.5, True, "center", "#334155")
    line(c, 765, 34, 765, 88, "#d8dee9", 0.6)
    line(c, 930, 34, 930, 88, "#d8dee9", 0.6)
    finish(c)


def fig3() -> None:
    global MIN_VECTOR_FONT
    MIN_VECTOR_FONT = 18.0
    c = new_page(FIGURES / "Figure_3.pdf", 1100, 780)
    draw_text(c, 550, 752, "Selective assurance makes automation utility explicit", 15, True, "center")
    draw_text(c, 270, 705, "Precision versus proposal coverage", 11, True, "center")
    draw_text(c, 820, 705, "Complete-document utility", 11, True, "center")
    axes(c, 70, 490, 390, 170, "Selective precision", "", 1.0,
         [(0.8, ".80"), (.9, ".90"), (1.0, "1.00")], ymin=.8)
    for value, label in [(0, "0"), (.25, ".25"), (.5, ".50"), (.75, ".75"), (1, "1.00")]:
        xx = 70 + 390 * value
        line(c, xx, 490, xx, 484, "#334155", 1.0)
        draw_text(c, xx, 467, label, 8.5, False, "center", "#334155")
    draw_text(c, 265, 438, "proposal coverage (accepted / proposed)", 9, False, "center")
    points = [(.236, 1.0, "v001"), (.287, .979, "v002"), (.244, .993, "v003")]
    previous = None
    for cov, pre, label in points:
        xx = 70 + 390 * cov
        yy = 490 + 170 * (pre - .8) / .2
        if previous:
            line(c, previous[0], previous[1], xx, yy, "#16a34a", 2)
        set_fill(c, "#16a34a")
        c.circle(xx, yy, 5, fill=1, stroke=0)
        label_offsets = {"v001": (18, 13), "v002": (24, -25), "v003": (55, -2)}
        dx, dy = label_offsets[label]
        draw_text(c, xx + dx, yy + dy, label, 9)
        previous = (xx, yy)
    set_stroke(c, "#64748b", 1.4)
    c.setDash(3, 2)
    c.line(70 + 390, 490, 70 + 390, 490 + 170 * (.907 - .8) / .2)
    c.setDash()
    set_fill(c, "#64748b")
    c.circle(70 + 390, 490 + 170 * (.907 - .8) / .2, 5, fill=0, stroke=1)
    draw_text(c, 70 + 390 - 4, 490 + 170 * (.907 - .8) / .2 + 12, "raw baseline", 9, False, "right")
    axes(c, 610, 490, 390, 170, "Documents auto-accepted (%)", "", 100,
         [(0, "0"), (25, "25"), (50, "50"), (75, "75"), (100, "100")])
    for i, lab in enumerate(["v001", "v002", "v003"]):
        bar(c, 680 + i * 82, 490, 35, 170, 4, 100, "#f59e0b", "4%")
        draw_text(c, 697 + i * 82, 462, lab, 9, False, "center")
    draw_text(c, 550, 405, "Evidence funnel (held-out v003)", 11, True, "center")
    line(c, 320, 100, 320, 340, "#334155", 1.0)
    for value in (0, 500, 1000, 1500, 2000):
        xx = 320 + 560 * value / 2000
        line(c, xx, 100, xx, 340, "#d8dee9", 0.45)
        draw_text(c, xx, 75, str(value), 8.5, False, "center", "#334155")
    values = [1833, 1450, 447, 4]
    stages = ["VLM interval proposals", "Both endpoints anchored", "Owned and accepted", "Complete documents"]
    colors = ["#2563eb", "#60a5fa", "#16a34a", "#f59e0b"]
    for i, (value, stage, color) in enumerate(zip(values, stages, colors)):
        yy = 122 + i * 52
        set_fill(c, color)
        c.roundRect(320, yy, 560 * value / 2000, 30, 3, fill=1, stroke=0)
        draw_text(c, 920, yy + 8, str(value), 10)
        draw_text(c, 285, yy + 8, stage, 9, False, "right", "#334155")
    draw_text(c, 300, 56, "Endpoint fields anchored: 3099/3666; interval anchors: 1450/1833", 9, False, color="#475569")
    finish(c)


def fig4() -> None:
    global MIN_VECTOR_FONT
    MIN_VECTOR_FONT = 18.0
    c = new_page(FIGURES / "Figure_4.pdf", 1100, 560)
    draw_text(c, 550, 532, "Abstention changes the geoscientific observation set", 15, True, "center")
    draw_text(c, 220, 492, "Distinct estimands", 11, True, "center")
    draw_text(c, 550, 492, "Support retained", 11, True, "center")
    draw_text(c, 875, 492, "Support spacing", 11, True, "center")
    axes(c, 70, 120, 285, 300, "Volume discrepancy", "", .2,
         [(0, "0"), (.05, ".05"), (.1, ".10"), (.15, ".15"), (.2, ".20")])
    labels = ["raw", "reread", "risk"]
    full = [.1387, .1213, .0821]
    matched = [.0326, .0754, .0754]
    method_colors = ["#64748b", "#2563eb", "#dc2626"]
    for i, (a, b, label, color) in enumerate(zip(full, matched, labels, method_colors)):
        xx = 100 + i * 87
        bar(c, xx, 120, 24, 300, a, .2, color, "")
        bar(c, xx + 30, 120, 24, 300, b, .2, color, "", hatch=True)
        draw_text(c, xx + 12, 120 + 300 * a / .2 + 22, f"{a:.4f}", 8.5, False, "center")
        draw_text(c, xx + 42, 120 + 300 * b / .2 + 16, f"{b:.4f}", 8.5, False, "center")
        draw_text(c, xx + 27, 98, label, 9, False, "center")
    box(c, 85, 455, 14, 14, "#64748b", "#64748b", .2)
    draw_text(c, 108, 454, "Full-support", 8.5, False)
    box(c, 85, 430, 14, 14, "#ffffff", "#64748b", .8)
    line(c, 86, 431, 98, 443, "#64748b", .8)
    line(c, 86, 437, 92, 443, "#64748b", .8)
    draw_text(c, 108, 429, "Matched-subset (15 docs)", 8.5, False)
    axes(c, 450, 120, 180, 300, "Hull area ratio", "", 1.0,
         [(0, "0"), (.25, ".25"), (.5, ".50"), (.75, ".75"), (1, "1.00")])
    bar(c, 490, 120, 42, 300, 1.0, 1.0, "#64748b", "1.000")
    bar(c, 555, 120, 42, 300, .636, 1.0, "#dc2626", ".636")
    draw_text(c, 511, 98, "raw", 9, False, "center")
    draw_multiline(c, 576, 98, "risk-\naware", 9, False, leading=10)
    axes(c, 750, 120, 285, 300, "Distance (km)", "", 5.0,
         [(0, "0"), (1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")])
    bar(c, 795, 120, 24, 300, 1.387, 5, "#64748b", "1.39")
    bar(c, 823, 120, 24, 300, 3.479, 5, "#dc2626", "3.48")
    bar(c, 930, 120, 24, 300, 2.745, 5, "#64748b", "2.75")
    bar(c, 958, 120, 24, 300, 4.619, 5, "#dc2626", "4.62")
    draw_multiline(c, 821, 98, "Nearest\nneighbour\nmean", 8.5, False, leading=10)
    draw_multiline(c, 956, 98, "Grid-to\nobservation\nmean", 8.5, False, leading=10)
    draw_text(c, 550, 35, "Full-support and matched-support are different estimands.", 9, False, "center", "#475569")
    finish(c)


def graphical_abstract() -> None:
    global MIN_VECTOR_FONT
    MIN_VECTOR_FONT = 0.0
    c = new_page(FIGURES / "graphical_abstract.pdf", 1000, 400)
    draw_text(c, 500, 365, "From visual extraction to trustworthy database ingestion", 15, True, "center")
    node(c, 25, 150, 135, 72, "Borehole page", "visual record", "#e2e8f0")
    node(c, 205, 150, 135, 72, "VLM proposal", "high recall", "#dbeafe")
    node(c, 385, 150, 145, 72, "Independent evidence", "page + bbox", "#dcfce7")
    node(c, 590, 190, 115, 56, "ACCEPT", "auditable row", "#bbf7d0")
    node(c, 590, 126, 115, 56, "NEEDS REVIEW", "preserve reason", "#fee2e2")
    node(c, 765, 150, 205, 72, "Database + spatial support", "support mask", "#e0e7ff")
    arrow(c, 160, 186, 205, 186); arrow(c, 340, 186, 385, 186)
    arrow(c, 530, 186, 590, 218); arrow(c, 530, 186, 590, 154)
    arrow(c, 705, 218, 765, 186); arrow(c, 705, 154, 765, 186)
    draw_text(c, 500, 48, "0.993 precision @ 24.4% proposal coverage  |  4/100 complete documents auto-accepted", 10, False, "center", "#334155")
    finish(c)


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    register_fonts()
    fig1()
    fig2()
    fig3()
    fig4()
    graphical_abstract()
    print("Wrote embedded-font vector PDFs for Figure_1 through Figure_4 and graphical abstract")


if __name__ == "__main__":
    main()
