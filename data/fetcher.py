"""
EUR-Lex / CELLAR fetcher.

Fetches full text of DORA, MiCA, and PSD3 from EUR-Lex and stores them as
structured JSON in data/fetched/. Checks for updates weekly.

Manual run:  python -m data.fetcher
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── Regulation registry ───────────────────────────────────────────────────

REGULATIONS: dict[str, dict] = {
    "DORA": {
        "celex": "32022R2554",
        "title": "Digital Operational Resilience Act (EU) 2022/2554",
        "effective_date": "2025-01-17",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32022R2554",
    },
    "MiCA": {
        "celex": "32023R1114",
        "title": "Markets in Crypto-Assets Regulation (EU) 2023/1114",
        "effective_date": "2024-12-30",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32023R1114",
    },
    "PSD3": {
        "celex": "52023PC0366",
        "title": "Payment Services Directive 3 — Commission Proposal COM(2023) 366",
        "effective_date": None,
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:52023PC0366",
    },
}

# ── Paths ─────────────────────────────────────────────────────────────────

_BASE = Path(__file__).parent
CACHE_DIR = _BASE / "fetched"
META_FILE = _BASE / "fetch_meta.json"
REFRESH_DAYS = 7

# ── HTTP setup ────────────────────────────────────────────────────────────

SPARQL_ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"
HEADERS = {
    "User-Agent": (
        "Regalith-Intelligence/1.0 "
        "(regulatory-research; +https://github.com/furmmaci/regalith-mvp)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
}
REQUEST_TIMEOUT = 30
INTER_REQUEST_DELAY = 2.0  # seconds — be polite to EUR-Lex


# ── Metadata via CELLAR SPARQL ────────────────────────────────────────────

_SPARQL_QUERY = """
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT DISTINCT ?title ?force_date WHERE {{
  ?work cdm:resource_legal_id_celex "{celex}"^^xsd:string .
  OPTIONAL {{ ?work cdm:resource_title ?title .
              FILTER(lang(?title) = "en") }}
  OPTIONAL {{ ?work cdm:resource_legal_in-force ?force_date . }}
}}
LIMIT 5
"""


def fetch_metadata(celex: str) -> dict:
    """Query CELLAR SPARQL for official title and entry-into-force date."""
    query = _SPARQL_QUERY.format(celex=celex)
    try:
        resp = requests.get(
            SPARQL_ENDPOINT,
            params={"query": query, "format": "application/sparql-results+json"},
            headers={**HEADERS, "Accept": "application/sparql-results+json"},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        bindings = data.get("results", {}).get("bindings", [])
        if bindings:
            b = bindings[0]
            return {
                "sparql_title": b.get("title", {}).get("value", ""),
                "sparql_force_date": b.get("force_date", {}).get("value", ""),
            }
    except Exception as exc:
        logger.warning("SPARQL metadata fetch failed for %s: %s", celex, exc)
    return {}


# ── Full-text fetch and parse ─────────────────────────────────────────────

def fetch_html(url: str) -> str | None:
    """Fetch EUR-Lex HTML document. Returns raw HTML or None on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except Exception as exc:
        logger.error("HTML fetch failed for %s: %s", url, exc)
        return None


def parse_articles(html: str) -> list[dict]:
    """
    Parse EUR-Lex HTML into a list of article records.
    Each record: {article_number, article_title, article_text}
    """
    soup = BeautifulSoup(html, "lxml")

    # Strip nav, script, style noise
    for tag in soup.find_all(["nav", "header", "footer", "script", "style",
                               "noscript", "aside"]):
        tag.decompose()

    # Try to isolate the main document body
    main = (
        soup.find("div", id="TexteOnly")
        or soup.find("div", class_="tabContent")
        or soup.find("div", id="document1")
        or soup.find("main")
        or soup.find("body")
    )
    if not main:
        return []

    full_text = main.get_text(separator="\n", strip=True)

    # Match "Article 1", "Article 23" etc. — EUR-Lex uses this exact phrasing
    article_re = re.compile(
        r"(?:^|\n)(Article\s+(\d+))\s*\n(.*?)(?=\nArticle\s+\d+|\Z)",
        re.DOTALL | re.IGNORECASE,
    )

    articles = []
    for m in article_re.finditer(full_text):
        number = int(m.group(2))
        body = m.group(3).strip()

        # First non-empty line ≤ 120 chars → article title
        lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
        if lines and len(lines[0]) <= 120:
            title = lines[0]
            text_lines = lines[1:]
        else:
            title = ""
            text_lines = lines

        text = " ".join(text_lines)
        # Collapse excessive whitespace
        text = re.sub(r" {2,}", " ", text)

        articles.append({
            "article_number": number,
            "article_title": title,
            "article_text": text[:8000],  # cap per article
        })

    # Deduplicate (EUR-Lex sometimes has duplicate article sections)
    seen: set[int] = set()
    unique = []
    for a in articles:
        if a["article_number"] not in seen:
            seen.add(a["article_number"])
            unique.append(a)

    return unique


