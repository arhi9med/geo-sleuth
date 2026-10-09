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


BUILDERS = {"ae": build_ae}


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
