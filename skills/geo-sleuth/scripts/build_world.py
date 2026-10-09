#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Build per-country lookup tables in data/world/<cc>.json (plates, phone prefixes, admin divisions).

Tables are offline JSON read by world.py / clues.py. Each file records its sources and fetch date in `_meta`.
Parsed parts come from Wikipedia wikitext (fetched live); rule-like parts (plate code ranges, phone prefixes)
are transcribed from the same Wikipedia pages and kept here as constants so the source stays reviewable.

  build_world.py ae                 rebuild data/world/ae.json
  build_world.py ae --from-dir d/   use already downloaded <Title>.wiki files (dev / offline)
  build_world.py list               list available builders
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

DATA = Path(__file__).parent.parent / "data" / "world"
UA = "geo-sleuth/2 (lookup table builder)"
WIKI_RAW = "https://en.wikipedia.org/w/index.php?title={t}&action=raw"


def wiki(title: str, from_dir: str | None, proxy: str | None) -> str:
    if from_dir:
        return (Path(from_dir) / f"{title}.wiki").read_text(encoding="utf-8")
    cmd = ["curl", "-s", "-m", "90", "-A", UA, "-L"]
    if proxy:
        cmd += ["--proxy", proxy]
    r = subprocess.run(cmd + [WIKI_RAW.format(t=title)], capture_output=True)
    if r.returncode != 0 or len(r.stdout) < 500:
        sys.exit(f"fetch failed: {title}")
    return r.stdout.decode("utf-8", "replace")


def _templates(s: str) -> str:
    """Resolve wiki templates innermost-first: {{sort|key|shown}} / {{lang|xx|shown}} -> shown, {{flag|X}} -> X, the rest dropped."""
    for _ in range(10):
        m = re.search(r"\{\{([^{}]*)\}\}", s)
        if not m:
            break
        parts = m.group(1).split("|")
        name = parts[0].strip().lower()
        keep = ""
        if name in ("sort", "lang", "nowrap", "small", "flag", "flagu", "flagcountry") and len(parts) > 1:
            keep = parts[-1] if name in ("sort", "lang", "nowrap", "small") else parts[1]
        elif name.startswith("formatnum") and ":" in parts[0]:
            keep = parts[0].split(":", 1)[1]
        s = s[:m.start()] + keep + s[m.end():]
    return s


def _clean(cell: str) -> str:
    cell = _templates(cell)
    cell = re.sub(r"^\s*(align|style|class|data-sort-value)=\"[^\"]*\"\s*\|", "", cell.strip())
    cell = re.sub(r"\{\{formatnum:([^}]*)\}\}", r"\1", cell)
    cell = re.sub(r"\{\{lang\|[a-z-]+\|([^}]*)\}\}", r"\1", cell, flags=re.I)
    cell = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", cell)
    cell = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", cell, flags=re.S)
    cell = re.sub(r"<br\s*/?>.*", "", cell, flags=re.I | re.S)
    cell = re.sub(r"'{2,}", "", cell)
    return cell.strip()


def _num(s: str) -> float | None:
    s = s.replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


# ---------------------------------------------------------------- UAE

AE_SRC = {
    "plates": "https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_the_United_Arab_Emirates",
    "phone": "https://en.wikipedia.org/wiki/Telephone_numbers_in_the_United_Arab_Emirates",
    "emirates": "https://en.wikipedia.org/wiki/Emirates_of_the_United_Arab_Emirates",
    "dubai": "https://en.wikipedia.org/wiki/List_of_communities_in_Dubai",
}

