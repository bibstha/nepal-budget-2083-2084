#!/usr/bin/env python3
"""Convert a flow HTML (from generate_nepali_flow.py) to free-flowing Markdown.

Drops the inline page-number superscripts and per-page table separator rows so
the Markdown reads as one continuous document. Tables become Markdown tables.

Usage: flow_html_to_md.py IN.html OUT.md ["# Doc title"] ["subtitle"]
"""
import re, html, sys

IN, OUT = sys.argv[1], sys.argv[2]
TITLE = sys.argv[3] if len(sys.argv) > 3 else None
SUB = sys.argv[4] if len(sys.argv) > 4 else None
h = open(IN, encoding="utf-8").read()

def clean(t):
    t = re.sub(r"<sup class='pg'>\d+</sup>", "", t)   # drop page markers
    t = re.sub(r"<b>(.*?)</b>", r"**\1**", t, flags=re.S)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()

def cell(t):
    return clean(t).replace("|", r"\|")

def render_table(inner):
    out = ["| शीर्षक | वस्तुको विवरण | दर |", "| --- | --- | ---: |"]
    for tr in re.findall(r"<tr\b[^>]*>(.*?)</tr>", inner, re.S):
        if "<th" in tr or "pgrow" in tr or "colspan" in tr:
            continue
        tds = re.findall(r"<td\b[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) == 3:
            out.append(f"| {cell(tds[0])} | {cell(tds[1])} | {cell(tds[2])} |")
    return "\n".join(out)

md = []
t = TITLE or (clean(m.group(1)) and f"# {clean(m.group(1))}" if (m := re.search(r"<h1>(.*?)</h1>", h, re.S)) else None)
if isinstance(t, str):
    md.append(t if t.startswith("#") else f"# {t}")
sub = SUB or ((m := re.search(r'<div class="sub">(.*?)</div>', h, re.S)) and clean(m.group(1)))
if sub:
    md.append(f"*{sub}*")

for m in re.finditer(r"<p>(.*?)</p>|<table>(.*?)</table>", h, re.S):
    if m.group(1) is not None:
        txt = clean(m.group(1))
        if txt:
            md.append(txt)
    else:
        md.append(render_table(m.group(2)))

open(OUT, "w", encoding="utf-8").write("\n\n".join(md) + "\n")
sys.stderr.write(f"wrote {OUT}: {len(md)} blocks\n")
