"""
Regulatory mapping engine.

Takes a company profile dict and returns a list of RequirementRecord dicts —
one per applicable article. Works from curated rules (always) and supplements
with heuristic matching against EUR-Lex fetched article text when available.
"""

from __future__ import annotations

import re
from typing import TypedDict

from engine.rules import (
    ALL_RULES,
    HEURISTIC_KEYWORDS,
    REGULATION_NAMES,
    REGULATION_SCOPE,
    ArticleRule,
)


# ── Output schema ──────────────────────────────────────────────────────────

class RequirementRecord(TypedDict):
    requirement_id: str          # e.g. DORA-ART-005
    regulation_name: str         # e.g. "Digital Operational Resilience Act (DORA)"
    regulation_id: str           # DORA | MiCA | PSD3
    article_reference: str       # e.g. "Article 5"
    article_label: str           # full label with title
    obligation_summary: str      # ≤ 2 sentences
    applies_because: str         # 1 sentence
    deadline: str
    severity: str                # critical | important | informational
    source: str                  # "curated" | "heuristic"
    article_text_excerpt: str    # first 400 chars of raw EUR-Lex text, or ""


_SEVERITY_ORDER = {"critical": 0, "important": 1, "informational": 2}
_DEADLINE_ORDER = {
    "30 December 2024": 0,
    "17 January 2025": 1,
}


# ── Public API ──────────────────────────────────────────────────────────────

def map_profile(profile: dict) -> list[RequirementRecord]:
    """
    Map a company profile against all applicable regulations.

    Returns RequirementRecords sorted by: severity → deadline → regulation → article number.
    Curated rules are always included when applicable.
    Heuristic rules from fetched EUR-Lex text supplement where available.
    """
    results: list[RequirementRecord] = []
    covered_keys: set[str] = set()   # (regulation_id, article_number) already added

    # 1. Curated rules — always authoritative
    for rule in ALL_RULES:
        scope_fn = REGULATION_SCOPE.get(rule.regulation_id)
        if not scope_fn or not scope_fn(profile):
            continue
        if rule.condition is not None and not rule.condition(profile):
            continue

        key = (rule.regulation_id, rule.article_number)
        covered_keys.add(key)

        # Try to enrich with fetched article text
        excerpt = _fetch_excerpt(rule.regulation_id, rule.article_number)

        results.append(_build_record(rule, profile, "curated", excerpt))

    # 2. Heuristic rules — from fetched EUR-Lex articles not already covered
    for reg_id, scope_fn in REGULATION_SCOPE.items():
        if not scope_fn(profile):
            continue

        fetched = _load_fetched(reg_id)
        if not fetched:
            continue

        for article in fetched.get("articles", []):
            num = article.get("article_number", 0)
            if (reg_id, num) in covered_keys:
                continue

            text = article.get("article_text", "")
            title = article.get("article_title", "")
            full_text = f"{title} {text}".lower()

            reason = _heuristic_match(full_text, profile)
            if not reason:
                continue

            covered_keys.add((reg_id, num))
            results.append(_build_heuristic_record(
                reg_id=reg_id,
                article=article,
                profile=profile,
                reason=reason,
                fetched_meta=fetched,
            ))

    results.sort(key=lambda r: (
        _SEVERITY_ORDER.get(r["severity"], 9),
        _DEADLINE_ORDER.get(r["deadline"], 5),
        r["regulation_id"],
        _article_num(r["article_reference"]),
    ))

    return results


def map_profile_summary(profile: dict) -> dict:
    """Aggregate counts for dashboard display."""
    records = map_profile(profile)
    return {
        "total": len(records),
        "critical": sum(1 for r in records if r["severity"] == "critical"),
        "important": sum(1 for r in records if r["severity"] == "important"),
        "informational": sum(1 for r in records if r["severity"] == "informational"),
        "by_regulation": {
            reg: sum(1 for r in records if r["regulation_id"] == reg)
            for reg in ("DORA", "MiCA", "PSD3")
        },
        "records": records,
    }


# ── Internal helpers ────────────────────────────────────────────────────────

