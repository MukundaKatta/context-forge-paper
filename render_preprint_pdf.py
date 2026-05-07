from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "paper.md"
OUTPUT = ROOT / "context-forge-method-article-preprint.pdf"


def clean_inline(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[@[^\]]+\]", "", text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text.strip()


def extract_blocks(markdown: str) -> list[tuple[str, object]]:
    lines = markdown.splitlines()
    blocks: list[tuple[str, object]] = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("# "):
            blocks.append(("title", clean_inline(stripped[2:])))
            i += 1
            continue

        if stripped.startswith("## "):
            blocks.append(("h2", clean_inline(stripped[3:])))
            i += 1
            continue

        if stripped.startswith("### "):
            blocks.append(("h3", clean_inline(stripped[4:])))
            i += 1
            continue

        if stripped.startswith("!["):
            blocks.append(("figure_marker", "Workflow figure"))
            i += 1
            continue

        if stripped.startswith("*Figure 1."):
            blocks.append(("caption", clean_inline(stripped.strip("*"))))
            i += 1
            continue

        if stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            blocks.append(("table", table_lines))
            continue

        if stripped.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(clean_inline(lines[i].strip()[2:]))
                i += 1
            blocks.append(("list", items))
            continue

        para_lines = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt:
                i += 1
                break
            if nxt.startswith(("# ", "## ", "### ", "- ", "|", "![", "*Figure 1.")):
                break
            para_lines.append(nxt)
            i += 1
        blocks.append(("p", clean_inline(" ".join(para_lines))))

    return blocks


def make_table(table_lines: list[str], styles) -> Table:
    rows = []
    for raw in table_lines:
        cells = [clean_inline(cell.strip()) for cell in raw.strip("|").split("|")]
        rows.append(cells)
    rows = [row for row in rows if not all(set(cell) <= {"-"} for cell in row)]
    data = [[Paragraph(cell, styles["BodySmall"]) for cell in row] for row in rows]
    table = Table(data, repeatRows=1, colWidths=[1.3 * inch, 1.75 * inch, 1.75 * inch, 2.2 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#18324A")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C8D3E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def build_pdf() -> Path:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="PaperTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#18324A"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Author",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#47627E"),
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyTextPaper",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#202B38"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#202B38"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2Paper",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=colors.HexColor("#18324A"),
            spaceBefore=12,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H3Paper",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=14,
            textColor=colors.HexColor("#18324A"),
            spaceBefore=10,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Caption",
            parent=styles["Italic"],
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#4D637A"),
            spaceAfter=10,
        )
    )

    story = []
    blocks = extract_blocks(SOURCE.read_text())
    title_done = False
    author_done = False

    for kind, payload in blocks:
        if kind == "title" and not title_done:
            story.append(Paragraph(str(payload), styles["PaperTitle"]))
            title_done = True
            continue
        if title_done and not author_done and kind == "p" and str(payload) == "Mukunda Rao Katta":
            story.append(Paragraph(str(payload), styles["Author"]))
            author_done = True
            continue
        if kind == "h2":
            story.append(Paragraph(str(payload), styles["H2Paper"]))
        elif kind == "h3":
            story.append(Paragraph(str(payload), styles["H3Paper"]))
        elif kind == "p":
            story.append(Paragraph(str(payload), styles["BodyTextPaper"]))
        elif kind == "list":
            items = [
                ListItem(Paragraph(item, styles["BodyTextPaper"]), leftIndent=12)
                for item in payload
            ]
            story.append(ListFlowable(items, bulletType="bullet", leftIndent=18))
            story.append(Spacer(1, 0.08 * inch))
        elif kind == "figure_marker":
            story.append(Spacer(1, 0.08 * inch))
            story.append(
                Table(
                    [[Paragraph("Workflow figure included in source package", styles["BodyTextPaper"])]],
                    colWidths=[6.1 * inch],
                )
            )
            story[-1].setStyle(
                TableStyle(
                    [
                        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#8AA4C1")),
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F8FC")),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 14),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                    ]
                )
            )
        elif kind == "caption":
            story.append(Paragraph(str(payload), styles["Caption"]))
        elif kind == "table":
            story.append(make_table(payload, styles))
            story.append(Spacer(1, 0.1 * inch))

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=0.8 * inch,
        leftMargin=0.8 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.8 * inch,
        title="Lightweight Evaluation and Operational Scorecards for Tool-Using AI Agents",
        author="Mukunda Rao Katta",
    )

    def add_page_number(canvas, doc):
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#4D637A"))
        canvas.drawRightString(7.5 * inch, 0.55 * inch, f"Page {doc.page}")

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    return OUTPUT


if __name__ == "__main__":
    pdf = build_pdf()
    print(pdf)