# Plate rules, transcribed from the plates page (design table). `markers` are words printed on the plate.
AE_PLATES = [
    {"admin1": "Abu Dhabi", "markers": ["ABU DHABI", "A.D", "AD", "أبوظبي", "أبو ظبي"],
     "code_kind": "number", "codes": ["1"] + [str(i) for i in range(4, 23)] + ["50"], "digits": 5,
     "note": "code is a number, usually in a red box on the left (1, 4-22, 50)"},
    {"admin1": "Dubai", "markers": ["DUBAI", "دبي"],
     "code_kind": "letter", "codes": [chr(c) for c in range(65, 91)] + ["AA", "BB", "CC", "DD", "EE"], "digits": 5,
     "note": "letter code (doubled letters AA-EE also used); taxis yellow, export blue, transit green, police dark green"},
    {"admin1": "Sharjah", "markers": ["SHARJAH", "SHJ", "الشارقة"],
     "code_kind": "number", "codes": ["", "1", "2", "3", "4"], "digits": 5,
     "note": "optional category number 1-4; orange or white plate"},
    {"admin1": "Ajman", "markers": ["AJMAN", "عجمان"],
     "code_kind": "letter", "codes": list("ABCDEH"), "digits": 5, "note": "first letter only A, B, C, D, E or H"},
    {"admin1": "Umm Al Quwain", "markers": ["UMM AL QUWAIN", "U.A.Q", "UAQ", "أم القيوين"],
     "code_kind": "letter", "codes": list("ABCDEFGHIX"), "digits": 5, "note": "letters A-I or X"},
    {"admin1": "Ras Al Khaimah", "markers": ["RAS AL KHAIMAH", "R.A.K", "RAK", "رأس الخيمة"],
     "code_kind": "letter", "codes": list("ACDIKMNSVY"), "digits": 5, "note": "letters A, C, D, I, K, M, N, S, V, Y; some plates show a fort"},
    {"admin1": "Fujairah", "markers": ["FUJAIRAH", "FUJ", "الفجيرة"],
     "code_kind": "letter", "codes": list("ABCDEFGKMPRST"), "digits": 5, "note": "letters A-G, K, M, P, R, S, T"},
]

# Phone prefixes, transcribed from the telephone numbers page.
AE_PHONE = {
    "calling_code": "971", "trunk": "0",
    "area": [
        {"prefix": "02", "admin1": ["Abu Dhabi"], "place": "Abu Dhabi city and region"},
        {"prefix": "03", "admin1": ["Abu Dhabi"], "place": "Al Ain"},
        {"prefix": "04", "admin1": ["Dubai"], "place": "Dubai"},
        {"prefix": "06", "admin1": ["Sharjah", "Ajman", "Umm Al Quwain"], "place": "Sharjah, Ajman, Umm Al Quwain"},
        {"prefix": "07", "admin1": ["Ras Al Khaimah"], "place": "Ras Al Khaimah"},
        {"prefix": "08", "admin1": ["Abu Dhabi"], "place": "Al Dhafra (Western Region, Liwa)"},
        {"prefix": "09", "admin1": ["Fujairah"], "place": "Fujairah"},
    ],
    "mobile": [
        {"prefix": "050", "note": "Etisalat (e&)"}, {"prefix": "052", "note": "du"}, {"prefix": "053", "note": "Virgin Mobile"},
        {"prefix": "054", "note": "Etisalat (e&)"}, {"prefix": "055", "note": "du"}, {"prefix": "056", "note": "Etisalat (e&)"},
        {"prefix": "057", "note": "DOMC"}, {"prefix": "058", "note": "du / Virgin Mobile"},
    ],
    "special": [
        {"prefix": "800", "note": "toll-free, nationwide"}, {"prefix": "600", "note": "shared cost, nationwide"},
        {"prefix": "200", "note": "shared cost, nationwide"},
    ],
}

AE_EMIRATE_ALIASES = {
    "Abu Dhabi": ["AD", "Abudhabi", "أبوظبي"], "Dubai": ["DXB", "دبي"], "Sharjah": ["SHJ", "الشارقة"],
    "Ajman": ["عجمان"], "Umm Al Quwain": ["UAQ", "Umm al-Quwain", "أم القيوين"],
    "Ras Al Khaimah": ["RAK", "Ras al-Khaimah", "رأس الخيمة"], "Fujairah": ["الفجيرة"],
}


def parse_emirates(txt: str) -> list[dict]:
    out = []
    for row in re.split(r"\n\|-", txt):
        iso = re.search(r"\|\s*(AE-[A-Z]{2})", row)
        if not iso:
            continue
        cells = [c for c in re.split(r"\n\|", row) if c.strip()]
        name = local = cap = ""
        for c in cells:
            m = re.search(r"\[\[Emirate of [^|\]]*\|([^\]]*)\]\]|\[\[(Emirate of [^\]]*)\]\]", c)
            if m and not name:
                name = (m.group(1) or m.group(2).replace("Emirate of ", "")).strip()
            m = re.search(r"\{\{lang\|ar\|([^}]*)\}\}", c)
            if m and not local:
                local = m.group(1).strip()
        if not name:  # e.g. Umm Al Quwain links without "Emirate of"
            for c in cells:
                if "File:" in c or "{{" in c:
                    continue
                v = _clean(c)
                if v and not re.match(r"^[\d,. ()A-Z-]*$", v):
                    name = v
                    break
        idx = next((i for i, c in enumerate(cells) if "{{dts" in c), None)
        if idx is not None and idx + 1 < len(cells):
            cap = _clean(cells[idx + 1])
        name = {"Ras al-Khaimah": "Ras Al Khaimah", "Umm al-Quwain": "Umm Al Quwain"}.get(name, name)
        out.append({"name": name, "name_local": local, "iso": iso.group(1), "capital": cap,
                    "aliases": AE_EMIRATE_ALIASES.get(name, [])})
    return out


