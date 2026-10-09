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


def _clean(cell: str) -> str:
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


BUILDERS = {"ae": build_ae, "us": build_us}


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
