#!/usr/bin/env python3
"""pptx-scramble — length-preserving, REVERSIBLE, position-independent text redaction for PowerPoint.

What it does
------------
`scramble` replaces every WORD in a .pptx with random gibberish of the SAME
length and SAME character class (letter -> letter, digit -> digit, case +
alphabet preserved; spaces and punctuation untouched). Layout, fonts, colours
and per-line character counts stay identical — only the words change.

`restore` puts the original words back. Restoration is BY CONTENT, not by
position: every word is replaced CONSISTENTLY (same word -> same gibberish) and
UNIQUELY (different words -> different gibberish), so each gibberish word acts as
a stable "barcode". Between scramble and restore an editor (e.g. the official
`pptx` skill, or a small model) may have moved words to other slides, reordered
them, split runs or reflowed paragraphs — they are still found wherever they now
sit, because we match on the word itself, not on where it is.

Design goals (so a small model can run this blindly)
----------------------------------------------------
  * Standard library only — no python-pptx, no network.
  * Byte-faithful — only the inner text of <a:t> run elements is rewritten; every
    other byte of the OOXML package is copied verbatim.
  * Self-verifying — `scramble` round-trips in memory and prints "OK" before
    writing, so the caller knows restoration will work.

Usage
-----
    python pptx_scramble.py scramble <input.pptx> [--out OUT] [--map MAP]
                                     [--seed N] [--all-text] [--no-verify]
    python pptx_scramble.py restore  <edited.pptx> <map.json> [--out OUT]

Examples
--------
    python pptx_scramble.py scramble "Q4 board deck.pptx"
        -> "Q4 board deck-scrambled.pptx"  +  "Q4 board deck-scrambled.map.json"
    # ...rework the scrambled deck however you like (move/reorder/restyle)...
    python pptx_scramble.py restore "Q4 board deck-scrambled.pptx" \
                                    "Q4 board deck-scrambled.map.json"
        -> "Q4 board deck-restored.pptx"
"""

import argparse
import html
import json
import random
import re
import shutil
import string
import sys
import zipfile
from datetime import datetime
from pathlib import Path

# --- what counts as a text-bearing XML part -------------------------------
# All human-readable text in OOXML lives in DrawingML <a:t> run elements:
# titles, body, table cells, grouped shapes, SmartArt, speaker notes, chart
# labels. We skip slide layouts/masters (template scaffolding, not visible
# content) unless --all-text is given, and never touch <c:v> numeric caches.
DEFAULT_PREFIXES = (
    "ppt/slides/slide",
    "ppt/notesSlides/notesSlide",
    "ppt/diagrams/data",
    "ppt/charts/chart",
)
EXTRA_PREFIXES = (
    "ppt/slideLayouts/",
    "ppt/slideMasters/",
    "ppt/notesMasters/",
    "ppt/handoutMasters/",
)

# Match an <a:t ...>inner</a:t> run. DOTALL because the inner text may (rarely)
# contain a newline; the non-greedy body + explicit close tag keep it anchored
# to a single element (a:t never nests).
A_T_RE = re.compile(r"(<a:t(?:\s[^>]*)?>)(.*?)(</a:t>)", re.DOTALL)

# A "word" = a maximal run of letters/digits (Unicode-aware), excluding the
# underscore. Splitting on every non-alphanumeric boundary means each word is an
# independent unit that can be found and restored on its own after being moved.
WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)

# Replacement alphabets, kept per-script + per-case so swapped text keeps the
# same visual texture (a Cyrillic capital stays a Cyrillic capital, etc.).
LAT_UP = string.ascii_uppercase
LAT_LO = string.ascii_lowercase
CYR_UP = "".join(chr(c) for c in range(0x410, 0x430)) + "Ё"  # А-Я + Ё
CYR_LO = "".join(chr(c) for c in range(0x430, 0x450)) + "ё"  # а-я + ё
DIGITS = string.digits
WIDE_POOL = LAT_UP + LAT_LO + CYR_UP + CYR_LO + DIGITS  # uniqueness fallback