def parse_dubai_communities(txt: str) -> list[dict]:
    out = []
    sector = ""
    for block in re.split(r"\n(?===)", txt):
        m = re.match(r"==\s*([^=]+?)\s*==", block)
        if m:
            sector = m.group(1)
        for row in re.split(r"\n\|-", block):
            cells = [c for c in re.split(r"\n\|", "\n" + row.strip()) if c.strip()]
            if len(cells) < 3:
                continue
            code = _clean(cells[0])
            if not re.fullmatch(r"\d{3}", code):
                continue
            name = _clean(cells[1])
            local = _clean(cells[2])
            area = _num(_clean(cells[3])) if len(cells) > 3 else None
            pop = _num(_clean(cells[4])) if len(cells) > 4 else None
            out.append({"name": name, "name_local": local, "admin1": "Dubai", "code": code, "sector": sector,
                        "area_km2": area, "population": int(pop) if pop is not None else None})
    return out


def build_ae(from_dir: str | None, proxy: str | None) -> dict:
    t = {k: v.rsplit("/", 1)[1] for k, v in AE_SRC.items()}
    emirates = parse_emirates(wiki(t["emirates"], from_dir, proxy))
    communities = parse_dubai_communities(wiki(t["dubai"], from_dir, proxy))
    if len(emirates) != 7:
        sys.exit(f"expected 7 emirates, parsed {len(emirates)}: {[e['name'] for e in emirates]}")
    if len(communities) < 200:
        sys.exit(f"parsed only {len(communities)} Dubai communities")
    return {
        "_meta": {"source": list(AE_SRC.values()), "fetched": date.today().isoformat(),
                  "count": len(emirates) + len(communities),
                  "license": "derived from Wikipedia, CC BY-SA 4.0",
                  "by_kind": {"plate": AE_SRC["plates"], "area": AE_SRC["phone"], "admin": AE_SRC["dubai"]}},
        "country": "United Arab Emirates", "iso": "AE", "driving_side": "right",
        "admin1": emirates,
        "admin2": communities,
        "admin2_level": "district",
        "admin2_note": "only Dubai communities (with official community codes, as used in Dubai addresses); other emirates via OSM",
        "plates": AE_PLATES,
        "phone": AE_PHONE,
    }


# ---------------------------------------------------------------- United States

US_SRC = {
    "area": "https://en.wikipedia.org/wiki/List_of_North_American_Numbering_Plan_area_codes",
    "plates": "https://en.wikipedia.org/wiki/Vehicle_license_plates_of_the_United_States (per-state pages: infobox slogan and serial_format)",
}
# USPS codes (stable public standard)
US_STATES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA", "Colorado": "CO", "Connecticut": "CT",
    "Delaware": "DE", "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL",
    "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT",
    "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}
US_PLATE_TITLE = {"Georgia": "Georgia (U.S. state)", "New York": "New York", "Washington": "Washington (state)",
                  "District of Columbia": "the District of Columbia"}
# slogan fragments shared by many states or not printed as text: not usable as a marker
US_SLOGAN_SKIP = re.compile(r"^(none|county name|in god we trust|.*\d{4}.*|.*\.(gov|com|org)|\s*)$", re.I)


def _infobox_field(txt: str, field: str) -> str:
    m = re.search(r"^\|[ \t]*" + field + r"[ \t]*=[ \t]*(.*)$", txt, re.M)
    return m.group(1) if m else ""


