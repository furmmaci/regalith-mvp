"""
Legislative monitoring module — Regulatory Radar.

Scrapes OEIL (European Parliament Legislative Observatory) procedure pages
for key dossiers and caches results locally with weekly refresh.

Dossiers tracked:
  PSD3   2023/0209(COD)
  FIDA   2023/0205(COD)
  AMLA   2021/0240(COD)
  AMLR   2023/0268(COD)
  AMLD6  2020/0267(COD)
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ── Constants ────────────────────────────────────────────────────────────────

_CACHE_FILE = Path(__file__).parent / "fetched" / "radar.json"
_CACHE_TTL_DAYS = 7

_OEIL_BASE = "https://oeil.secure.europarl.europa.eu/oeil/popups/ficheprocedure.do"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Dossiers where we skip scraping and rely on static data (already adopted laws)
_SKIP_SCRAPE = {"AMLA", "AMLR", "AMLD6"}

# Dossier definitions
DOSSIERS = {
    "PSD3": {
        "ref": "2023/0209(COD)",
        "title": "Payment Services Directive 3",
        "short": "PSD3",
        "color": "#e8a020",
        "scope": ["EMI", "PI", "Bank"],  # licence types it applies to
        "description": "Revised rules for payment services — open banking, fraud liability, SCA.",
    },
    "FIDA": {
        "ref": "2023/0205(COD)",
        "title": "Financial Data Access Regulation",
        "short": "FIDA",
        "color": "#3d6af5",
        "scope": ["EMI", "PI", "Bank", "Lending"],
        "description": "Open finance framework — customer data sharing obligations for financial institutions.",
    },
    "AMLA": {
        "ref": "2021/0240(COD)",
        "title": "AML Authority Regulation",
        "short": "AMLA",
        "color": "#e84040",
        "scope": ["EMI", "PI", "VASP", "Bank", "Lending"],
        "description": "Creates EU Anti-Money Laundering Authority — direct supervisory powers over obliged entities.",
    },
    "AMLR": {
        "ref": "2023/0268(COD)",
        "title": "AML Regulation",
        "short": "AMLR",
        "color": "#e84040",
        "scope": ["EMI", "PI", "VASP", "Bank", "Lending"],
        "description": "Single EU rulebook replacing national AML/CTF laws — CDD, UBO, PEPs, crypto.",
    },
    "AMLD6": {
        "ref": "2020/0267(COD)",
        "title": "6th Anti-Money Laundering Directive",
        "short": "AMLD6",
        "color": "#e84040",
        "scope": ["EMI", "PI", "VASP", "Bank", "Lending"],
        "description": "National implementation framework for AMLR — replaces AMLD4/5.",
    },
}

# Fallback static data (used when scraping fails)
_STATIC_FALLBACK = {
    "PSD3": {
        "current_stage": "Council 1st reading",
        "last_update": "2024-11-13",
        "next_milestone": "Council general approach",
        "expected_date": "2025 Q2",
        "status_class": "amber",
        "progress_pct": 55,
    },
    "FIDA": {
        "current_stage": "EP 1st reading completed",
        "last_update": "2024-12-01",
        "next_milestone": "Council position",
        "expected_date": "2025 Q3",
        "status_class": "blue",
        "progress_pct": 60,
    },
    "AMLA": {
        "current_stage": "Published in OJ — Authority operational July 2025",
        "last_update": "2024-06-19",
        "next_milestone": "AMLA operational (July 2025)",
        "expected_date": "2025-07-01",
        "status_class": "red",
        "progress_pct": 95,
    },
    "AMLR": {
        "current_stage": "Published in OJ — applies from July 2027",
        "last_update": "2024-06-19",
        "next_milestone": "Commission delegated acts (2025–2026)",
        "expected_date": "2027-07-01",
        "status_class": "amber",
        "progress_pct": 90,
    },
    "AMLD6": {
        "current_stage": "Published in OJ — national transposition",
        "last_update": "2024-06-19",
        "next_milestone": "Member States transposition deadline",
        "expected_date": "2027-07-01",
        "status_class": "amber",
        "progress_pct": 88,
    },
}

# ── Scraping ─────────────────────────────────────────────────────────────────

def _scrape_oeil(ref: str) -> dict | None:
    """Scrape OEIL procedure page and extract key legislative status info."""
    try:
        url = f"{_OEIL_BASE}?lang=en&reference={ref}"
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "lxml")

        stage = _extract_stage(soup)
        last_update = _extract_last_update(soup)
        next_milestone = _extract_next_milestone(soup)

        if not stage:
            return None

        return {
            "current_stage": stage,
            "last_update": last_update or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "next_milestone": next_milestone or "Awaiting next step",
            "expected_date": _infer_expected_date(stage, ref),
            "status_class": _stage_to_class(stage),
            "progress_pct": _stage_to_progress(stage),
        }
    except Exception:
        return None


def _extract_stage(soup: BeautifulSoup) -> str | None:
    """Extract the current procedural stage from OEIL HTML."""
    # Try various selectors used by OEIL
    for selector in [
        ".procedure-stage",
        "#currentStage",
        ".lastEvent td",
        "td.procedureStage",
    ]:
        el = soup.select_one(selector)
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)[:120]

    # Fallback: look for a <td> near "Stage reached"
    for td in soup.find_all("td"):
        text = td.get_text(strip=True)
        if "Stage reached" in text or "stage reached" in text:
            # next sibling td
            nxt = td.find_next_sibling("td")
            if nxt:
                return nxt.get_text(strip=True)[:120]

    # Last resort: find any element containing common EP stage keywords
    keywords = ["1st reading", "2nd reading", "trilogue", "Council position",
                 "published", "entry into force", "adopted"]
    for kw in keywords:
        el = soup.find(string=lambda t: t and kw.lower() in t.lower())
        if el:
            parent = el.parent
            if parent:
                text = parent.get_text(strip=True)
                if len(text) < 150:
                    return text

    return None


def _extract_last_update(soup: BeautifulSoup) -> str | None:
    """Extract the date of the last legislative event."""
    # Look for a date pattern near event tables
    import re
    date_pattern = re.compile(r"\b(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})\b")

    # Prefer dates in event/history tables
    for table in soup.find_all("table"):
        tds = table.find_all("td")
        dates = []
        for td in tds:
            m = date_pattern.search(td.get_text())
            if m:
                dates.append(m.group(1))
        if dates:
            raw = dates[-1]
            # Normalize to ISO
            if "/" in raw:
                parts = raw.split("/")
                return f"{parts[2]}-{parts[1]}-{parts[0]}"
            return raw

    return None


def _extract_next_milestone(soup: BeautifulSoup) -> str | None:
    """Try to identify the next expected step."""
    for selector in [".nextStep", ".next-step", "#nextMilestone"]:
        el = soup.select_one(selector)
        if el:
            return el.get_text(strip=True)[:120]
    return None


def _infer_expected_date(stage: str, ref: str) -> str:
    """Infer expected completion / application date from stage text."""
    stage_l = stage.lower()
    if "2027" in stage or "july 2027" in stage_l:
        return "2027-07-01"
    if "2026" in stage:
        return "2026"
    if "force" in stage_l or "published" in stage_l:
        if "2024" in stage:
            return "2024"
    if "1st reading" in stage_l and "council" in stage_l:
        return "2025–2026"
    return "TBD"


def _stage_to_class(stage: str) -> str:
    stage_l = stage.lower()
    if any(k in stage_l for k in ["force", "published in oj", "adopted", "applies"]):
        return "red"
    if any(k in stage_l for k in ["trilogue", "2nd reading", "conciliation"]):
        return "amber"
    if any(k in stage_l for k in ["1st reading", "committee", "plenary"]):
        return "blue"
    return "gray"


def _stage_to_progress(stage: str) -> int:
    stage_l = stage.lower()
    if "force" in stage_l or "applies" in stage_l:
        return 95
    if "published" in stage_l:
        return 90
    if "trilogue" in stage_l:
        return 75
    if "2nd reading" in stage_l:
        return 70
    if "council position" in stage_l:
        return 65
    if "1st reading" in stage_l and "council" in stage_l:
        return 55
    if "1st reading" in stage_l:
        return 40
    if "committee" in stage_l:
        return 30
    if "proposal" in stage_l:
        return 15
    return 25


# ── Cache management ─────────────────────────────────────────────────────────

def _cache_is_fresh() -> bool:
    if not _CACHE_FILE.exists():
        return False
    try:
        data = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        fetched_at = data.get("_fetched_at", 0)
        age_days = (time.time() - fetched_at) / 86400
        return age_days < _CACHE_TTL_DAYS
    except Exception:
        return False


def _load_cache() -> dict:
    try:
        return json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(data: dict) -> None:
    _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    data["_fetched_at"] = time.time()
    _CACHE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ── Public API ───────────────────────────────────────────────────────────────

def get_radar_data(force_refresh: bool = False) -> dict[str, dict]:
    """
    Return legislative status for all tracked dossiers.

    Returns a dict keyed by short name (PSD3, FIDA, AMLA, AMLR, AMLD6).
    Each value contains:
        current_stage, last_update, next_milestone, expected_date,
        status_class (red/amber/blue/gray), progress_pct (0-100),
        plus metadata from DOSSIERS (title, short, color, scope, description).
    """
    if not force_refresh and _cache_is_fresh():
        cached = _load_cache()
        # Merge static dossier metadata
        result = {}
        for key, meta in DOSSIERS.items():
            entry = dict(meta)
            entry.update(cached.get(key, _STATIC_FALLBACK.get(key, {})))
            result[key] = entry
        return result

    # Attempt live scrape (skip adopted laws — static data is more accurate)
    scraped: dict[str, dict] = {}
    for key, dossier in DOSSIERS.items():
        if key in _SKIP_SCRAPE:
            scraped[key] = _STATIC_FALLBACK[key]
            continue
        live = _scrape_oeil(dossier["ref"])
        if live:
            scraped[key] = live
        else:
            scraped[key] = _STATIC_FALLBACK.get(key, {
                "current_stage": "Status unavailable",
                "last_update": "—",
                "next_milestone": "—",
                "expected_date": "TBD",
                "status_class": "gray",
                "progress_pct": 0,
            })

    _save_cache(scraped)

    result = {}
    for key, meta in DOSSIERS.items():
        entry = dict(meta)
        entry.update(scraped[key])
        result[key] = entry
    return result


def refresh_radar(force: bool = False) -> None:
    """Background-safe refresh call (swallows exceptions)."""
    try:
        get_radar_data(force_refresh=force or not _cache_is_fresh())
    except Exception:
        pass
