"""
PDF report generation using ReportLab.
Replaces the fpdf2 implementation with a properly structured,
multi-section report with cover page, profile summary, and
obligations table grouped by regulation.
"""

from __future__ import annotations

import html
import re
from datetime import date
from io import BytesIO
from typing import Any

from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ── Dimensions ────────────────────────────────────────────────────────────

W, H      = A4
MARGIN    = 20 * mm
CONTENT_W = W - 2 * MARGIN

# ── Colour palette ─────────────────────────────────────────────────────────

C_NAVY      = HexColor("#0a0f1e")
C_NAVY_MID  = HexColor("#0f1729")
C_RULE      = HexColor("#1e2d4a")
C_BLUE      = HexColor("#3d6af5")
C_SLATE     = HexColor("#4a6080")
C_SILVER    = HexColor("#8a9bb8")
C_LIGHT_BG  = HexColor("#f5f7fc")
C_RULE_LIGHT= HexColor("#dde3ef")
C_CRITICAL  = HexColor("#e84040")
C_IMPORTANT = HexColor("#e8a020")
C_INFO      = HexColor("#6b8ef5")
C_MICA      = HexColor("#2db87a")
C_PSD3      = HexColor("#e8a020")

REG_COLORS = {"DORA": C_BLUE, "MiCA": C_MICA, "PSD3": C_PSD3}
SEV_COLORS = {
    "critical":      C_CRITICAL,
    "important":     C_IMPORTANT,
    "informational": C_INFO,
}
REG_NAMES = {
    "DORA": "Digital Operational Resilience Act (EU) 2022/2554",
    "MiCA": "Markets in Crypto-Assets Regulation (EU) 2023/1114",
    "PSD3": "Payment Services Directive 3 — Commission Proposal",
}


# ── Public API ──────────────────────────────────────────────────────────────

def generate_pdf(profile: dict[str, Any], records: list[dict[str, Any]]) -> bytes:
    company  = profile.get("company_name", "Company")
    lt       = profile.get("license_type", "")
    juris    = ", ".join(profile.get("jurisdictions", []))
    today    = date.today().strftime("%d %B %Y")

    total        = len(records)
    critical     = sum(1 for r in records if r["severity"] == "critical")
    important    = sum(1 for r in records if r["severity"] == "important")
    informational= sum(1 for r in records if r["severity"] == "informational")

    # Group by regulation, preserve order
    by_reg: dict[str, list] = {}
    for r in records:
        by_reg.setdefault(r["regulation_id"], []).append(r)

    buf  = BytesIO()
    doc  = _build_doc(buf, company)
    styles = _styles()

    # ── Page callbacks ─────────────────────────────────────────────────────
    def on_cover(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(C_NAVY)
        canvas.rect(0, 0, W, H, fill=1, stroke=0)
        # Blue top strip
        canvas.setFillColor(C_BLUE)
        canvas.rect(0, H - 6 * mm, W, 6 * mm, fill=1, stroke=0)
        # Blue bottom strip
        canvas.rect(0, 0, W, 3 * mm, fill=1, stroke=0)
        canvas.restoreState()

    def on_content(canvas, doc):
        canvas.saveState()
        # Top rule
        canvas.setStrokeColor(C_RULE_LIGHT)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, H - 16 * mm, W - MARGIN, H - 16 * mm)
        # Header text
        canvas.setFont("Helvetica-Bold", 7)
        canvas.setFillColor(C_BLUE)
        canvas.drawString(MARGIN, H - 11 * mm, "REGALITH INTELLIGENCE")
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(C_SLATE)
        label = f"{company} — Regulatory Obligations Report"
        canvas.drawRightString(W - MARGIN, H - 11 * mm, label)
        # Bottom rule
        canvas.line(MARGIN, 16 * mm, W - MARGIN, 16 * mm)
        # Footer
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(C_SLATE)
        canvas.drawCentredString(
            W / 2, 10 * mm,
            "Powered by Regalith Intelligence \u2013 not legal advice"
        )
        canvas.setFillColor(C_SILVER)
        canvas.drawRightString(W - MARGIN, 10 * mm, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    # Attach callbacks to page templates
    doc.pageTemplates[0].onPage = on_cover
    doc.pageTemplates[1].onPage = on_content

    # ── Story ──────────────────────────────────────────────────────────────
    story: list = []

    # 1. Cover
    story += _cover_story(
        company, lt, juris, today,
        total, critical, important, informational,
        by_reg, styles,
    )
    story.append(NextPageTemplate("Content"))
    story.append(PageBreak())

    # 2. Profile summary
    story += _profile_story(profile, today, styles)
    story.append(PageBreak())

    # 3. Obligations grouped by regulation
    story += _obligations_story(by_reg, styles)

    doc.build(story)
    return buf.getvalue()


def pdf_filename(company: str) -> str:
    """Return the formatted filename: CompanyName_RegulatoryProfile_YYYY-MM-DD.pdf"""
    safe = re.sub(r"[^\w]", "_", company)
    safe = re.sub(r"_+", "_", safe).strip("_")[:40]
    return f"{safe}_RegulatoryProfile_{date.today().isoformat()}.pdf"


# ── Document structure ──────────────────────────────────────────────────────

def _build_doc(buf: BytesIO, company: str) -> BaseDocTemplate:
    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        title=f"{company} — Regulatory Obligations Report",
        author="Regalith Intelligence",
        leftMargin=0,
        rightMargin=0,
        topMargin=0,
        bottomMargin=0,
    )

    cover_frame = Frame(
        MARGIN, 20 * mm,
        CONTENT_W, H - 30 * mm,
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
        id="cover",
    )
    content_frame = Frame(
        MARGIN, 20 * mm,
        CONTENT_W, H - 40 * mm,
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
        id="content",
    )

    doc.addPageTemplates([
        PageTemplate(id="Cover",   frames=[cover_frame]),
        PageTemplate(id="Content", frames=[content_frame]),
    ])
    return doc