def _fmt_regex(fmt: str) -> str | None:
    f = re.sub(r"\(.*?\)", "", fmt.replace("&nbsp;", " "))
    f = re.sub(r"^[^:]*:\s*", "", f).strip()  # "Yucca: 123-ABC"
    if not re.fullmatch(r"[A-Z0-9 \-·]{4,10}", f):
        return None
    out = ""
    for ch in f:
        out += r"\d" if ch.isdigit() else "[A-Z]" if ch.isalpha() else ""
    return "^" + out + "$"


def wiki_follow(title: str, from_dir, proxy) -> str:
    txt = wiki(title, from_dir, proxy)
    m = re.match(r"#REDIRECT\s*\[\[([^\]#]+)", txt, re.I)
    return wiki(m.group(1).strip().replace(" ", "_"), from_dir, proxy) if m else txt


def build_us(from_dir: str | None, proxy: str | None) -> dict:
    import time
    txt = wiki("List_of_North_American_Numbering_Plan_area_codes", from_dir, proxy)
    # numeric list: code -> description of the numbering plan area
    desc = {}
    for row in re.split(r"\n\|-", txt.split("== Area codes by country")[0]):
        cells = [c for c in re.split(r"\n\|", "\n" + row.strip()) if c.strip()]
        if len(cells) >= 2:
            code = _clean(cells[0]).strip("'")
            if re.fullmatch(r"\d{3}", code):
                desc[code] = _clean(cells[1])
    sec = txt.split("=== United States ===")[1].split("=== Canada ===")[0]
    area = []
    for row in re.split(r"\n\|-", sec):
        m = re.match(r"\s*\|\s*\[\[(?:[^|\]]*\|)?([^\]]*)\]\].*?\|\|(.*)", row.strip(), re.S)
        if not m:
            continue
        state = m.group(1).strip()
        for code in re.findall(r"\|(\d{3})\]\]", m.group(2)):
            area.append({"prefix": code, "admin1": [state], "place": desc.get(code, "")})
    nongeo = [{"prefix": c, "note": "toll-free, nationwide"} for c in ("800", "833", "844", "855", "866", "877", "888")]
    nongeo += [{"prefix": "900", "note": "premium rate"}, {"prefix": "500", "note": "personal communications, non-geographic"}]

    plates, admin1 = [], []
    for state, usps in US_STATES.items():
        admin1.append({"name": state, "name_local": "", "iso": f"US-{usps}", "capital": "", "aliases": [usps]})
        title = "Vehicle_registration_plates_of_" + US_PLATE_TITLE.get(state, state).replace(" ", "_")
        try:
            pt = wiki_follow(title, from_dir, proxy)
        except SystemExit:
            print(f"  no plate page for {state}", file=sys.stderr)
            continue
        if not from_dir:
            time.sleep(0.4)
        raw_sl = re.split(r"<br\s*/?>", _infobox_field(pt, "slogan"), flags=re.I)
        # drop slogans no longer issued: "(1998-2001)" style closed ranges; keep "(2011-present)"
        raw_sl = [s for s in raw_sl if not re.search(r"\(\s*\d{4}\s*[-–]\s*\d{4}\s*\)", s)]
        slog = [re.sub(r"\s*\(.*?\)\s*$", "", _clean(s)).strip(' "') for s in raw_sl]
        slog = [s for s in slog if s and not s.endswith(":") and not s.startswith(("|", "{")) and not US_SLOGAN_SKIP.match(s)]
        fmts = [re.sub(r"\(.*?\)", "", _clean(s)).replace("&nbsp;", " ").strip() for s in re.split(r"<br\s*/?>", _infobox_field(pt, "serial_format"), flags=re.I)]
        rx = sorted({r for r in (_fmt_regex(f) for f in fmts) if r})
        plates.append({"admin1": state, "markers": [state.upper()] + [s.upper() for s in slog], "code_kind": "format",
                       "formats": [f for f in fmts if f], "format_regex": rx, "codes": [], "digits": 9,
                       "note": ("slogans: " + "; ".join(slog) if slog else "") + ("; formats: " + ", ".join(f for f in fmts if f) if fmts else "")})
    return {
        "_meta": {"source": [US_SRC["area"], US_SRC["plates"]], "fetched": date.today().isoformat(),
                  "count": len(area) + len(plates), "license": "derived from Wikipedia, CC BY-SA 4.0",
                  "by_kind": {"plate": US_SRC["plates"], "area": US_SRC["area"], "admin": "USPS state codes"}},
        "country": "United States", "iso": "US", "driving_side": "right",
        "admin1": admin1, "admin2": [], "admin2_level": "county",
        "admin2_note": "counties not tabled; use board.py children <state> (OSM)",
        "plates": plates,
        "phone": {"calling_code": "1", "trunk": "1", "scheme": "nanp", "area": area, "mobile": [], "special": nongeo},
    }


