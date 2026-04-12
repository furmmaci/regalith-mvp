"""
PDF report generation for Regalith Intelligence.
Produces a professional obligations report from a mapped profile.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from fpdf import FPDF, XPos, YPos


# ── Colour palette (light PDF — inverted from UI dark theme) ──────────────
_NAVY      = (10,  15,  30)
_SLATE     = (74,  96,  128)
_SILVER    = (168, 187, 208)
_WHITE     = (255, 255, 255)
_LIGHT_BG  = (245, 247, 252)
_RULE_LINE = (220, 226, 238)

_SEV_COLORS = {
    "critical":      (220, 53,  53),
    "important":     (220, 148, 20),
    "informational": (80,  120, 220),
}

_REG_COLORS = {
    "DORA": (61,  106, 245),
    "MiCA": (45,  184, 122),
    "PSD3": (220, 148, 20),
}

# Column widths (portrait A4, 170 mm usable)
_COL = {
    "reg":       22,
    "article":   24,
    "obligation":82,
    "deadline":  24,
    "severity":  18,
}

_ROW_H   = 6    # base cell height
_HEAD_H  = 7    # header row height


class _RegalithPDF(FPDF):
    def __init__(self, company: str, today: str):
        super().__init__()
        self._company = company
        self._today   = today
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*_SLATE)
        self.cell(0, 6, f"REGALITH INTELLIGENCE  ·  {self._company}  ·  Regulatory Obligations Report",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*_RULE_LINE)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*_SLATE)
        self.cell(0, 5,
                  f"Page {self.page_no()}  ·  Generated {self._today}  ·  "
                  "Ranges reflect medium confidence estimates. Not legal advice.",
                  align="C")


def generate_pdf(profile: dict[str, Any], records: list[dict[str, Any]]) -> bytes:
    company    = profile.get("company_name", "Company")
    lt         = profile.get("license_type", "")
    juris      = ", ".join(profile.get("jurisdictions", []))
    today      = date.today().strftime("%d %B %Y")

    total        = len(records)
    critical     = sum(1 for r in records if r["severity"] == "critical")
    important    = sum(1 for r in records if r["severity"] == "important")
    informational = sum(1 for r in records if r["severity"] == "informational")
    by_reg       = {}
    for r in records:
        by_reg[r["regulation_id"]] = by_reg.get(r["regulation_id"], 0) + 1

    # Sanitise all profile strings once
    company = _clean(company)
    lt      = _clean(lt)
    juris   = _clean(juris)

    pdf = _RegalithPDF(company, today)
    pdf.add_page()

    # ── Cover ─────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*_SLATE)
    pdf.cell(0, 6, "REGALITH INTELLIGENCE",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_draw_color(*_RULE_LINE)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*_NAVY)
    pdf.multi_cell(0, 10, "Regulatory Obligations Report",
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*_NAVY)
    pdf.cell(0, 9, company, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*_SLATE)
    pdf.cell(0, 6, f"{lt}  |  {juris}  |  Generated {today}",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    # ── Summary metrics ────────────────────────────────────────────────────
    _section_title(pdf, "Obligation summary")

    # Metric boxes
    metrics = [
        ("TOTAL",         str(total),         _NAVY),
        ("CRITICAL",      str(critical),       _SEV_COLORS["critical"]),
        ("IMPORTANT",     str(important),      _SEV_COLORS["important"]),
        ("INFORMATIONAL", str(informational),  _SEV_COLORS["informational"]),
    ]
    box_w = 40
    x_start = pdf.get_x()
    y_start = pdf.get_y()
    for i, (label, val, color) in enumerate(metrics):
        x = x_start + i * (box_w + 2)
        pdf.set_xy(x, y_start)
        pdf.set_fill_color(*_LIGHT_BG)
        pdf.rect(x, y_start, box_w, 16, style="F")
        pdf.set_xy(x + 2, y_start + 2)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*color)
        pdf.cell(box_w - 4, 8, val)
        pdf.set_xy(x + 2, y_start + 10)
        pdf.set_font("Helvetica", "", 6)
        pdf.set_text_color(*_SLATE)
        pdf.cell(box_w - 4, 5, label)

    pdf.set_xy(x_start, y_start + 20)
    pdf.ln(4)

    # By regulation
    _section_title(pdf, "By regulation")
    for reg, count in sorted(by_reg.items()):
        color = _REG_COLORS.get(reg, _SLATE)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*color)
        pdf.cell(30, 6, reg)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*_NAVY)
        pdf.cell(0, 6, f"{count} obligation{'s' if count != 1 else ''}",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    # Profile snapshot
    _section_title(pdf, "Company profile")
    _kv_row(pdf, "Licence type",      lt)
    _kv_row(pdf, "Jurisdictions",     juris)
    _kv_row(pdf, "Products",          ", ".join(profile.get("products", [])))
    _kv_row(pdf, "Customer segments", ", ".join(profile.get("customer_segments", [])))
    _kv_row(pdf, "Headcount",         profile.get("headcount_range", ""))
    _kv_row(pdf, "Onboarding volume", profile.get("monthly_onboarding_volume", ""))
    _kv_row(pdf, "KYC/AML function",  profile.get("kyc_aml_function", ""))
    _kv_row(pdf, "Remote onboarding", "Yes" if profile.get("has_remote_onboarding") else "No")
    _kv_row(pdf, "Crypto in scope",   "Yes" if profile.get("has_crypto") else "No")

    # ── Obligations table ──────────────────────────────────────────────────
    pdf.add_page()
    _section_title(pdf, f"Full obligations list  ({total} requirements)")
    _draw_table_header(pdf)

    sev_order = {"critical": 0, "important": 1, "informational": 2}
    sorted_records = sorted(records, key=lambda r: (sev_order.get(r["severity"], 9),
                                                     r["regulation_id"],
                                                     int(r.get("article_reference","0").split()[-1])
                                                     if r.get("article_reference","").split()
                                                     else 0))

    fill = False
    for rec in sorted_records:
        _draw_table_row(pdf, rec, fill)
        fill = not fill

    return bytes(pdf.output())


# ── Helpers ────────────────────────────────────────────────────────────────

def _section_title(pdf: FPDF, text: str) -> None:
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*_SLATE)
    pdf.cell(0, 5, _clean(text).upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_draw_color(*_RULE_LINE)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(3)


def _kv_row(pdf: FPDF, key: str, val: str) -> None:
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*_SLATE)
    pdf.cell(45, 5, _clean(key))
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*_NAVY)
    pdf.multi_cell(0, 5, _clean(val) or "-", new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _draw_table_header(pdf: FPDF) -> None:
    pdf.set_fill_color(*_LIGHT_BG)
    pdf.set_draw_color(*_RULE_LINE)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*_SLATE)
    for label, w in [("REGULATION", _COL["reg"]),
                      ("ARTICLE",   _COL["article"]),
                      ("OBLIGATION", _COL["obligation"]),
                      ("DEADLINE",  _COL["deadline"]),
                      ("SEVERITY",  _COL["severity"])]:
        pdf.cell(w, _HEAD_H, label, border=1, fill=True)
    pdf.ln()


def _draw_table_row(pdf: FPDF, rec: dict, fill: bool) -> None:
    sev     = rec.get("severity", "informational")
    reg_id  = _clean(rec.get("regulation_id", ""))
    article = _clean(rec.get("article_reference", ""))
    oblig   = _truncate(rec.get("obligation_summary", ""), 160)
    ddline  = _clean(_short_date(rec.get("deadline", "")))

    sev_color = _SEV_COLORS.get(sev, _SLATE)
    reg_color = _REG_COLORS.get(reg_id, _SLATE)
    bg        = _LIGHT_BG if fill else _WHITE

    # Calculate required row height from obligation text
    pdf.set_font("Helvetica", "", 7)
    # Estimate lines needed (approx 11 chars per mm at font size 7, col width 82mm)
    chars_per_line = int(_COL["obligation"] * 1.6)
    n_lines = max(1, -(-len(oblig) // chars_per_line))  # ceiling division
    row_h = max(_ROW_H, n_lines * 4)

    x0 = pdf.get_x()
    y0 = pdf.get_y()

    # Check page break
    if y0 + row_h > pdf.page_break_trigger:
        pdf.add_page()
        _draw_table_header(pdf)
        x0, y0 = pdf.get_x(), pdf.get_y()

    # Fill background
    pdf.set_fill_color(*bg)
    pdf.rect(x0, y0, sum(_COL.values()), row_h, style="F")

    # Regulation
    pdf.set_xy(x0, y0 + 1)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*reg_color)
    pdf.cell(_COL["reg"], row_h - 2, reg_id, border="LRB")

    # Article
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*_NAVY)
    pdf.cell(_COL["article"], row_h - 2, article, border="RB")

    # Obligation — multi_cell
    x_oblig = pdf.get_x()
    pdf.set_xy(x_oblig, y0 + 1)
    pdf.set_text_color(*_NAVY)
    pdf.set_font("Helvetica", "", 7)
    pdf.multi_cell(_COL["obligation"], 4, _clean(oblig), border="RB",
                   new_x=XPos.RIGHT, new_y=YPos.TOP)

    # Deadline
    x_dl = x0 + _COL["reg"] + _COL["article"] + _COL["obligation"]
    pdf.set_xy(x_dl, y0 + 1)
    pdf.set_font("Helvetica", "", 6)
    pdf.set_text_color(*_SLATE)
    pdf.cell(_COL["deadline"], row_h - 2, ddline, border="RB")

    # Severity badge
    pdf.set_font("Helvetica", "B", 6)
    pdf.set_text_color(*sev_color)
    pdf.cell(_COL["severity"], row_h - 2, sev.upper(), border="RB")

    pdf.set_xy(x0, y0 + row_h)


def _clean(text: str) -> str:
    """Normalise text to Latin-1 for Helvetica compatibility."""
    return (
        str(text)
        .replace("\u2013", "-")   # en-dash
        .replace("\u2014", "--")  # em-dash
        .replace("\u2019", "'")   # right single quote
        .replace("\u2018", "'")   # left single quote
        .replace("\u201c", '"')   # left double quote
        .replace("\u201d", '"')   # right double quote
        .replace("\u2026", "...")  # ellipsis
        .replace("\u20ac", "EUR") # euro sign
        .replace("\u2192", "->")  # right arrow
        .replace("\u2713", "OK")  # check mark
        .encode("latin-1", errors="replace")
        .decode("latin-1")
    )


def _truncate(text: str, n: int) -> str:
    text = _clean(text)
    return text if len(text) <= n else text[:n - 1] + "..."


def _short_date(deadline: str) -> str:
    # Shorten long deadline strings for table cell
    if "TBD" in deadline or "expected" in deadline:
        return "TBD ~2027"
    if "January 2025" in deadline:
        return "17 Jan 2025"
    if "December 2024" in deadline:
        return "30 Dec 2024"
    return deadline[:14]