# ── Styles ─────────────────────────────────────────────────────────────────

def _styles() -> dict[str, ParagraphStyle]:
    base = ParagraphStyle("base", fontName="Helvetica", fontSize=9,
                          leading=13, textColor=C_NAVY)
    return {
        # Cover
        "cover_label": ParagraphStyle(
            "cover_label", parent=base,
            fontName="Helvetica-Bold", fontSize=9,
            textColor=C_BLUE, letterSpacing=2, leading=13,
        ),
        "cover_title": ParagraphStyle(
            "cover_title", parent=base,
            fontName="Helvetica-Bold", fontSize=34,
            textColor=white, leading=40,
        ),
        "cover_company": ParagraphStyle(
            "cover_company", parent=base,
            fontName="Helvetica-Bold", fontSize=18,
            textColor=white, leading=24,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta", parent=base,
            fontSize=9, textColor=C_SLATE, leading=14,
        ),
        # Content headings
        "h1": ParagraphStyle(
            "h1", parent=base,
            fontName="Helvetica-Bold", fontSize=16,
            textColor=C_NAVY, leading=20, spaceAfter=3 * mm,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base,
            fontName="Helvetica-Bold", fontSize=12,
            textColor=C_NAVY, leading=16, spaceBefore=5 * mm, spaceAfter=2 * mm,
        ),
        "section_label": ParagraphStyle(
            "section_label", parent=base,
            fontName="Helvetica-Bold", fontSize=7,
            textColor=C_SLATE, letterSpacing=1.5, leading=11,
            spaceBefore=4 * mm, spaceAfter=1 * mm,
        ),
        "body": ParagraphStyle(
            "body", parent=base,
            fontSize=9, textColor=C_NAVY, leading=14,
        ),
        "body_small": ParagraphStyle(
            "body_small", parent=base,
            fontSize=8, textColor=C_SLATE, leading=12,
        ),
        # Table cells
        "tc": ParagraphStyle(
            "tc", parent=base,
            fontSize=7.5, textColor=C_NAVY, leading=11,
        ),
        "tc_small": ParagraphStyle(
            "tc_small", parent=base,
            fontSize=7, textColor=C_SLATE, leading=10,
        ),
        "tc_bold": ParagraphStyle(
            "tc_bold", parent=base,
            fontName="Helvetica-Bold", fontSize=7.5,
            textColor=C_NAVY, leading=11,
        ),
        # Regulation header in table section
        "reg_name": ParagraphStyle(
            "reg_name", parent=base,
            fontName="Helvetica-Bold", fontSize=11,
            textColor=C_NAVY, leading=16,
        ),
        "reg_count": ParagraphStyle(
            "reg_count", parent=base,
            fontSize=8, textColor=C_SLATE, leading=12, spaceAfter=2 * mm,
        ),
    }


# ── Cover page ──────────────────────────────────────────────────────────────