# ---------------------------------------------------------------- Russia

RU_SRC = {
    "plates": "https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Russia",
    "phone": "https://en.wikipedia.org/wiki/Telephone_numbers_in_Russia",
}
BOLD_CODE = re.compile("'''" + r"\(?(\d{2,3})")
# names differ between the plates page and the phone page; map phone-page names to plate-page names
RU_NAME_FIX = {"Moscow City": "Moscow", "St. Petersburg": "Saint Petersburg", "Khanty–Mansi Autonomous Okrug": "Khanty-Mansi Autonomous Okrug",
               "Republic of Chechnya": "Chechen Republic", "Republic of Chuvashia": "Chuvash Republic",
               "Republic of Kabardino-Balkaria": "Kabardino-Balkar Republic", "Republic of Karachay–Cherkessia": "Karachay-Cherkess Republic",
               "Republic of Mari El": "Mari El Republic", "Republic of Tyva (Tuva)": "Tuva Republic", "Republic of Udmurtia": "Udmurt Republic",
               "Sakha Republic (Yakutia)": "Sakha Republic"}


def _ru_name(cell: str) -> str:
    v = _clean(cell).replace("&nbsp;", " ").strip("'* ")
    v = re.sub(r"\s+", " ", v)
    return RU_NAME_FIX.get(v, v)


def build_ru(from_dir: str | None, proxy: str | None) -> dict:
    pt = wiki("Vehicle_registration_plates_of_Russia", from_dir, proxy)
    sec = pt.split("==Regional codes==")[1].split("==Codes of diplomatic")[0]
    region_codes: dict[str, list[str]] = {}
    for row in re.split(r"\n\|-", sec):
        cells = [c for c in re.split(r"\n\|", "\n" + row.strip()) if c.strip()]
        if len(cells) < 2 or "colspan" in cells[0]:
            continue
        codes = BOLD_CODE.findall(cells[0])
        name = _ru_name(cells[1])
        if not codes or not name or name.lower().startswith(("initially", "internationally")):
            continue
        region_codes.setdefault(name, []).extend(codes)
    ph = wiki("Telephone_numbers_in_Russia", from_dir, proxy)
    geo = ph.split("=== Geographic area codes ===")[1].split("===Russian mobile")[0]
    area = []
    for row in re.split(r"\n\s*\|-", geo):
        cells = [c.strip() for c in re.split(r"\|\|", row.strip().lstrip("|"))]
        if len(cells) < 2:
            continue
        codes = re.findall(r"\b(\d{3,4})\b", _clean(cells[1].split("|")[-1]))
        if not codes:
            continue
        names = [_ru_name(n.split("|")[-1]) for n in re.findall(r"\[\[([^\]]+)\]\]", cells[0])] or [_ru_name(cells[0])]
        for c in codes:
            area.append({"prefix": c, "admin1": names, "place": ", ".join(names)})
    plates = [{"admin1": n, "markers": [], "code_kind": "region", "codes": c, "digits": 3, "note": "region codes " + ", ".join(c)}
              for n, c in region_codes.items()]
    admin1 = [{"name": n, "name_local": "", "iso": "", "capital": "", "aliases": []} for n in region_codes]
    return {
        "_meta": {"source": [RU_SRC["plates"], RU_SRC["phone"]], "fetched": date.today().isoformat(),
                  "count": len(plates) + len(area), "license": "derived from Wikipedia, CC BY-SA 4.0",
                  "by_kind": {"plate": RU_SRC["plates"], "area": RU_SRC["phone"], "admin": RU_SRC["plates"]}},
        "country": "Russia", "iso": "RU", "driving_side": "right",
        "admin1": admin1, "admin2": [], "admin2_level": "district",
        "admin2_note": "districts not tabled; use board.py children <subject> (OSM)",
        "plates": plates,
        "phone": {"calling_code": "7", "trunk": "8", "scheme": "ru", "area": area,
                  "mobile": [{"prefix": "9", "note": "mobile (9xx), not tied to a place"}],
                  "special": [{"prefix": "800", "note": "toll-free, nationwide"}, {"prefix": "809", "note": "premium rate"}]},
    }


