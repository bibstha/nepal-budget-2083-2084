#!/usr/bin/env python3
"""Flow-corrected Unicode Devanagari HTML from the OCR'd finance bill.

Unlike generate_nepali.py (which rendered each PDF page independently and so
split clauses at every blank line and page break), this streams the whole
document continuously: a fragment joins the running paragraph across blank
lines AND page boundaries unless the paragraph already closed with sentence
punctuation or the next line opens a new clause. Tariff tables merge across
pages into one continuous table.

Usage: generate_nepali_flow.py SRC.pdf OUT.html [first] [last]
"""
import subprocess, sys, re, html

SRC = sys.argv[1]
OUT = sys.argv[2]
FIRST = int(sys.argv[3]) if len(sys.argv) > 3 else 1
LAST = int(sys.argv[4]) if len(sys.argv) > 4 else 0

DIG = "०-९"        # devanagari digits 0-9
CONS = "क-हक़-य़"  # consonants
I_MATRA = "ि"        # i-matra
RE_ISPLIT = re.compile(f"({I_MATRA}) +([{CONS}])")

def fix_dev(s):
    prev = None
    while prev != s:
        prev = s
        s = RE_ISPLIT.sub(r"\1\2", s)
    return re.sub(r"[ \t]{2,}", " ", s).strip()

# a line that OPENS a new clause: "१.", "(१)", "(१क)", "(2)", "(क)"
RE_MARKER = re.compile(f"^\\s*(\\([{DIG}0-9]+[क-ह]?\\)|[{DIG}0-9]+\\.|\\([क-ह]\\))")
# sentence already closed
RE_SENTEND = re.compile(r"[।|:]\s*$")
# pure scan-noise line (no Devanagari, short) or a far-indented stray number
RE_PUREJUNK = re.compile(r"^[\s~`'^_|.\-—)(*ऀ-ःoO0-9]{1,4}$")
def is_devanagari(c): return "ऀ" <= c <= "ॿ"
def junk_line(t, indent):
    s = t.strip()
    if not s:
        return False
    if re.fullmatch(f"[{DIG}0-9]{{1,3}}", s):
        return True                       # bare printed page number: १५, १०१, १
    if not any(is_devanagari(c) for c in s) and len(s) <= 4:
        return True                       # "ay", "~~)", "N"
    return False

# HS heading: 84.70 / 0904.11.30
RE_HS = re.compile(f"^\\s*[{DIG}0-9]{{2,4}}[.।]([{DIG}0-9]{{1,2}}[.।]?){{0,2}}\\s*[|]?")
RE_TRAIL_RATE = re.compile(f"([{DIG}0-9]{{1,3}})\\s*$")

def is_table_page(lines):
    ne = [l for l in lines if l.strip()]
    if not ne:
        return None  # blank
    hits = sum(1 for l in ne if RE_HS.match(l))
    return "table" if (hits >= 3 and hits / len(ne) >= 0.20) else "prose"

def extract():
    a = ["pdftotext", "-f", str(FIRST)]
    if LAST: a += ["-l", str(LAST)]
    a += ["-layout", SRC, "-"]
    out = subprocess.run(a, capture_output=True).stdout.decode("utf-8", "replace")
    return out.split("\f")

pages = extract()
# (pageno, kind, lines); blank pages kept as kind=None — they mark a hard
# section boundary (e.g. the blank page between the title, the objectives and
# the act), so content on either side must NOT flow together.
catalog = []
for i, raw in enumerate(pages):
    pageno = FIRST + i
    if not raw.strip():
        catalog.append((pageno, None, None))
        continue
    lines = raw.split("\n")
    catalog.append((pageno, is_table_page(lines), lines))

# group consecutive same-kind pages into segments; a blank page forces a break
segments = []
force_new = True
for pageno, kind, lines in catalog:
    if kind is None:
        force_new = True
        continue
    if not force_new and segments and segments[-1][0] == kind:
        segments[-1][1].append((pageno, lines))
    else:
        segments.append((kind, [(pageno, lines)]))
    force_new = False

def esc(s): return html.escape(s)
MARK = "\x00%d\x00"  # page-boundary sentinel placed inline
def render_marks(s):
    return re.sub(r"\x00(\d+)\x00", r"<sup class='pg'>\1</sup>", s)

def emphasize(p):
    # bold a leading section number or "(n)" marker
    return re.sub(r"^(\([^)]{1,5}\)|[०-९]+\.)", r"<b>\1</b>", p)