def _cover_story(
    company, lt, juris, today,
    total, critical, important, informational,
    by_reg, styles,
) -> list:
    s = styles
    items: list = []

    items.append(Spacer(1, 30 * mm))

    items.append(Paragraph("REGALITH INTELLIGENCE", s["cover_label"]))
    items.append(Spacer(1, 8 * mm))

    items.append(Paragraph("Regulatory<br/>Obligations<br/>Report", s["cover_title"]))
    items.append(Spacer(1, 8 * mm))

    items.append(HRFlowable(
        width="100%", thickness=1,
        color=HexColor("#1e2d4a"), spaceAfter=8 * mm,
    ))

    items.append(Paragraph(_esc(company), s["cover_company"]))
    items.append(Spacer(1, 4 * mm))
    items.append(Paragraph(_esc(f"{lt}  ·  {juris}"), s["cover_meta"]))
    items.append(Spacer(1, 2 * mm))
    items.append(Paragraph(f"Date of analysis: {today}", s["cover_meta"]))
    items.append(Spacer(1, 10 * mm))

    # Summary stats table on dark background
    reg_cells = []
    for rid in ("DORA", "MiCA", "PSD3"):
        cnt = len(by_reg.get(rid, []))
        if cnt:
            rc = REG_COLORS.get(rid, C_BLUE)
            reg_cells.append(
                Paragraph(
                    f'<font color="{rc.hexval()}">{cnt}</font><br/>'
                    f'<font color="#4a6080" size="7">{rid}</font>',
                    ParagraphStyle("cc", fontName="Helvetica-Bold",
                                   fontSize=20, leading=24, alignment=TA_CENTER,
                                   textColor=white),
                )
            )

    stat_style = ParagraphStyle(
        "stat", fontName="Helvetica-Bold", fontSize=22,
        leading=26, alignment=TA_CENTER, textColor=white,
    )
    lbl_style = ParagraphStyle(
        "lbl", fontName="Helvetica", fontSize=7,
        leading=10, alignment=TA_CENTER, textColor=C_SLATE,
    )

    def _stat_cell(val, label, color):
        return [
            Paragraph(f'<font color="{color}">{val}</font>', stat_style),
            Paragraph(label, lbl_style),
        ]

    stats_data = [
        [
            _stat_cell(total,         "TOTAL",         "#e8edf5"),
            _stat_cell(critical,      "CRITICAL",      "#e84040"),
            _stat_cell(important,     "IMPORTANT",     "#e8a020"),
            _stat_cell(informational, "INFORMATIONAL", "#6b8ef5"),
        ]
    ]

    stats_t = Table(
        [[cell[0] for cell in stats_data[0]],
         [cell[1] for cell in stats_data[0]]],
        colWidths=[CONTENT_W / 4] * 4,
    )
    stats_t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), C_NAVY),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("LINEABOVE",    (0, 0), (-1, 0),  0.5, HexColor("#1e2d4a")),
        ("LINEBELOW",    (0, -1),(-1, -1), 0.5, HexColor("#1e2d4a")),
    ]))
    items.append(stats_t)

    return items


# ── Profile summary page ────────────────────────────────────────────────────