# ---------------------------------------------------------------- Europe

B3 = "'''"


def _meta(sources: dict, n: int) -> dict:
    src = list(sources.values())
    return {"source": src, "fetched": date.today().isoformat(), "count": n, "license": "derived from Wikipedia, CC BY-SA 4.0",
            "by_kind": {"plate": sources.get("plates", src[0]), "area": sources.get("phone", src[0]), "admin": sources.get("admin", src[0])}}


def build_eu(from_dir, proxy) -> dict:
    """Distinguishing sign (blue EU band / oval sticker) -> country."""
    src = {"plates": "https://en.wikipedia.org/wiki/International_vehicle_registration_code"}
    iso = {}
    for m in re.finditer(r"\{\{mono\|([A-Z]{3})\}\}(?:&nbsp;)*\s*\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", wiki("ISO_3166-1_alpha-3", from_dir, proxy)):
        iso[m.group(1)] = m.group(2)
    txt = wiki("International_vehicle_registration_code", from_dir, proxy).split("== Current codes ==")[1].split("\n|}")[0]
    plates = []
    for row in re.split(r"\n\|-", txt):
        cells = [c.strip() for c in re.split(r"\n\|", "\n" + row.strip()) if c.strip()]
        if len(cells) < 2 or not re.fullmatch(r"[A-Z]{1,4}", _clean(cells[0])):
            continue
        m = re.search(r"\{\{([A-Z]{3})\}\}", cells[1])
        name = iso.get(m.group(1)) if m else _clean(re.sub(r"\{\{flag\|([^|}]*).*?\}\}", r"\1", cells[1]))
        if name:
            plates.append({"admin1": name, "markers": [], "code_kind": "band", "codes": [_clean(cells[0])], "digits": 9, "note": "distinguishing sign"})
    return {"_meta": _meta(src, len(plates)), "country": "Europe (distinguishing signs)", "iso": "EU", "driving_side": "",
            "admin1": [{"name": p["admin1"], "name_local": "", "iso": p["codes"][0], "capital": "", "aliases": []} for p in plates],
            "admin2": [], "admin2_level": "district", "plates": plates, "phone": {"calling_code": "", "trunk": "", "area": []}}


def build_de(from_dir, proxy) -> dict:
    src = {"plates": "https://de.wikipedia.org/wiki/Liste_der_Kfz-Kennzeichen_in_Deutschland"}
    txt = wiki("Liste_der_Kfz-Kennzeichen_in_Deutschland", from_dir, proxy)
    codes: dict[str, dict] = {}
    cur = None
    for row in re.split(r"\n\|-[^\n]*", txt):
        cells = [c for c in re.split(r"\n\|", "\n" + row.strip()) if c.strip()]
        if not cells:
            continue
        first = re.sub(r"rowspan=\"?\d+\"?\s*\|", "", cells[0]).strip()
        m = re.fullmatch(B3 + r"(?:\[\[[^|\]]*\|)?([A-ZÄÖÜ]{1,3})(?:\]\])?" + B3, first)
        if m:
            cur = m.group(1)
            ent = codes.setdefault(cur, {"districts": [], "state": ""})
            if len(cells) > 1:
                ent["districts"].append(_clean(cells[1]))
            if len(cells) > 3:
                ent["state"] = _clean(re.sub(r"rowspan=\"?\d+\"?\s*\|", "", cells[-1]))
        elif cur and len(cells) == 1 and not first.startswith(("{", "!")):
            codes[cur]["districts"].append(_clean(first))
    for v in codes.values():  # "Region Hannover\n* Stadt Hannover\n* übrige Region" -> keep the first line
        v["districts"] = [re.split(r"\n|\*", x)[0].strip(" ,") for x in v["districts"]]
    plates = [{"admin1": v["state"], "admin2_list": [d for d in v["districts"] if d], "markers": [], "code_kind": "district",
               "codes": [k], "digits": 9, "note": "; ".join(d for d in v["districts"] if d)} for k, v in codes.items() if v["state"]]
    states = sorted({p["admin1"] for p in plates})
    return {"_meta": _meta(src, len(plates)), "country": "Germany", "iso": "DE", "driving_side": "right",
            "admin1": [{"name": s, "name_local": s, "iso": "", "capital": "", "aliases": []} for s in states],
            "admin2": [{"name": d, "name_local": d, "admin1": p["admin1"], "code": p["codes"][0], "sector": ""} for p in plates for d in p["admin2_list"]],
            "admin2_level": "district", "plates": plates, "phone": {"calling_code": "49", "trunk": "0", "area": []}}


