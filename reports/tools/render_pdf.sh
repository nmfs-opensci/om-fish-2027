#!/usr/bin/env bash
# Re-render reports/mom6-evaluation-synthesis.pdf from the Markdown.
# Needs Quarto (tested with 1.7.34, Typst output). Run from anywhere.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
reports="$(dirname "$here")"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
python3 -I "$here/prep_pdf.py" "$reports/mom6-evaluation-synthesis.md" "$work/body.md"
sed -i '1{/^# /d}' "$work/body.md"   # title comes from header.yml
cat "$here/header.yml" "$work/body.md" > "$work/report.md"
(cd "$work" && quarto render report.md --to typst --quiet)
cp "$work/report.pdf" "$reports/mom6-evaluation-synthesis.pdf"
echo "wrote $reports/mom6-evaluation-synthesis.pdf"
