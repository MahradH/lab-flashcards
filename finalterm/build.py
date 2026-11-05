#!/usr/bin/env python3
"""Rebuild the final-term (Units 5-8) flashcard block inside data-en2.js.

Source of truth: finalterm/src/u{5,6,7,8}.psv
Each line: English | Persian meaning | Persian pronunciation | difficulty

The old extractor (gen.py) produced bidi-broken meanings and weak
transliterations; this build uses the reviewed data instead. It only
touches the u5-u8 block and leaves Units 1-4 and examData2 untouched.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data-en2.js"

TITLES = {
    5: ("Acid test", "فصل ۵ — Acid test"),
    6: ("Stress: Another chimera", "فصل ۶ — Stress: Another chimera"),
    7: ("Why sugar is bad for you", "فصل ۷ — Why sugar is bad for you"),
    8: ("Malaria: A case study of evolution", "فصل ۸ — Malaria: A case study of evolution"),
}
UNITS = [5, 6, 7, 8]


def read_psv(unit):
    path = HERE / "src" / f"u{unit}.psv"
    rows = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("|")
        if len(parts) != 4:
            sys.exit(f"{path}:{lineno}: expected 4 fields, got {len(parts)}")
        en, fa, pron, diff = (p.strip() for p in parts)
        if not en or not fa or not pron:
            sys.exit(f"{path}:{lineno}: empty field")
        if diff not in ("easy", "hard"):
            sys.exit(f"{path}:{lineno}: bad difficulty {diff!r}")
        if re.search(r"[A-Za-z]", fa):
            sys.exit(f"{path}:{lineno}: Latin letters left in meaning: {fa!r}")
        if re.search(r"[A-Za-z]", pron):
            sys.exit(f"{path}:{lineno}: Latin letters left in pronunciation: {pron!r}")
        rows.append((en, fa, pron, diff))
    return rows


def existing_words(text, unit):
    """English words currently in data-en2.js for this unit, in order."""
    start = text.index(f"    u{unit}: {{")
    end = text.index("    },\n", start)
    return re.findall(r'en: "((?:[^"\\]|\\.)*)"', text[start:end])


def js(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def main():
    text = DATA.read_text(encoding="utf-8")
    blocks = []
    for unit in UNITS:
        rows = read_psv(unit)
        current = existing_words(text, unit)
        if [r[0] for r in rows] != current:
            missing = [w for w in current if w not in [r[0] for r in rows]]
            extra = [r[0] for r in rows if r not in current]
            sys.exit(
                f"u{unit}: word list mismatch\n  missing: {missing}\n  extra: {extra}"
            )
        hard = sum(1 for r in rows if r[3] == "hard")
        print(f"u{unit}: {len(rows)} words, {hard} hard ({100 * hard / len(rows):.0f}%)")
        short, title = TITLES[unit]
        lines = [f"    u{unit}: {{", f'        title: "{title}",', f'        short: "{short}",', "        words: ["]
        for en, fa, pron, diff in rows:
            lines.append(
                f'            {{ en: "{js(en)}", pron: "{js(pron)}", fa: "{js(fa)}", difficulty: "{diff}" }},'
            )
        lines += ["        ],", "    },"]
        blocks.append("\n".join(lines))

    start = text.index("    u5: {")
    end = text.index("const examData2")
    new_text = text[:start].rstrip("\n") + "\n\n" + "\n".join(blocks) + "\n};\n\n" + text[end:]
    DATA.write_text(new_text, encoding="utf-8")
    print(f"wrote {DATA}")


if __name__ == "__main__":
    main()