def build_fr(from_dir, proxy) -> dict:
    src = {"admin": "https://en.wikipedia.org/wiki/Departments_of_France", "phone": "https://en.wikipedia.org/wiki/Telephone_numbers_in_France"}
    txt = wiki("Departments_of_France", from_dir, proxy)
    txt = txt[txt.index("[[INSEE code]]"):]
    txt = txt[:txt.index("\n|}")]  # current departments table only (later tables list former departments)
    deps, carry = [], ("", 0)
    for row in re.split(r"\n\|-", txt):
        m = re.match(r"\s*!scope=\"row\"[^|]*\|\s*(\d{2}[A-Z]?|2[AB]|97\d)\s*\n(.*)", row.strip(), re.S)
        if not m:
            continue
        raw_cells = [c for c in re.split(r"\n\|", "\n" + m.group(2)) if c.strip() and "File:" not in c]
        cells, flag_i, span = [], None, 1
        for c in raw_cells:
            rs = re.match(r"^\s*rowspan=\"?(\d+)\"?\s*\|", c)
            body = c[rs.end():] if rs else c
            if re.search(r"\b1[789]\d\d\s*$|\b20\d\d\s*$", _clean(body)):
                continue  # date of establishment
            if re.search(r"\{\{flag\w*\|", body) and flag_i is None:
                flag_i, span = len(cells), int(rs.group(1)) if rs else 1
            cells.append(body)
        if flag_i is not None and flag_i >= 2:
            region = re.search(r"\{\{flag\w*\|([^|}]+)", cells[flag_i]).group(1)
            carry = (region, span - 1)
            name, cap = cells[flag_i - 2], cells[flag_i - 1]
        elif carry[1] > 0 and len(cells) >= 2:  # region cell spans from an earlier row
            region = carry[0]
            carry = (region, carry[1] - 1)
            name, cap = cells[0], cells[1]
        else:
            continue
        deps.append({"code": m.group(1), "name": _clean(name).rstrip("]").strip(), "capital": _clean(cap), "region": region})
    plates = [{"admin1": d["region"], "admin2": d["name"], "markers": [], "code_kind": "department", "codes": [d["code"]], "digits": 9,
               "note": f"department {d['code']} {d['name']} (capital {d['capital']}); the number on French plates is chosen by the owner"} for d in deps]
    area = [{"prefix": "01", "admin1": ["Île-de-France"], "place": "Paris and Île-de-France"},
            {"prefix": "02", "admin1": ["Normandy", "Brittany", "Pays de la Loire", "Centre-Val de Loire", "Réunion", "Mayotte"], "place": "north-west France (and Réunion, Mayotte); region list approximate, zone edges do not follow regions"},
            {"prefix": "03", "admin1": ["Hauts-de-France", "Grand Est", "Bourgogne-Franche-Comté"], "place": "north-east France; region list approximate, zone edges do not follow regions"},
            {"prefix": "04", "admin1": ["Auvergne-Rhône-Alpes", "Provence-Alpes-Côte d'Azur", "Occitanie", "Corsica"], "place": "south-east France and Corsica; region list approximate, zone edges do not follow regions"},
            {"prefix": "05", "admin1": ["Nouvelle-Aquitaine", "Occitanie", "Guadeloupe", "Martinique", "French Guiana"], "place": "south-west France (and the Antilles, Guiana); region list approximate, zone edges do not follow regions"}]
    regions = sorted({d["region"] for d in deps})
    return {"_meta": _meta(src, len(deps)), "country": "France", "iso": "FR", "driving_side": "right",
            "admin1": [{"name": r, "name_local": r, "iso": "", "capital": "", "aliases": []} for r in regions],
            "admin2": [{"name": d["name"], "name_local": d["name"], "admin1": d["region"], "code": d["code"], "sector": d["capital"]} for d in deps],
            "admin2_level": "district", "plates": plates,
            "phone": {"calling_code": "33", "trunk": "0", "area": area,
                      "mobile": [{"prefix": "06", "note": "mobile"}, {"prefix": "07", "note": "mobile"}],
                      "special": [{"prefix": "08", "note": "special-rate, nationwide"}, {"prefix": "09", "note": "VoIP/box, nationwide"}]}}


