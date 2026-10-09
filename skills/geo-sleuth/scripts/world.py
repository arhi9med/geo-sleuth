"""Per-country lookups outside China: plates, phone prefixes, admin divisions. Read by clues.py.

Tables live in data/world/<cc>.json (built by build_world.py). Output uses the same contract as clues.py:
  {"kind", "value", "matches": [{"country", "admin1", "admin2", "admin2_level", "note"}], "source", "table_fetched", "note"}
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

DATA = Path(__file__).parent.parent / "data" / "world"

# country names / codes that select a table
ALIASES = {
    "ae": ["ae", "are", "uae", "u.a.e", "united arab emirates", "emirates", "阿联酋", "阿拉伯联合酋长国", "оаэ", "эмираты"],
    "us": ["us", "usa", "u.s.", "u.s.a.", "united states", "united states of america", "america", "美国", "сша"],
}
# international calling code -> table, for auto-detecting "+971 4 ..." without --country
CALLING = {"971": "ae", "1": "us"}


def table_for(country: str | None) -> str | None:
    if not country:
        return None
    c = country.strip().lower()
    for cc, names in ALIASES.items():
        if c in names and (DATA / f"{cc}.json").exists():
            return cc
    return None


def available() -> list[str]:
    return sorted(p.stem for p in DATA.glob("*.json")) if DATA.exists() else []


def load(cc: str) -> dict:
    return json.loads((DATA / f"{cc}.json").read_text(encoding="utf-8"))


def _res(kind, value, matches, d, note=""):
    by = d["_meta"].get("by_kind") or {}
    src = by.get(kind) or by.get(kind.split("-")[0]) or d["_meta"]["source"][0]
    return {"kind": kind, "value": value, "matches": matches, "source": src,
            "table_fetched": d["_meta"]["fetched"], "note": note}


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^0-9a-z؀-ۿЀ-ӿ]+", " ", s.lower()).strip()


# ---------------------------------------------------------------- plates

def lookup_plate(cc: str, value: str) -> dict:
    d = load(cc)
    raw = value.upper()
    folded = " " + _fold(value) + " "
    # 1) a word printed on the plate names the region outright
    named = [r for r in d["plates"] if any(" " + _fold(m) + " " in folded for m in r["markers"])]
    if named:
        ms = [{"country": d["country"], "admin1": r["admin1"], "admin2": "", "note": "region printed on plate; " + r["note"]} for r in named]
        return _res("plate", value, ms, d)
    # 2a) format-based tables (US states): match the serial against each region's issued formats
    if any(r.get("code_kind") == "format" for r in d["plates"]):
        serial = re.sub(r"[^A-Z0-9]", "", raw)
        ms = [r for r in d["plates"] if any(re.match(rx, serial) for rx in r.get("format_regex", []))]
        note = "serial format shared by several regions: look for the region name, slogan or plate design" if len(ms) > 1 else \
            ("" if ms else "serial matches no current standard format (vanity, specialty, older series, or misread)")
        return _res("plate", value, [{"country": d["country"], "admin1": r["admin1"], "admin2": "", "note": r["note"][:160]} for r in ms], d, note)
    # 2b) otherwise narrow by the code: letters vs number, and which codes each region issues
    toks = re.findall(r"[A-Z]+|\d+", raw)
    nums = [t for t in toks if t.isdigit()]
    lets = [t for t in toks if t.isalpha()]
    serial = max(nums, key=len) if nums else ""
    code_num = next((t for t in nums if t != serial and len(t) <= 2), "")
    code_let = lets[0] if lets else ""
    ms = []
    for r in d["plates"]:
        if serial and len(serial) > r["digits"]:
            continue
        if r["code_kind"] == "letter" and code_let and code_let in r["codes"]:
            ms.append(r)
        elif r["code_kind"] == "number" and not code_let and (code_num in r["codes"]):
            ms.append(r)
    note = "" if ms else "code not issued by any region in the table (new series, special plate, or misread)"
    if ms and len(ms) > 1:
        note = "code shared by several regions: look for the region name, logo or plate colour"
    return _res("plate", value, [{"country": d["country"], "admin1": r["admin1"], "admin2": "", "note": r["note"]} for r in ms], d, note)


# ---------------------------------------------------------------- phone

def lookup_phone(cc: str, value: str) -> dict:
    d = load(cc)
    p = d["phone"]
    digits = re.sub(r"\D", "", value)
    if p.get("scheme") == "nanp":
        digits = digits[2:] if digits.startswith("00") else digits
        digits = digits[1:] if len(digits) == 11 and digits.startswith("1") else digits
        code = digits[:3]
        for s in p.get("special", []):
            if code == s["prefix"]:
                return _res("area-code", value, [{"country": d["country"], "note": s["note"]}], d, "nationwide number, no area")
        hits = [a for a in p["area"] if a["prefix"] == code]
        if not hits:
            return _res("area-code", value, [], d, "area code not in the US table (Canada, Caribbean, or not a NANP number)")
        return _res("area-code", value, [{"country": d["country"], "admin1": s, "admin2": "", "note": a["place"]} for a in hits for s in a["admin1"]], d,
                    "US numbers are portable: mobile numbers keep their area code after people move")
    for pre in ("00" + p["calling_code"], p["calling_code"]):
        if digits.startswith(pre) and len(digits) > len(pre) + 6:
            digits = p["trunk"] + digits[len(pre):]
            break
    if not digits.startswith(p["trunk"]) and not any(digits.startswith(s["prefix"]) for s in p.get("special", [])):
        digits = p["trunk"] + digits
    for s in p.get("special", []):
        if digits.startswith(s["prefix"]):
            return _res("area-code", value, [{"country": d["country"], "note": s["note"]}], d, "nationwide number, no area")
    for m in sorted(p.get("mobile", []), key=lambda x: -len(x["prefix"])):
        if digits.startswith(m["prefix"]):
            return _res("area-code", value, [{"country": d["country"], "note": f"mobile ({m['note']}); not tied to a place"}], d,
                        "mobile prefix: tells the country only")
    for a in sorted(p["area"], key=lambda x: -len(x["prefix"])):
        if digits.startswith(a["prefix"]):
            return _res("area-code", value, [{"country": d["country"], "admin1": r, "admin2": "", "note": a["place"]} for r in a["admin1"]], d)
    return _res("area-code", value, [], d, "prefix not in table")


# ---------------------------------------------------------------- admin

def _admin1_match(d: dict, name: str) -> dict | None:
    f = _fold(name)
    for e in d["admin1"]:
        if f in {_fold(x) for x in [e["name"], e.get("name_local", ""), e.get("iso", ""), *e.get("aliases", [])] if x}:
            return e
    return None


def lookup_admin(cc: str, value: str | None, children: str | None) -> dict:
    d = load(cc)
    lvl2 = d.get("admin2_level", "district")
    if children:
        if table_for(children) == cc or _fold(children) == _fold(d["country"]):
            return _res("admin-children", children, [{"country": d["country"], "admin1": e["name"], "admin2": "", "note": e.get("iso", "")}
                                                    for e in d["admin1"]], d)
        e = _admin1_match(d, children)
        if not e:
            return _res("admin-children", children, [], d, "unknown region name")
        kids = [k for k in d["admin2"] if k["admin1"] == e["name"]]
        note = "" if kids else d.get("admin2_note", "no subdivisions in table")
        return _res("admin-children", children, [{"country": d["country"], "admin1": e["name"], "admin2": k["name"], "admin2_level": lvl2,
                                                   "code": k.get("code", ""), "note": k.get("sector", "")} for k in kids], d, note)
    name = (value or "").strip()
    e = _admin1_match(d, name)
    if e:
        return _res("admin", name, [{"country": d["country"], "admin1": e["name"], "admin2": "", "chain": [d["country"], e["name"]]}], d)
    f = _fold(name)
    exact = [k for k in d["admin2"] if f in (_fold(k["name"]), _fold(k.get("name_local", "")), k.get("code", ""))]
    hits = exact or [k for k in d["admin2"] if f and f in _fold(k["name"])]
    ms = [{"country": d["country"], "admin1": k["admin1"], "admin2": k["name"], "admin2_level": lvl2, "code": k.get("code", ""),
           "chain": [d["country"], k["admin1"], k.get("sector", ""), k["name"]], "note": "" if k in exact else "partial name match"} for k in hits]
    return _res("admin", name, ms, d, "" if ms else "not in table (" + d.get("admin2_note", "") + ")")
