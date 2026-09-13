#!/usr/bin/env python3
"""Mark Belarusian stress, so the singing model puts the accent on the right syllable.

Belarusian does not write stress, and a model guesses it wrong ("паба́ч" instead of "по́бач").
This inserts a combining acute (U+0301) after the stressed vowel, using the lexicon built from
GrammarDB by build_stress_lexicon.py.

Words of one syllable are left alone. A word written with more than one stress (homographs) is
left alone too, unless --pick-first is given, which takes the most frequent stress. Unknown words
are left alone and can be listed with --report.

Homographs: GrammarDB lists their variants in no particular order, and taking the first was right on
48.9 % of the homographs in Common Voice sentences and 24.9 % in a literary text (Belarusian
Homographs Stress Benchmark). BelVoice's table of the most frequent stress of common homographs, put
first, raises that to 82.9 % and 68.8 % (stress_benchmark.py).

Usage: be_stress.py [FILE] [--report] [--pick-first]   (stdin when no FILE)
"""
import argparse
import gzip
import json
import os
import re
import sys

from .data import table

ACUTE = "́"
VOWELS = set("аеёіоуыэюя")
WORD_RE = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*", re.UNICODE)


def stress_index(marked):
    """1-based index of the stressed vowel in a word marked with an acute (or +) after it."""
    count = 0
    for c in marked.lower():
        if c in VOWELS:
            count += 1
        elif c in (ACUTE, "+"):
            return count or None
    return None


def frequent_first(lexicon, table):
    """Put each homograph's most frequent stress first, when the table's stress is one GrammarDB lists."""
    for key, marked in table.items():
        word = key.lower()
        if key != word and word in table:
            continue  # «Мая» the name must not decide «мая» the pronoun
        options, idx = lexicon.get(word), stress_index(marked)
        if options and len(options) > 1 and idx in options:
            lexicon[word] = (idx,) + tuple(o for o in options if o != idx)
    return lexicon


def load_homographs(path=None):
    """word -> the word with its most frequent stress marked, from BelVoice (LGPL-3.0-or-later).

    The table is downloaded at run time from a pinned BelVoice commit (see data.URLS), never
    bundled. Without an explicit path, a table that cannot be had (offline, blocked, a damaged
    download) gives {}, and homographs keep GrammarDB's own order.
    """
    if path:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    try:
        with open(table("homographs"), encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # an optional improvement must never stop stress marking
        return {}


def load_lexicon(path=None, overrides=None, homographs=None):
    """Load word -> stressed-vowel indexes, the most likely first. Files default to the published tables.

    `homographs` is a BelVoice stresses-stat.json; "" keeps GrammarDB's order. Overrides still win.
    """
    path = path or table("stress")
    overrides = table("overrides") if overrides is None else overrides  # "" disables them
    lexicon = {}
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            word, _, marks = line.rstrip("\n").partition("\t")
            lexicon[word] = tuple(int(m) for m in marks.split(","))
    if homographs != "":
        frequent_first(lexicon, load_homographs(homographs))
    if overrides and os.path.exists(overrides):
        for line in open(overrides, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#"):
                word, _, idx = line.partition("\t")
                lexicon[word.strip().lower()] = (int(idx.strip()),)
    return lexicon


def mark_word(word, lexicon, pick_first=False):
    """Add the acute after the stressed vowel; return (word, status)."""
    plain = word.lower().replace("’", "'")
    vowels = [i for i, c in enumerate(plain) if c in VOWELS]
    if len(vowels) < 2:
        return word, "single"
    if "ё" in plain:  # in Belarusian ё always carries the stress
        at = plain.index("ё")
        return word[:at + 1] + ACUTE + word[at + 1:], "marked"
    options = lexicon.get(plain) or lexicon.get(plain.replace("'", "’"))
    shift = 0
    if not options and plain.startswith("ў"):
        # ў at the start is the same word written after a vowel (ўдваіх = удваіх),
        # but ў is not a vowel, so every stress index moves down by one
        options, shift = lexicon.get("у" + plain[1:]), 1
    if not options:
        return word, "unknown"
    if len(options) > 1 and not pick_first:
        return word, "ambiguous"
    idx = options[0] - shift
    if not 1 <= idx <= len(vowels):
        return word, "unknown"
    at = vowels[idx - 1]
    return word[:at + 1] + ACUTE + word[at + 1:], "marked"


def mark_text(text, lexicon, pick_first=False):
    stats = {"marked": 0, "single": 0, "unknown": 0, "ambiguous": 0}
    unknown = []

    def replace(m):
        word, status = mark_word(m.group(0), lexicon, pick_first)
        stats[status] += 1
        if status in ("unknown", "ambiguous"):
            unknown.append((m.group(0), status))
        return word

    # Section tags and source notes are not sung. Marking them turns «[Куплет]» into «[Купле́т]»,
    # a tag the singing model no longer recognises as a tag.
    lines = [line if line.lstrip().startswith(("[", "#")) else WORD_RE.sub(replace, line)
             for line in text.split("\n")]
    return "\n".join(lines), stats, unknown


def _utf8_stdout():
    """Windows consoles default to cp1252, which cannot encode Cyrillic at all."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):  # already redirected, or an unusual stream
        pass


def main():
    _utf8_stdout()
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("file", nargs="?")
    p.add_argument("--lexicon", help="a be-stress.tsv.gz; defaults to the published table")
    p.add_argument("--overrides", help="word<TAB>index, wins over the lexicon")
    p.add_argument("--pick-first", action="store_true",
                   help="use the most frequent stress for homographs")
    p.add_argument("--report", action="store_true", help="list unmarked words on stderr")
    a = p.parse_args()
    text = open(a.file, encoding="utf-8").read() if a.file else sys.stdin.read()
    marked, stats, unknown = mark_text(text, load_lexicon(a.lexicon, a.overrides), a.pick_first)
    sys.stdout.write(marked)
    if a.report:
        print(f"marked={stats['marked']} one-syllable={stats['single']} "
              f"unknown={stats['unknown']} ambiguous={stats['ambiguous']}", file=sys.stderr)
        for word, status in unknown:
            print(f"  {status}: {word}", file=sys.stderr)


if __name__ == "__main__":
    main()
