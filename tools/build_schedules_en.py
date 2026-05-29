#!/usr/bin/env python3
"""Render the finance bill's tariff/exemption SCHEDULES as English HS-code+rate tables.

Per the chosen approach: the schedules are reproduced as (HS code, rate) tables
with Devanagari numerals converted to Latin. Per-line product descriptions are
NOT translated row-by-row — they follow the standard Harmonized System (HS)
nomenclature for each HS code (full Nepali descriptions are in the companion
Nepali markdown). Annex titles and group headers are carried across with light
translation of the structural words.

Usage: build_schedules_en.py NEPALI.md OUT.md FIRST_LINE
"""
import sys, re

SRC, OUT, FIRST = sys.argv[1], sys.argv[2], int(sys.argv[3])
lines = open(SRC, encoding="utf-8").read().split("\n")[FIRST - 1:]

DEV2LAT = str.maketrans("०१२३४५६७८९", "0123456789")
def lat(s): return s.translate(DEV2LAT)

# structural word translations for headings/labels
SUBST = [
    ("अनुसूची", "Annex"), ("समूह", "Group"), ("दफा", "Section"),
    ("उपदफा", "sub-section"), ("सँग सम्बन्धित", "— related to"),
    ("को सट्टा देहायको", ""), ("राखिएको छ", ""), ("राखि एको छ", ""),
    ("कर छुट हुने वस्तु तथा सेवा", "Tax-exempt goods and services"),
]
def soften(s):
    for a, b in SUBST:
        s = s.replace(a, b)
    return re.sub(r"\s{2,}", " ", s).strip(" :-")

HS_RE = re.compile(r"^[०-९0-9]{2,4}[.।][०-९0-9.।]*$|^[०-९0-9]{2,4}$")

out = ["<!-- AUTO-GENERATED schedules: HS code + rate. See build_schedules_en.py. -->", ""]
in_table = False
rows = []

def flush_table():
    global rows, in_table
    if rows:
        out.append("| HS Code | Rate |")
        out.append("| --- | ---: |")
        out.extend(rows)
        out.append("")
        rows = []
    in_table = False

for ln in lines:
    s = ln.strip()
    if not s:
        continue
    # table separator / header rows from the source — skip
    if re.match(r"^\|\s*शीर्षक", s) or re.match(r"^\|\s*-{2,}", s):
        in_table = True
        continue
    if s.startswith("|"):
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) >= 3:
            code, desc, rate = cells[0], cells[1], cells[2]
            # a group/category header row: no code, has text in desc
            if not code and desc:
                flush_table()
                out.append(f"**{soften(lat(desc))}**")
                out.append("")
                continue
            # tariff data row — keep HS code + a clean numeric rate only
            code_l = lat(code).strip()
            rm = re.search(r"\d{1,3}", lat(rate))
            rate_l = rm.group(0) if rm and re.fullmatch(r"[\s\d.%]+", lat(rate)) else ""
            if code_l or rate_l:
                rows.append(f"| {code_l} | {rate_l} |")
            continue
        else:
            continue
    # non-table line (annex title, note, leftover prose)
    flush_table()
    if "अनुसूची" in s:
        m = re.search(r"अनुसूची[-\s]*([०-९]+)", s)
        num = lat(m.group(1)) if m else ""
        out.append(f"### Annex {num}".rstrip())
    elif "Annex" in s:
        out.append(f"### {soften(lat(s))}")
    else:
        out.append(soften(lat(s)) if any('ऀ' <= c <= 'ॿ' for c in s) else lat(s))
    out.append("")

flush_table()
open(OUT, "w", encoding="utf-8").write("\n".join(out) + "\n")
sys.stderr.write(f"wrote {OUT}: {len(out)} lines\n")