def scramble_char(ch: str, rng: random.Random, widen: bool = False) -> str:
    """Map one alphanumeric character to a same-class placeholder.

    `widen=True` draws from the whole pool, ignoring class — used only as a
    fallback so even very short words can get a unique replacement.
    """
    if widen:
        return rng.choice(WIDE_POOL)
    if ch in DIGITS:
        return rng.choice(DIGITS)
    upper = ch.isupper()
    o = ord(ch)
    if ("a" <= ch.lower() <= "z") and o < 0x250:        # Latin
        return rng.choice(LAT_UP if upper else LAT_LO)
    if 0x400 <= o <= 0x4FF:                              # Cyrillic
        return rng.choice(CYR_UP if upper else CYR_LO)
    # Any other script (accented Latin, Greek, CJK, ...): fall back to a Latin
    # letter of the same case. Rare; keeps content hidden.
    return rng.choice(LAT_UP if upper else LAT_LO)


def make_token(word: str, used: set, rng: random.Random) -> str:
    """A unique, same-length gibberish replacement for `word`.

    Tries same-class characters first (best layout fidelity). If a glut of very
    short words exhausts that space, it widens the alphabet so uniqueness — which
    content-based restoration depends on — is still guaranteed.
    """
    for widen in (False, True):
        for _ in range(500):
            tok = "".join(scramble_char(c, rng, widen) for c in word)
            if tok != word and tok not in used:
                used.add(tok)
                return tok
    raise RuntimeError(
        f"Could not find a unique replacement for {word!r} (length {len(word)}): "
        "too many distinct very-short words for the available alphabet."
    )


def xml_escape(s: str) -> str:
    # Element-content escaping only — order matters (& first).
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def scramble_text(text: str, mapping: dict, used: set, rng: random.Random) -> str:
    """Replace each word in `text` with its consistent, unique gibberish."""
    def repl(m: "re.Match[str]") -> str:
        w = m.group(0)
        tok = mapping.get(w)
        if tok is None:
            tok = make_token(w, used, rng)
            mapping[w] = tok
        return tok
    return WORD_RE.sub(repl, text)


def restore_text(text: str, rev: dict, stats: list) -> str:
    """Swap every known gibberish word back to its original; leave the rest."""
    def repl(m: "re.Match[str]") -> str:
        w = m.group(0)
        if w in rev:
            stats[0] += 1
            return rev[w]
        stats[1] += 1
        return w
    return WORD_RE.sub(repl, text)


def is_text_part(name: str, prefixes: tuple) -> bool:
    return name.endswith(".xml") and name.startswith(prefixes)