def build_gb(from_dir, proxy) -> dict:
    src = {"plates": "https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_the_United_Kingdom"}
    txt = wiki("Vehicle_registration_plates_of_the_United_Kingdom", from_dir, proxy)
    sec = txt.split("==== Local memory tags ====")[1].split("\n|}")[0]
    tags: dict[str, dict] = {}
    first = mnem = ""
    for row in re.split(r"\n\|-[^\n]*", sec):
        cells = [c for c in re.split(r"\n\|", "\n" + row.strip()) if c.strip()]
        cells = [re.sub(r"\{\{rh\}\}|rowspan=\"?\d+\"?|class=\"[^\"]*\"", "", c).strip().lstrip("|").strip() for c in cells]
        if len(cells) >= 4 and re.fullmatch(r"[A-Z]", _clean(cells[0])):
            first, mnem = _clean(cells[0]), _clean(cells[1])
            office, seconds = _clean(cells[2]), cells[3]
        elif len(cells) == 2 and first:
            office, seconds = _clean(cells[0]), cells[1]
        else:
            continue
        if "reserved" in office.lower():
            continue
        for s in re.findall(r"\b([A-Z])\b", _clean(seconds)):
            tags[first + s] = {"office": office, "area": mnem}
    plates = [{"admin1": v["area"], "markers": [], "code_kind": "memory", "codes": [k], "digits": 9,
               "note": f"DVLA office {v['office']} (registration office, not necessarily where the car is)"} for k, v in tags.items()]
    areas = sorted({p["admin1"] for p in plates})
    return {"_meta": _meta(src, len(plates)), "country": "United Kingdom", "iso": "GB", "driving_side": "left",
            "admin1": [{"name": a, "name_local": a, "iso": "", "capital": "", "aliases": []} for a in areas],
            "admin2": [], "admin2_level": "district", "plates": plates, "phone": {"calling_code": "44", "trunk": "0", "area": []}}


def build_it(from_dir, proxy) -> dict:
    src = {"plates": "https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Italy"}
    txt = wiki("Vehicle_registration_plates_of_Italy", from_dir, proxy)
    sec = txt.split("=== Province codes 1927 to present day ===")[1].split("\n|}")[0]
    prov = {}
    for line in sec.splitlines():
        for m in re.finditer(B3 + r"([A-Z]{2})" + B3 + r"\s*\|\|\s*((?:\[\[[^\]]*\]\]|[^|\[])+)", line):
            prov[m.group(1)] = _clean(m.group(2)).split(" / ")[0].strip()
    prov["ROMA"] = "Rome"  # Rome's band shows the word ROMA instead of a two-letter code
    plates = [{"admin1": v, "markers": [], "code_kind": "province", "codes": [k], "digits": 9,
               "note": "province sticker on the right blue band (optional since 1999; older plates show it on the plate)"} for k, v in prov.items()]
    return {"_meta": _meta(src, len(plates)), "country": "Italy", "iso": "IT", "driving_side": "right",
            "admin1": [{"name": v, "name_local": v, "iso": k, "capital": "", "aliases": []} for k, v in prov.items()],
            "admin2": [], "admin2_level": "district", "plates": plates, "phone": {"calling_code": "39", "trunk": "0", "area": []}}


BUILDERS = {"ae": build_ae, "us": build_us, "ru": build_ru, "eu": build_eu, "de": build_de, "fr": build_fr, "gb": build_gb, "it": build_it}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("country", help="country code (ae) or 'list'")
    ap.add_argument("--from-dir")
    ap.add_argument("--proxy", default=os.environ.get("GEO_PROXY"))
    a = ap.parse_args()
    if a.country == "list":
        print(", ".join(BUILDERS))
        return
    cc = a.country.lower()
    if cc not in BUILDERS:
        sys.exit(f"no builder for {cc}; have: {', '.join(BUILDERS)}")
    d = BUILDERS[cc](a.from_dir, a.proxy)
    DATA.mkdir(parents=True, exist_ok=True)
    f = DATA / f"{cc}.json"
    f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{cc}: admin1 {len(d['admin1'])}, admin2 {len(d['admin2'])}, plates {len(d['plates'])} -> {f}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