def render_prose(seg_pages):
    out, buf, pending = [], [], []
    break_pending = False

    def buftext():
        return re.sub(r"\x00\d+\x00", "", " ".join(buf)).strip()

    def flush():
        if not buf:
            return
        parts = re.split(r"(\x00\d+\x00)", fix_dev(" ".join(buf)))
        txt = "".join(
            f"<sup class='pg'>{p[1:-1]}</sup>" if (len(p) > 2 and p[0] == "\x00" and p[-1] == "\x00")
            else esc(p)
            for p in parts)
        out.append("<p>" + emphasize(txt) + "</p>")
        buf.clear()

    for pageno, lines in seg_pages:
        pending.append(MARK % pageno)
        for ln in lines:
            indent = len(ln) - len(ln.lstrip(" "))
            s = ln.strip()
            if not s:
                break_pending = True
                continue
            if junk_line(s, indent):
                continue
            starts = bool(RE_MARKER.match(ln))
            ends = bool(RE_SENTEND.search(buftext()))
            if buf and (starts or (break_pending and ends)):
                flush()
            if pending:
                buf.extend(pending); pending = []
            buf.append(s)
            break_pending = False
    flush()
    return "\n".join(out)

def render_table(seg_pages):
    rows, cur = [], None
    for pageno, lines in seg_pages:
        rows.append(("PAGE", pageno))
        for ln in lines:
            if not ln.strip():
                continue
            m = RE_HS.match(ln)
            if m:
                rest = ln[m.end():].strip().lstrip("|").strip()
                rate = ""
                rm = RE_TRAIL_RATE.search(rest)
                if rm:
                    rate = rm.group(1); rest = rest[:rm.start()].strip()
                code = m.group(0).strip().rstrip("|").strip()
                cur = ["ROW", code, rest, rate]; rows.append(cur)
            else:
                t = ln.strip()
                if cur is None:
                    cur = ["ROW", "", t, ""]; rows.append(cur)
                else:
                    rm = RE_TRAIL_RATE.search(t)
                    if rm and not cur[3]:
                        cur[3] = rm.group(1); t = t[:rm.start()].strip()
                    cur[2] = (cur[2] + " " + t).strip()
    body = ["<table><thead><tr><th>शीर्षक</th><th>वस्तुको विवरण</th>"
            "<th>दर</th></tr></thead><tbody>"]
    for r in rows:
        if r[0] == "PAGE":
            body.append(f"<tr class='pgrow'><td colspan='3'>पृष्ठ {r[1]}</td></tr>")
        else:
            _, code, desc, rate = r
            body.append(f"<tr><td class='code'>{esc(fix_dev(code))}</td>"
                        f"<td>{esc(fix_dev(desc))}</td>"
                        f"<td class='rate'>{esc(fix_dev(rate))}</td></tr>")
    body.append("</tbody></table>")
    return "\n".join(body)

HEAD = """<!doctype html><html lang="ne"><head><meta charset="utf-8">
<title>आर्थिक विधेयक, २०८३ — पुनर्संरचित पाठ</title>
<style>
:root{ --ink:#16181d; }
body{ font-family:'Kohinoor Devanagari','Devanagari Sangam MN',serif;
      font-size:12pt; line-height:1.95; color:var(--ink);
      max-width:820px; margin:0 auto; padding:36px 28px 80px; }
h1{ font-size:18pt; text-align:center; margin:0 0 4px; }
.sub{ text-align:center; color:#888; font-family:sans-serif; font-size:9.5pt; margin-bottom:30px; }
p{ margin:0 0 12px; text-align:justify; }
sup.pg{ color:#c0c4cc; font-size:7.5pt; font-family:sans-serif; padding:0 1px; }
table{ width:100%; border-collapse:collapse; font-size:10.5pt; line-height:1.55; margin:14px 0; }
th,td{ border:1px solid #d7d9de; padding:4px 7px; vertical-align:top; }
th{ background:#f4f5f7; }
td.code{ white-space:nowrap; width:96px; font-variant-numeric:tabular-nums; }
td.rate{ text-align:center; width:50px; }
tr.pgrow td{ background:#fafbfc; color:#b6bac2; font-family:sans-serif;
             font-size:8pt; text-align:right; border-left:none; border-right:none; padding:2px 7px; }
.note{ font-family:sans-serif; font-size:9pt; color:#8a8f98; border-top:1px solid #eee;
       margin-top:48px; padding-top:12px; }
</style></head><body>
<h1>आर्थिक विधेयक, २०८३</h1>
<div class="sub">OCR बाट पुनःप्राप्त नेपाली पाठ — प्रवाह सच्याइएको (निरन्तर) संस्करण</div>
"""
parts = [HEAD]
for kind, seg_pages in segments:
    if kind == "table":
        parts.append(render_table(seg_pages))
    else:
        parts.append(render_prose(seg_pages))
parts.append('<div class="note">अनौपचारिक, OCR-आधारित पुनर्संरचना। सुपरस्क्रिप्ट अङ्कहरूले '
             'मूल पृष्ठ सङ्ख्या जनाउँछन्। कानूनी प्रयोजनका लागि मूल कागजातसँग भिडाउनुहोस्।</div>')
parts.append("</body></html>")
open(OUT, "w", encoding="utf-8").write("\n".join(parts))
sys.stderr.write(f"segments={len(segments)} "
                 f"prose={sum(1 for k,_ in segments if k=='prose')} "
                 f"table={sum(1 for k,_ in segments if k=='table')}\n")