def cmd_scramble(args: argparse.Namespace) -> int:
    in_path = Path(args.input)
    if not in_path.exists():
        print(f"Error: {in_path} does not exist", file=sys.stderr)
        return 1

    # --into ROOT: give this run its own self-contained folder so everything for
    # one job lives together: ROOT/<deck>-<timestamp>/ holding a copy of the
    # original, the scrambled deck, the map, a README, and later the restored deck.
    run_dir = None
    if args.into:
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        run_dir = Path(args.into) / f"{in_path.stem}-{stamp}"
        run_dir.mkdir(parents=True, exist_ok=True)
        orig_copy = run_dir / in_path.name
        if orig_copy.resolve() != in_path.resolve():
            shutil.copy2(in_path, orig_copy)
        out_path = run_dir / (in_path.stem + "-scrambled.pptx")
        map_path = run_dir / (out_path.stem + ".map.json")
    else:
        out_path = Path(args.out) if args.out else in_path.with_name(
            in_path.stem + "-scrambled.pptx")
        map_path = Path(args.map) if args.map else out_path.with_name(
            out_path.stem + ".map.json")

    prefixes = DEFAULT_PREFIXES + (EXTRA_PREFIXES if args.all_text else ())
    rng = random.Random(args.seed)

    mapping: dict = {}        # original word -> gibberish (consistent + injective)
    used: set = set()         # every gibberish token, for uniqueness
    orig_runs: list = []      # decoded run texts, for the self-check
    scr_runs: list = []
    n_parts = n_runs = n_words = n_chars = 0

    with zipfile.ZipFile(in_path, "r") as zin:
        items = zin.infolist()
        new_data: dict = {}
        for item in items:
            if item.is_dir() or not is_text_part(item.filename, prefixes):
                continue
            xml = zin.read(item.filename).decode("utf-8")
            before = len(orig_runs)

            def repl(m: "re.Match[str]") -> str:
                original = html.unescape(m.group(2))
                scrambled = scramble_text(original, mapping, used, rng)
                orig_runs.append(original)
                scr_runs.append(scrambled)
                return m.group(1) + xml_escape(scrambled) + m.group(3)

            scrambled_xml = A_T_RE.sub(repl, xml)
            if len(orig_runs) == before:
                continue  # part had no <a:t> text
            new_data[item.filename] = scrambled_xml.encode("utf-8")
            n_parts += 1

        n_runs = len(orig_runs)
        n_chars = sum(len(t) for t in orig_runs)
        n_words = sum(len(WORD_RE.findall(t)) for t in orig_runs)

        # In-memory self-check: same length per run, and content-based restore
        # of the freshly scrambled text reproduces the originals exactly.
        if not args.no_verify:
            rev = {tok: word for word, tok in mapping.items()}
            for o, s in zip(orig_runs, scr_runs):
                if len(o) != len(s):
                    print("Error: length check failed (char counts differ)",
                          file=sys.stderr)
                    return 1
                if restore_text(s, rev, [0, 0]) != o:
                    print("Error: round-trip check failed", file=sys.stderr)
                    return 1

        # Write the new package, copying every entry verbatim except the
        # rewritten text parts. Reusing each ZipInfo preserves names, order,
        # timestamps and per-entry compression.
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in items:
                if item.is_dir():
                    continue
                data = new_data.get(item.filename) or zin.read(item.filename)
                zout.writestr(item, data)

    map_doc = {
        "tool": "pptx-scramble",
        "format_version": 2,
        "unit": "word",
        "match": "by-content",  # restoration finds words by value, not position
        "source_file": in_path.name,
        "scrambled_file": out_path.name,
        "mode": "preserve-class",
        "seed": args.seed,
        "scope": "all-text" if args.all_text else "content",
        "stats": {
            "parts": n_parts, "runs": n_runs,
            "words_total": n_words, "words_distinct": len(mapping),
            "chars": n_chars,
        },
        # The decode table: gibberish -> original. Keys are unique by construction.
        "words": {tok: word for word, tok in mapping.items()},
    }
    map_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.write_text(
        json.dumps(map_doc, ensure_ascii=False, indent=2), encoding="utf-8")

    if run_dir is not None:
        _write_readme(run_dir, in_path.name, out_path, map_path)

    check = "self-check (length + round-trip): OK" if not args.no_verify \
        else "self-check: skipped (--no-verify)"
    print(f"Scrambled {n_words} words ({len(mapping)} distinct, {n_chars} chars) "
          f"across {n_parts} parts. {check}")
    if run_dir is not None:
        print(f"  run folder -> {run_dir}")
    print(f"  deck -> {out_path}")
    print(f"  map  -> {map_path}")
    print("  NOTE: the .map.json holds the ORIGINAL text in clear - keep it "
          "private; without it the deck cannot be restored.")
    return 0


def _write_readme(run_dir: Path, original_name: str, out_path: Path, map_path: Path) -> None:
    """Drop a short, human-friendly note so the folder explains itself later."""
    script = Path(__file__).resolve()
    restored_name = out_path.stem.replace("-scrambled", "") + "-restored.pptx"
    text = f"""Папка одной обработки pptx-scramble.

Что здесь лежит:
  {original_name}
      — исходная презентация (копия оригинала).
  {out_path.name}
      — обезличенная «болванка»: текст заменён на абракадабру той же длины.
        Её можно безопасно отдавать в работу / на доработку дизайна.
  {map_path.name}
      — карта для восстановления. ВНИМАНИЕ: хранит оригинальный текст
        открытым. Это секрет — НЕ отдавать вместе с болванкой.
  {restored_name}
      — появится после восстановления (см. команду ниже).

Восстановить оригинальные слова (можно после любой переработки болванки —
слова находятся по содержимому, их положение могло измениться):

  python "{script}" restore "{out_path.name}" "{map_path.name}"

Запускать из этой папки.
"""
    (run_dir / "README.txt").write_text(text, encoding="utf-8")


