#!/usr/bin/env python3
"""Write Paper 4 main artwork as dependency-free vector PDFs.

The writer emits PDF drawing primitives directly: text uses Helvetica, while
boxes, axes, bars, and arrows are paths. Values are copied from frozen Paper 4
tables and figure inputs; this script does not rerun an experiment.
"""

from __future__ import annotations

import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FIGURES = ROOT / "figures"


def esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def text(cmd, x, y, value, size=10, bold=False, align="left"):
    width = 0.50 * size * len(value)
    if align == "center":
        x -= width / 2
    elif align == "right":
        x -= width
    font = "/F2" if bold else "/F1"
    color(cmd, "#0f172a")
    cmd.extend(["BT", f"{font} {size:.2f} Tf", f"{x:.2f} {y:.2f} Td", f"({esc(value)}) Tj", "ET"])


def color(cmd, hex_color, stroke=False):
    rgb = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    cmd.append("%.3f %.3f %.3f %s" % (*rgb, "RG" if stroke else "rg"))


def rect(cmd, x, y, w, h, fill=None, stroke="#334155", lw=1.0):
    if fill:
        color(cmd, fill)
    color(cmd, stroke, stroke=True)
    cmd.extend([f"{lw:.2f} w", f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re", "B" if fill else "S"])


def line(cmd, x1, y1, x2, y2, stroke="#475569", lw=1.0, dash=False):
    color(cmd, stroke, stroke=True)
    cmd.append(f"{lw:.2f} w")
    if dash:
        cmd.append("[5 4] 0 d")
    cmd.extend([f"{x1:.2f} {y1:.2f} m", f"{x2:.2f} {y2:.2f} l", "S"])
    if dash:
        cmd.append("[] 0 d")


def arrow(cmd, x1, y1, x2, y2, stroke="#475569", lw=1.4):
    line(cmd, x1, y1, x2, y2, stroke, lw)
    angle = math.atan2(y2 - y1, x2 - x1)
    length = 8
    left = (x2 - length * math.cos(angle - 0.45), y2 - length * math.sin(angle - 0.45))
    right = (x2 - length * math.cos(angle + 0.45), y2 - length * math.sin(angle + 0.45))
    color(cmd, stroke)
    cmd.extend([f"{x2:.2f} {y2:.2f} m", f"{left[0]:.2f} {left[1]:.2f} l", f"{right[0]:.2f} {right[1]:.2f} l", "h", "f"])


def page_pdf(path: Path, width: float, height: float, cmd):
    stream = ("\n".join(cmd) + "\n").encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width:.2f} {height:.2f}] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>".encode("ascii"),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream),
    ]
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out.extend(f"{index} 0 obj\n".encode("ascii"))
        out.extend(obj)
        out.extend(b"\nendobj\n")
    xref = len(out)
    out.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    out.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii"))
    path.write_bytes(out)


def node(cmd, x, y, w, h, title, body, fill):
    rect(cmd, x, y, w, h, fill)
    text(cmd, x + w / 2, y + h - 20, title, 10, True, "center")
    text(cmd, x + w / 2, y + h - 39, body, 8, False, "center")


def fig1():
    c = []
    text(c, 540, 315, "One chain: capability -> evidence -> decision -> support consequence", 15, True, "center")
    text(c, 35, 285, "RQ1 / CAPABILITY", 9, True)
    text(c, 290, 285, "RQ2 / ASSURANCE", 9, True)
    text(c, 860, 285, "RQ3 / CONSEQUENCE", 9, True)
    node(c, 25, 150, 185, 80, "Modern VLM proposal", "high-recall image -> intervals", "#dbeafe")
    node(c, 240, 150, 185, 80, "Independent evidence", "positioned values; page + bbox", "#dcfce7")
    node(c, 455, 150, 185, 80, "Deterministic checks", "units; order; ownership", "#fef3c7")
    node(c, 675, 190, 145, 68, "ACCEPT", "auditable row", "#bbf7d0")
    node(c, 675, 112, 145, 68, "NEEDS REVIEW", "proposal + reason", "#fee2e2")
    node(c, 875, 150, 190, 80, "Database + support", "accepted rows -> support mask", "#e0e7ff")
    arrow(c, 210, 190, 240, 190); arrow(c, 425, 190, 455, 190)
    arrow(c, 640, 190, 675, 224); arrow(c, 640, 190, 675, 146)
    arrow(c, 820, 224, 875, 190); arrow(c, 820, 146, 875, 190)
    rect(c, 455, 45, 185, 55, "#f1f5f9", "#64748b", 1.0)
    text(c, 547, 80, "Legacy recovery", 9, True, "center")
    text(c, 547, 63, "secondary harm analysis only", 7.5, False, "center")
    line(c, 547, 150, 547, 100, "#64748b", 1.0, True)
    text(c, 540, 20, "Dashed branch: legacy sequence reconstruction is secondary harm analysis, not the main assurance path.", 8, False, "center")
    page_pdf(FIGURES / "Figure_1.pdf", 1090, 335, c)


