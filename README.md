# Nepal Budget — Fiscal Year 2083/84 (2026/27)

Machine-readable Nepali (Devanagari Unicode) and English versions of Nepal's
two core budget documents for **Fiscal Year 2083/84**, derived from the
official PDFs published by the Government of Nepal, Ministry of Finance.

The official PDFs are not usefully machine-readable: the **Finance Bill** is a
122 MB scan-like file in which every character is drawn as vector outlines (no
text layer at all), and the **Budget Speech** has a text layer whose font
Unicode map is corrupted (e.g. `आर्थिक` extracts as `आर्र्थक`, and characters are
silently dropped). This repository reconstructs clean, searchable text from
both, plus a working English translation.

## Documents

| Document | Nepali | What it is |
|---|---|---|
| **Finance Bill, 2083** (`आर्थिक विधेयक, २०८३`) | the statute | The legal instrument levying/amending taxes, duties, fees, and the customs/excise/VAT tariff schedules. ~461 pages, mostly tariff tables. |
| **Budget Speech, FY 2083/84** (`बजेट वक्तव्य`) | the speech | The budget actually delivered to Parliament by Finance Minister Dr. Swarnim Wagle. ~93 pages of prose. |

## Layout

```
finance-bill/
  finance-bill-2083-84-original.pdf   # original PDF, unmodified (Git LFS)
  finance-bill-2083-84-nepali.md      # reconstructed Devanagari Unicode, free-flowing
  finance-bill-2083-84-english.md     # English translation (in progress)
budget-speech/
  budget-speech-2083-84-original.pdf  # original PDF, unmodified
  budget-speech-2083-84-nepali.md     # reconstructed Devanagari Unicode, free-flowing
  budget-speech-2083-84-english.md    # English translation (in progress)
tools/
  generate_nepali_flow.py             # OCR text -> flow-corrected HTML
  flow_html_to_md.py                  # flow HTML -> Markdown
```

> The large original PDF is stored with **Git LFS** (`git lfs install` before cloning to fetch it).

## How the text was reconstructed

Because neither PDF yields correct text directly, both were processed with OCR:

1. **OCR** — pages rasterized and read with Tesseract (`nep+eng`, Devanagari).
2. **Flow correction** (`tools/generate_nepali_flow.py`) — the OCR output is
   re-flowed into continuous prose: fragments are rejoined across line and page
   breaks unless a sentence closed or a new clause began; the documents' own
   printed page numbers and scan noise are stripped; tariff pages are rebuilt as
   tables. A conservative Devanagari fix rejoins the systematic i-matra (ि)
   split (`प्रति शत` → `प्रतिशत`) without merging genuine word boundaries.
3. **Markdown** (`tools/flow_html_to_md.py`) — rendered to free-flowing Markdown.
4. **English** — translated from the cleaned Nepali.

## Accuracy and caveats

- These are **unofficial reconstructions**, not the authoritative legal text.
  For anything official, use the original PDFs / the Nepal Gazette.
- The Nepali is **OCR-derived**: expect occasional wrong characters, residual
  spacing artifacts (e.g. `कार्या न्वयन`), and noise — heaviest in numeric
  tariff tables. Always verify figures against the original.
- The English is a **machine-assisted translation** of OCR text — meaning is
  generally faithful, but legal/financial precision is not guaranteed.
- Status: Nepali reconstructions complete; English translations are being
  added in batches (see the 🚧 notes in each English file).

## Sources

- **Ministry of Finance (web page):** https://mof.gov.np/content/1741/budget8384/
- **Budget Speech — original PDF (Nepali):** https://giwmscdnone.gov.np/media/pdf_upload/budget%20speech%202083_nz9wmgt.pdf
- **Finance Bill — original PDF (Nepali, full details):** https://giwmscdnone.gov.np/media/pdf_upload/%E0%A4%86%E0%A4%B0%E0%A5%8D%E0%A4%A5%E0%A4%BF%E0%A4%95%20%E0%A4%B5%E0%A4%BF%E0%A4%A7%E0%A5%87%E0%A4%AF%E0%A4%95%2C%20%E0%A5%A8%E0%A5%A6%E0%A5%AE%E0%A5%A9%20_dkhaghj.pdf

## License / source

Source documents are public records of the Government of Nepal, Ministry of
Finance (mof.gov.np). This repository adds derived text and translations for
research and accessibility; it carries no official status.

## Disclaimer

The derived text, reconstructions, and English translations in this repository
were generated with the assistance of Claude (Claude.ai / Claude Code) by
Anthropic. They are **unofficial** and may contain errors. Verify them against
the official source documents listed above before any authoritative or legal
use.