def _profile_story(profile: dict, today: str, styles: dict) -> list:
    s = styles
    company = profile.get("company_name", "")
    items: list = []

    items.append(Paragraph("Company Profile", s["h1"]))
    items.append(HRFlowable(
        width="100%", thickness=0.5, color=C_RULE_LIGHT, spaceAfter=4 * mm,
    ))

    rows = [
        ("Company name",       profile.get("company_name", "")),
        ("Licence type",       profile.get("license_type", "")),
        ("Jurisdictions",      ", ".join(profile.get("jurisdictions", []))),
        ("Products offered",   ", ".join(profile.get("products", []))),
        ("Customer segments",  ", ".join(profile.get("customer_segments", []))),
        ("Headcount",          profile.get("headcount_range", "")),
        ("Onboarding volume",  profile.get("monthly_onboarding_volume", "")),
        ("KYC / AML function", profile.get("kyc_aml_function", "")),
        ("Remote onboarding",  "Yes" if profile.get("has_remote_onboarding") else "No"),
        ("Crypto in scope",    "Yes" if profile.get("has_crypto") else "No"),
        ("Date of analysis",   today),
    ]

    tdata = [
        [
            Paragraph(_esc(k), s["tc_bold"]),
            Paragraph(_esc(v), s["tc"]),
        ]
        for k, v in rows
    ]

    t = Table(tdata, colWidths=[55 * mm, CONTENT_W - 55 * mm])
    t.setStyle(TableStyle([
        ("ROWBACKGROUNDS",  (0, 0), (-1, -1), [white, C_LIGHT_BG]),
        ("TOPPADDING",      (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",   (0, 0), (-1, -1), 6),
        ("LEFTPADDING",     (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",    (0, 0), (-1, -1), 8),
        ("GRID",            (0, 0), (-1, -1), 0.5, C_RULE_LIGHT),
        ("VALIGN",          (0, 0), (-1, -1), "TOP"),
    ]))
    items.append(t)

    return items


# ── Obligations by regulation ───────────────────────────────────────────────

def _obligations_story(by_reg: dict, styles: dict) -> list:
    s = styles
    items: list = []

    items.append(Paragraph("Full Obligations List", s["h1"]))
    items.append(Paragraph(
        "Grouped by regulation · sorted by severity",
        s["body_small"],
    ))
    items.append(HRFlowable(
        width="100%", thickness=0.5, color=C_RULE_LIGHT, spaceAfter=6 * mm,
    ))

    for reg_id in ("DORA", "MiCA", "PSD3"):
        regs = by_reg.get(reg_id, [])
        if not regs:
            continue

        rc     = REG_COLORS.get(reg_id, C_BLUE)
        rcHex  = rc.hexval()
        rname  = REG_NAMES.get(reg_id, reg_id)

        # Regulation section header
        header_block = [
            Paragraph(
                f'<font color="{rcHex}"><b>{reg_id}</b></font>'
                f' <font color="#0a0f1e">— {_esc(rname)}</font>',
                s["reg_name"],
            ),
            Paragraph(
                f'{len(regs)} obligation{"s" if len(regs) != 1 else ""}',
                s["reg_count"],
            ),
        ]
        items += header_block

        # Table
        items.append(_obligation_table(regs, rc, s))
        items.append(Spacer(1, 8 * mm))

    return items


def _obligation_table(records: list, reg_color, styles: dict) -> Table:
    s = styles

    # Sort: critical → important → informational, then by article number
    sev_ord = {"critical": 0, "important": 1, "informational": 2}
    records = sorted(records, key=lambda r: (
        sev_ord.get(r["severity"], 9),
        _art_num(r["article_reference"]),
    ))

    # Column widths: Article | Obligation | Deadline | Severity
    cw = [28 * mm, 88 * mm, 30 * mm, 24 * mm]

    # Header row
    def _th(text):
        return Paragraph(text, ParagraphStyle(
            "th", fontName="Helvetica-Bold", fontSize=7,
            textColor=C_SLATE, leading=10,
        ))

    rows = [[_th("ARTICLE"), _th("OBLIGATION"), _th("DEADLINE"), _th("SEVERITY")]]

    for rec in records:
        sev      = rec.get("severity", "informational")
        sc       = SEV_COLORS.get(sev, C_SLATE)
        scHex    = sc.hexval()
        rcHex    = reg_color.hexval()

        art_ref  = rec.get("article_reference", "")
        # Article label: strip leading "Article N — " for title, keep ref separate
        lbl      = rec.get("article_label", art_ref)
        title    = lbl.split(" — ", 1)[-1] if " — " in lbl else lbl
        oblig    = rec.get("obligation_summary", "")
        deadline = rec.get("deadline", "")

        art_cell  = Paragraph(
            f'<font color="{rcHex}"><b>{_esc(art_ref)}</b></font>',
            s["tc_bold"],
        )
        oblig_cell = Paragraph(
            f'<b>{_esc(title)}</b><br/>'
            f'<font color="#4a6080" size="6.5">{_esc(oblig)}</font>',
            s["tc"],
        )
        dl_cell   = Paragraph(_esc(_short_dl(deadline)), s["tc_small"])
        sev_cell  = Paragraph(
            f'<font color="{scHex}"><b>{sev.upper()}</b></font>',
            s["tc_bold"],
        )

        rows.append([art_cell, oblig_cell, dl_cell, sev_cell])

    t = Table(rows, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        # Header
        ("BACKGROUND",    (0, 0), (-1, 0),  C_NAVY),
        ("TOPPADDING",    (0, 0), (-1, 0),  6),
        ("BOTTOMPADDING", (0, 0), (-1, 0),  6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        # Alternating data rows
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [white, C_LIGHT_BG]),
        ("TOPPADDING",    (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        # Grid
        ("GRID",          (0, 0), (-1, -1), 0.4, C_RULE_LIGHT),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        # Left border accent
        ("LINEAFTER",     (0, 0), (0, -1),  1.5, reg_color),
    ]))
    return t


# ── Helpers ─────────────────────────────────────────────────────────────────

def _esc(text: str) -> str:
    """Escape text for ReportLab XML paragraphs."""
    return html.escape(str(text), quote=False)


def _art_num(ref: str) -> int:
    m = re.search(r"\d+", ref)
    return int(m.group()) if m else 0


def _short_dl(dl: str) -> str:
    if "TBD" in dl or "expected" in dl:
        return "TBD ~2027"
    if "January 2025" in dl:
        return "17 Jan 2025"
    if "December 2024" in dl:
        return "30 Dec 2024"
    return dl[:18]