def axes(c, x, y, w, h, ylabel, xlabel, ymax, ticks):
    line(c, x, y, x, y + h, "#334155", 1.0); line(c, x, y, x + w, y, "#334155", 1.0)
    text(c, x - 22, y + h / 2, ylabel, 7, False, "center")
    text(c, x + w / 2, y - 38, xlabel, 7, False, "center")
    for value, label in ticks:
        yy = y + h * value / ymax
        line(c, x, yy, x + w, yy, "#d8dee9", .5)
        text(c, x - 7, yy - 2, label, 6.5, False, "right")


def bar(c, x, y, w, h, value, ymax, fill, label=""):
    rect(c, x, y, w, h * value / ymax, fill, fill, .4)
    if label:
        text(c, x + w / 2, y + h * value / ymax + 4, label, 7, False, "center")


def fig2():
    c = []
    text(c, 540, 420, "Capability and transport are separate evidence questions", 15, True, "center")
    rect(c, 20, 48, 500, 345, None, "#d8dee9", .8); rect(c, 560, 48, 520, 345, None, "#d8dee9", .8)
    text(c, 270, 370, "Familiar source: five record-disjoint cohorts", 10, True, "center")
    text(c, 270, 351, "Published manual-transcription Gold", 8, False, "center")
    text(c, 820, 370, "Source shift: declared evidence tiers", 10, True, "center")
    text(c, 820, 351, "Source-agreement/stress panels; not pooled with Gold", 8, False, "center")
    axes(c, 72, 100, 410, 225, "Boundary-pair interval F1", "cohort", 1.0, [(0,"0"),(.25,".25"),(.5,".50"),(.75,".75"),(1,"1.00")])
    qwen=[.932,.896,.918,.917,.903]; rapid=[.390,.450,.383,.428,.389]
    for i,(a,b,lab) in enumerate(zip(qwen,rapid,["v001","v002","v003","v004","v005"])):
        xx=93+i*78; bar(c,xx,100,22,225,a,1.0,"#2563eb",f"{a:.3f}"); bar(c,xx+27,100,22,225,b,1.0,"#94a3b8"); text(c,xx+23,76,lab,7,False,"center")
    text(c, 120, 330, "Qwen3.8-27B-FP8", 7, False); rect(c,103,326,9,9,"#2563eb","#2563eb",.2)
    text(c, 225, 330, "RapidOCR positioned", 7, False); rect(c,208,326,9,9,"#94a3b8","#94a3b8",.2)
    axes(c, 612, 100, 430, 225, "Boundary-pair interval F1", "source-shift panel", 1.0, [(0,"0"),(.25,".25"),(.5,".50"),(.75,".75"),(1,"1.00")])
    vals=[.577,.679,.857,.038,.041,1.0]; labs=["Swiss Qwen","Swiss OCR","Swiss Tess","BGS OCR","BGS Tess","Raft"]; cols=["#2563eb","#94a3b8","#64748b","#cbd5e1","#cbd5e1","#64748b"]
    for i,(v,lab,col) in enumerate(zip(vals,labs,cols)):
        xx=635+i*65; bar(c,xx,100,38,225,v,1.0,col,f"{v:.3f}"); text(c,xx+19,75,lab,6.5,False,"center")
    page_pdf(FIGURES / "Figure_2.pdf", 1100, 435, c)


def fig3():
    c = []
    text(c, 540, 420, "Selective assurance makes automation utility explicit", 15, True, "center")
    for x,w in [(20,315),(355,315),(690,390)]: rect(c,x,48,w,345,None,"#d8dee9",.8)
    text(c,177,370,"Precision-coverage",10,True,"center"); text(c,512,370,"Complete-record utility",10,True,"center"); text(c,885,370,"Evidence funnel",10,True,"center")
    axes(c,72,100,245,220,"precision","accepted proposals / VLM proposals",1.0,[(.8,".80"),(.9,".90"),(1,"1.00")])
    pts=[(.236,1.0,"v001"),(.287,.979,"v002"),(.244,.993,"v003")]; prev=None
    for cov,pre,lab in pts:
        xx=72+245*cov; yy=100+220*(pre-.8)/.2
        if prev: line(c,prev[0],prev[1],xx,yy,"#16a34a",2)
        rect(c,xx-3,yy-3,6,6,"#16a34a","#16a34a",.2)
        offset = {"v001": 8, "v002": -12, "v003": 10}[lab]
        text(c,xx+8,yy+offset,lab,7); prev=(xx,yy)
    text(c,72+245*.244+8,100+220*(.993-.8)/.2-13,"0.993",7)
    axes(c,407,100,220,220,"documents auto-accepted (%)","cohort",100,[(0,"0"),(25,"25"),(50,"50"),(75,"75"),(100,"100")])
    for i,lab in enumerate(["v001","v002","v003"]): bar(c,445+i*55,100,28,220,4,100,"#f59e0b","4%" ); text(c,459+i*55,80,lab,7,False,"center")
    axes(c,742,100,300,220,"count (held-out v003)","funnel stage",2000,[(0,"0"),(500,"500"),(1000,"1000"),(1500,"1500"),(2000,"2000")])
    vals=[1833,1450,447,4]; labs=["proposals","both endpoints","owned + accepted","complete docs"]; cols=["#2563eb","#60a5fa","#16a34a","#f59e0b"]
    for i,(v,lab,col) in enumerate(zip(vals,labs,cols)):
        xx=770+i*68; bar(c,xx,100,42,220,v,2000,col,str(v)); text(c,xx+21,76,lab,6.5,False,"center")
    text(c,742,30,"Endpoint fields anchored: 3099/3666; interval anchors: 1450/1833",7,False)
    page_pdf(FIGURES / "Figure_3.pdf", 1100, 435, c)