# ── Cache I/O ─────────────────────────────────────────────────────────────

def _load_meta() -> dict:
    if META_FILE.exists():
        try:
            return json.loads(META_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_meta(meta: dict) -> None:
    META_FILE.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def _cache_path(reg_id: str) -> Path:
    return CACHE_DIR / f"{reg_id.lower()}.json"


def load_cached(reg_id: str) -> dict | None:
    """Load a cached regulation document. Returns None if not cached."""
    path = _cache_path(reg_id)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def _save_cached(reg_id: str, doc: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(reg_id).write_text(
        json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ── Public API ────────────────────────────────────────────────────────────

def needs_refresh(reg_id: str) -> bool:
    """Return True if cache is absent or older than REFRESH_DAYS."""
    meta = _load_meta()
    if reg_id not in meta:
        return True
    try:
        last = datetime.fromisoformat(meta[reg_id]["last_fetched"])
        # Make timezone-aware if needed
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - last > timedelta(days=REFRESH_DAYS)
    except Exception:
        return True


def fetch_regulation(reg_id: str) -> dict | None:
    """
    Full pipeline for one regulation:
      SPARQL metadata → HTML fetch → article parse → cache write.
    Returns the structured document dict or None on failure.
    """
    if reg_id not in REGULATIONS:
        raise ValueError(f"Unknown regulation: {reg_id}")

    cfg = REGULATIONS[reg_id]
    logger.info("Fetching %s (%s)…", reg_id, cfg["celex"])

    # 1. SPARQL metadata
    meta_extra = fetch_metadata(cfg["celex"])
    time.sleep(INTER_REQUEST_DELAY)

    # 2. Full-text HTML
    html = fetch_html(cfg["source_url"])
    if not html:
        logger.error("Failed to fetch HTML for %s", reg_id)
        return None
    time.sleep(INTER_REQUEST_DELAY)

    # 3. Parse articles
    articles = parse_articles(html)
    logger.info("  Parsed %d articles for %s", len(articles), reg_id)

    # 4. Build structured document
    doc = {
        "regulation_id": reg_id,
        "celex": cfg["celex"],
        "title": meta_extra.get("sparql_title") or cfg["title"],
        "effective_date": (
            meta_extra.get("sparql_force_date")
            or cfg.get("effective_date")
            or ""
        ),
        "source_url": cfg["source_url"],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "article_count": len(articles),
        "articles": articles,
    }

    # 5. Persist
    _save_cached(reg_id, doc)

    fetch_meta = _load_meta()
    fetch_meta[reg_id] = {
        "last_fetched": doc["fetched_at"],
        "article_count": len(articles),
        "title": doc["title"],
    }
    _save_meta(fetch_meta)

    return doc


def check_and_refresh(reg_ids: list[str] | None = None) -> dict[str, str]:
    """
    Check all (or specified) regulations and refresh stale ones.
    Returns a status dict: {reg_id: "refreshed" | "cached" | "failed"}.
    Non-blocking for already-fresh cache entries.
    """
    ids = reg_ids or list(REGULATIONS.keys())
    status: dict[str, str] = {}

    for reg_id in ids:
        if needs_refresh(reg_id):
            result = fetch_regulation(reg_id)
            status[reg_id] = "refreshed" if result else "failed"
        else:
            status[reg_id] = "cached"

    return status


def get_fetch_status() -> dict[str, dict]:
    """Return per-regulation cache status for display in the UI."""
    meta = _load_meta()
    status = {}
    for reg_id in REGULATIONS:
        if reg_id in meta:
            last = meta[reg_id].get("last_fetched", "")
            try:
                dt = datetime.fromisoformat(last)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                age_days = (datetime.now(timezone.utc) - dt).days
                status[reg_id] = {
                    "fetched": True,
                    "last_fetched": last,
                    "age_days": age_days,
                    "article_count": meta[reg_id].get("article_count", 0),
                    "stale": age_days >= REFRESH_DAYS,
                }
            except Exception:
                status[reg_id] = {"fetched": False}
        else:
            status[reg_id] = {"fetched": False}
    return status


# ── CLI entry point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print("Regalith EUR-Lex fetcher\n")
    for reg_id in REGULATIONS:
        print(f"Fetching {reg_id}…")
        doc = fetch_regulation(reg_id)
        if doc:
            print(f"  ✓ {doc['article_count']} articles — {doc['title'][:60]}")
        else:
            print(f"  ✗ Failed")