def _build_record(
    rule: ArticleRule,
    profile: dict,
    source: str,
    excerpt: str,
) -> RequirementRecord:
    reg_id = rule.regulation_id
    art_num = rule.article_number
    return RequirementRecord(
        requirement_id=f"{reg_id}-ART-{art_num:03d}",
        regulation_name=REGULATION_NAMES.get(reg_id, reg_id),
        regulation_id=reg_id,
        article_reference=f"Article {art_num}",
        article_label=rule.article_label,
        obligation_summary=rule.obligation_summary,
        applies_because=rule.applies_because(profile),
        deadline=rule.deadline,
        severity=rule.severity,
        source=source,
        article_text_excerpt=excerpt,
    )


def _build_heuristic_record(
    reg_id: str,
    article: dict,
    profile: dict,
    reason: str,
    fetched_meta: dict,
) -> RequirementRecord:
    num = article.get("article_number", 0)
    title = article.get("article_title", "")
    text = article.get("article_text", "")

    label = f"Article {num}" + (f" — {title}" if title else "")
    summary = _first_two_sentences(text)
    deadline = _derive_deadline(reg_id, fetched_meta)

    return RequirementRecord(
        requirement_id=f"{reg_id}-ART-{num:03d}",
        regulation_name=REGULATION_NAMES.get(reg_id, reg_id),
        regulation_id=reg_id,
        article_reference=f"Article {num}",
        article_label=label,
        obligation_summary=summary,
        applies_because=_heuristic_applies_because(profile, reason),
        deadline=deadline,
        severity="informational",
        source="heuristic",
        article_text_excerpt=text[:400],
    )


def _heuristic_match(text_lower: str, profile: dict) -> str | None:
    """
    Return the reason string if the article text is relevant to this profile,
    or None if it should be skipped.
    """
    from engine.rules import _has_crypto, _has_remote, _is_outsourced, _has_retail, _has_payments

    checks = [
        (_has_remote(profile), "remote_onboarding",
         "involves remote onboarding processes"),
        (_has_crypto(profile), "crypto_in_scope",
         "includes crypto-asset services"),
        (_is_outsourced(profile), "outsourced",
         "relies on outsourced KYC/AML providers"),
        (_has_retail(profile), "retail",
         "serves retail customers"),
        (_has_payments(profile), "payments",
         "processes payment transactions"),
    ]

    for condition, keyword_set, reason in checks:
        if not condition:
            continue
        for kw in HEURISTIC_KEYWORDS.get(keyword_set, []):
            if kw in text_lower:
                return reason

    return None


def _heuristic_applies_because(profile: dict, reason: str) -> str:
    name = profile.get("company_name", "Your company")
    return f"Flagged because {name} {reason}, and this article's text contains directly relevant obligations."


def _first_two_sentences(text: str) -> str:
    """Extract first 2 sentences from article text as the obligation summary."""
    text = text.strip()
    if not text:
        return "See full article text for obligation details."
    # Split on sentence-ending punctuation followed by a space/end
    sentences = re.split(r'(?<=[.!?])\s+', text)
    summary = " ".join(sentences[:2])
    if len(summary) > 400:
        summary = summary[:397] + "…"
    return summary or text[:300]


def _derive_deadline(reg_id: str, fetched_meta: dict) -> str:
    defaults = {
        "DORA": "17 January 2025",
        "MiCA": "30 December 2024",
        "PSD3": "TBD — expected 2027 (proposal stage)",
    }
    eff = fetched_meta.get("effective_date", "")
    if eff and len(eff) >= 10:
        return eff[:10]
    return defaults.get(reg_id, "See regulation text")


def _article_num(ref: str) -> int:
    m = re.search(r"\d+", ref)
    return int(m.group()) if m else 0


# ── Cache loading ───────────────────────────────────────────────────────────

_fetched_cache: dict[str, dict | None] = {}


def _load_fetched(reg_id: str) -> dict | None:
    if reg_id in _fetched_cache:
        return _fetched_cache[reg_id]
    try:
        from data.fetcher import load_cached
        doc = load_cached(reg_id)
        _fetched_cache[reg_id] = doc
        return doc
    except Exception:
        _fetched_cache[reg_id] = None
        return None


def _fetch_excerpt(reg_id: str, article_number: int) -> str:
    doc = _load_fetched(reg_id)
    if not doc:
        return ""
    for art in doc.get("articles", []):
        if art.get("article_number") == article_number:
            return art.get("article_text", "")[:400]
    return ""


def invalidate_cache() -> None:
    """Call after a fresh EUR-Lex fetch to reload article text."""
    _fetched_cache.clear()