def fig4():
    c = []
    text(c, 540, 420, "Abstention changes the geoscientific observation set", 15, True, "center")
    for x,w in [(20,350),(390,300),(710,370)]: rect(c,x,48,w,345,None,"#d8dee9",.8)
    text(c,195,370,"Distinct estimands",10,True,"center"); text(c,540,370,"Retained support area",10,True,"center"); text(c,895,370,"Support spacing",10,True,"center")
    axes(c,72,100,275,220,"volume discrepancy","variant",.2,[(0,"0"),(.05,".05"),(.1,".10"),(.15,".15"),(.2,".20")])
    full=[.1387,.1213,.0821]; matched=[.0326,.0754,.0754]
    for i,(a,b,lab) in enumerate(zip(full,matched,["raw","reread","risk"])):
        xx=102+i*87; bar(c,xx,100,24,220,a,.2,"#64748b",f"{a:.4f}"); bar(c,xx+30,100,24,220,b,.2,"#2563eb",f"{b:.4f}"); text(c,xx+27,78,lab,7,False,"center")
    axes(c,442,100,190,220,"hull area ratio","variant",1.0,[(0,"0"),(.25,".25"),(.5,".50"),(.75,".75"),(1,"1.00")])
    bar(c,485,100,42,220,1.0,1.0,"#64748b","1.000"); bar(c,550,100,42,220,.636,1.0,"#dc2626",".636"); text(c,506,78,"raw",7,False,"center"); text(c,571,78,"risk-aware",7,False,"center")
    axes(c,760,100,275,220,"distance (km)","support metric",5.0,[(0,"0"),(1,"1"),(2,"2"),(3,"3"),(4,"4"),(5,"5")])
    bar(c,803,100,24,220,1.387,5,"#64748b","1.39"); bar(c,830,100,24,220,3.479,5,"#dc2626","3.48"); text(c,817,78,"Mean NN",6.5,False,"center")
    bar(c,935,100,24,220,2.745,5,"#64748b","2.75"); bar(c,962,100,24,220,4.619,5,"#dc2626","4.62"); text(c,949,78,"Mean grid",6.5,False,"center")
    text(c,760,30,"Full-support and matched-support are different estimands.",7,False)
    page_pdf(FIGURES / "Figure_4.pdf", 1100, 435, c)


def graphical_abstract():
    c = []
    text(c, 500, 285, "From visual extraction to trustworthy database ingestion", 15, True, "center")
    node(c, 25, 115, 135, 70, "Borehole page", "visual record", "#e2e8f0")
    node(c, 205, 115, 135, 70, "VLM proposal", "high recall", "#dbeafe")
    node(c, 385, 115, 145, 70, "Independent evidence", "page + bbox", "#dcfce7")
    node(c, 590, 155, 115, 55, "ACCEPT", "auditable row", "#bbf7d0")
    node(c, 590, 90, 115, 55, "REVIEW", "preserve reason", "#fee2e2")
    node(c, 765, 115, 205, 70, "Database + spatial support", "support mask", "#e0e7ff")
    arrow(c, 160, 150, 205, 150); arrow(c, 340, 150, 385, 150)
    arrow(c, 530, 150, 590, 182); arrow(c, 530, 150, 590, 118)
    arrow(c, 705, 182, 765, 150); arrow(c, 705, 118, 765, 150)
    text(c, 500, 35, "0.993 precision @ 24.4% proposal coverage  |  4/100 complete documents auto-accepted", 9, False, "center")
    # Keep the vector export proportional to the 1800x720 PNG (2.5:1),
    # matching the journal's 1328x531 graphical-abstract geometry.
    page_pdf(FIGURES / "graphical_abstract.pdf", 1000, 400, c)


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig1(); fig2(); fig3(); fig4(); graphical_abstract()
    print("Wrote vector PDFs for Figure_1 through Figure_4 and graphical abstract")


if __name__ == "__main__":
    main()
