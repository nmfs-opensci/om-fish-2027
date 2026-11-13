# Handoff: om-fish-2027

Rolling session state for coding agents. Read this first. It records what has
been happening, not what to do next; Eli says what she wants done.

## Repo

`nmfs-opensci/om-fish-2027`: website (Jupyter Book, from the uwhackweek
template) for OM-Fish HackWeek 2027, plus MOM6 reports under `reports/`.

## Recently shipped

- **Issue #4 (closed), PR #5 (merged), 2026-11-12:**
  `reports/mom6-evaluation-synthesis.md` and its PDF. It summarizes how West
  Coast colleagues have used and evaluated CEFI MOM6-NEP10k, written for Jameal
  as an overview of who compares what and which comparisons match. Appendix A
  lists the commits reviewed in the four colleague repos (esr indices,
  groundfish indices, oc_cciea, subsurface_heatwaves).
- **PR #7, "Reuse and citation" (open as of 2026-11-12, not merged):** adds a
  README reuse section and a `CITATION.cff`. Eli chose the "please cite" form.
  The license stays MIT, inherited from the template.

## Open threads

- **Issue #6:** tutorials from Appendix C of the report (18 candidates, core
  sequence 1, 2, 5, 6, 8, 9, 13, 15). Undecided: order, R vs. Python, and
  where the book lives.
- Issues #2 ("references") and #3 ("planning") predate this work.

## Working principles

- **The PDF is a render of the Markdown.** After editing the report, run
  `reports/tools/render_pdf.sh` (Quarto with Typst). It writes
  `reports/mom6-evaluation-synthesis.pdf`. `prep_pdf.py` fixes table column
  widths, makes paths in tables wrap, and adds blank lines before lists.
  `header.yml` holds the page and font settings.
- **The Seaside Chat slides PDF** (`CC-ESR-Seaside-Chat-*.pdf`) stays local and
  untracked; it is listed in `.git/info/exclude`.
- **The Earthmover store** (`NOAA-PMEL/cefi-nep-hindcast-monthly`) is a draft,
  not production. Shared reports may say this lightly but must not cite Eli's
  CEFI audit (see project memory).
- **Dates:** use Pacific time. The hub clock is UTC.