def cmd_restore(args: argparse.Namespace) -> int:
    scr_path = Path(args.input)
    map_path = Path(args.map)
    for p in (scr_path, map_path):
        if not p.exists():
            print(f"Error: {p} does not exist", file=sys.stderr)
            return 1

    map_doc = json.loads(map_path.read_text(encoding="utf-8"))
    rev: dict = map_doc["words"]  # gibberish -> original
    scope = map_doc.get("scope", "content")
    prefixes = DEFAULT_PREFIXES + (EXTRA_PREFIXES if scope == "all-text" else ())

    out_path = Path(args.out) if args.out else scr_path.with_name(
        scr_path.stem.replace("-scrambled", "") + "-restored.pptx")

    matched = unmatched = n_parts = 0
    with zipfile.ZipFile(scr_path, "r") as zin:
        items = zin.infolist()
        new_data: dict = {}
        for item in items:
            if item.is_dir() or not is_text_part(item.filename, prefixes):
                continue
            xml = zin.read(item.filename).decode("utf-8")
            stats = [0, 0]

            def repl(m: "re.Match[str]") -> str:
                inner = html.unescape(m.group(2))
                fixed = restore_text(inner, rev, stats)
                return m.group(1) + xml_escape(fixed) + m.group(3)

            new_xml = A_T_RE.sub(repl, xml)
            if stats[0]:
                n_parts += 1
            matched += stats[0]
            unmatched += stats[1]
            new_data[item.filename] = new_xml.encode("utf-8")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in items:
                if item.is_dir():
                    continue
                data = new_data.get(item.filename) or zin.read(item.filename)
                zout.writestr(item, data)

    print(f"Restored {matched} words across {n_parts} parts "
          f"(left as-is: {unmatched}).")
    print(f"  deck -> {out_path}")
    if unmatched:
        print("  note: 'left as-is' are words not in the map - text the editor "
              "added, or gibberish that was altered/split and no longer matches.")
    if matched == 0:
        print("  WARNING: nothing matched. Wrong map for this deck, or the deck "
              "was never scrambled.", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Length-preserving, reversible, position-independent .pptx text redaction")
    sub = parser.add_subparsers(dest="command", required=True)

    s = sub.add_parser("scramble", help="replace every word with same-length gibberish")
    s.add_argument("input", help="source .pptx")
    s.add_argument("--into", metavar="ROOT",
                   help="put this run in a fresh subfolder ROOT/<deck>-<timestamp>/ "
                        "with a copy of the original + a README (keeps a job's "
                        "materials together; overrides --out/--map)")
    s.add_argument("--out", help="output .pptx (default: <name>-scrambled.pptx)")
    s.add_argument("--map", help="output map .json (default: <out>.map.json)")
    s.add_argument("--seed", type=int, default=1, help="RNG seed (default: 1)")
    s.add_argument("--all-text", action="store_true",
                   help="also scramble slide layouts/masters")
    s.add_argument("--no-verify", action="store_true",
                   help="skip the in-memory round-trip self-check")
    s.set_defaults(func=cmd_scramble)

    r = sub.add_parser("restore", help="put the original words back (by content)")
    r.add_argument("input", help="edited/scrambled .pptx")
    r.add_argument("map", help="the .map.json produced by scramble")
    r.add_argument("--out", help="output .pptx (default: <name>-restored.pptx)")
    r.set_defaults(func=cmd_restore)

    # Print UTF-8 so Cyrillic paths render in modern terminals (VSCode / Windows
    # Terminal); soften errors so a legacy console can't crash on an exotic char.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, ValueError):
            pass

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
