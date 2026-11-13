"""Prepare the synthesis Markdown for a Typst PDF render (copy only)."""
import re, sys

src, dst = sys.argv[1], sys.argv[2]
lines = open(src, encoding="utf-8").read().split("\n")
ZW = "​"
LIST = re.compile(r"^\s*(?:[-*+]|\d+\.)\s")

def breakable_code(cell):
    # allow line breaks inside inline code after / _ . @ : so paths wrap in table cells
    return re.sub(r"`([^`]+)`",
                  lambda m: "`" + re.sub(r"([/_.@:])", r"\1" + ZW, m.group(1)) + "`",
                  cell)

def split_row(row):
    return [c.strip() for c in row.strip().strip("|").split("|")]

out, i, in_code = [], 0, False
while i < len(lines):
    ln = lines[i]
    if ln.startswith("```"):
        in_code = not in_code
    # table block: header, separator, rows
    if (not in_code and ln.startswith("|") and i + 1 < len(lines)
            and re.match(r"^\|[\s:|-]+\|$", lines[i + 1])):
        block = [ln]
        j = i + 1
        while j < len(lines) and lines[j].startswith("|"):
            block.append(lines[j]); j += 1
        rows = [split_row(r) for k, r in enumerate(block) if k != 1]
        ncol = len(rows[0])
        means = []
        for c in range(ncol):
            vals = [len(r[c]) for r in rows if c < len(r)]
            means.append(sum(vals) / len(vals))
        heads = rows[0]
        w = [max(len(heads[c]) + 2, 8, min(60, means[c])) for c in range(ncol)]
        tot = sum(w)
        dashes = [max(3, round(200 * x / tot)) for x in w]
        out.append(breakable_code(block[0]))
        out.append("|" + "|".join("-" * d for d in dashes) + "|")
        out.extend(breakable_code(r) for r in block[2:])
        i = j
        continue
    # pandoc needs a blank line before a list that follows a paragraph line
    if (not in_code and LIST.match(ln) and out and out[-1].strip()
            and not LIST.match(out[-1]) and not out[-1].startswith("  ")):
        out.append("")
    out.append(ln)
    i += 1

open(dst, "w", encoding="utf-8").write("\n".join(out))
