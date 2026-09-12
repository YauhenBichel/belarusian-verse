#!/usr/bin/env python3
"""Suggest Belarusian words that rhyme with a given word or line.

be_poetry.py can tell you a rhyme is weak; this tells you what would work instead — which is what
a songwriter, or a model writing a verse, actually needs. Rhymes match from the last stressed
vowel to the end of the word, so вадзе brings ідзе and нідзе, not вада.

Rich rhymes (the sound before the stressed vowel matches too) are listed first: they are the ones
that sound deliberate rather than lucky.

Usage:
    be_rhymes.py вадзе                       words that rhyme with вадзе
    be_rhymes.py "Жоўты ліст плыве па вадзе" the last word of the line
    be_rhymes.py вадзе --pos V --limit 20    only verbs
"""
import argparse
import gzip
import os
import re
import sys

from .build_rhyme_index import DEVOICE, SOFT_VOWELS, VOWELS, rhyme_ending
from .data import table


WORD_RE = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*", re.UNICODE)


def load_rhymes(path=None):
    path = path or table("rhymes")
    index = {}
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            ending, _, words = line.rstrip("\n").partition("\t")
            index[ending] = words.split()
    return index


def endings_of(word, stress_path=None, overrides=None):
    """Every rhyme ending this word can have (more than one if its stress is ambiguous)."""
    word = word.lower().replace("’", "'").replace("́", "")
    stress_path = stress_path or table("stress")
    overrides = table("overrides") if overrides is None else overrides
    if overrides and os.path.exists(overrides):  # a homograph we have already settled
        for line in open(overrides, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#"):
                head, _, index = line.partition("\t")
                if head.strip().lower() == word:
                    ending = rhyme_ending(word, int(index.strip()))
                    return [ending] if ending else []
    with gzip.open(stress_path, "rt", encoding="utf-8") as fh:
        for line in fh:
            head, _, marks = line.rstrip("\n").partition("\t")
            if head == word:
                return [e for e in (rhyme_ending(word, int(m)) for m in marks.split(",")) if e]
    positions = [i for i, c in enumerate(word) if c in VOWELS]  # unknown word: assume the last vowel
    if not positions:
        return []
    tail = word[positions[-1]:].replace("ь", "").translate(DEVOICE).translate(SOFT_VOWELS)
    return [tail]


def sound_before(word, ending_length):
    at = len(word) - ending_length - 1
    return word[at] if 0 <= at < len(word) else ""


def load_frequency(path=None):
    """word -> how often it appears in Belarusian Wikipedia. Missing file: everything scores 0."""
    path = path or table("frequency")
    if not os.path.exists(path):
        return {}
    counts = {}
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            word, _, count = line.rstrip("\n").partition("\t")
            counts[word] = int(count)
    return counts


def suggest(word, rhymes=None, limit=40, pos=None, index=None, frequency=None):
    """-> [(candidate, 'rich'|'exact', count)], best first.

    A rhyme nobody uses is not a rhyme you can sing, so common words come first; among equally
    common ones, a rich rhyme (the sound before the stressed vowel matches too) wins.
    """
    rhymes = rhymes if rhymes is not None else load_rhymes()
    frequency = load_frequency() if frequency is None else frequency
    out, seen = [], {word.lower()}
    for ending in endings_of(word):
        source_before = sound_before(word.lower(), len(ending))
        for candidate in rhymes.get(ending, ()):
            if candidate in seen:
                continue
            if pos and index is not None:
                readings = index.get(candidate, ())
                if not any(r[0] == pos for r in readings):
                    continue
            seen.add(candidate)
            grade = "rich" if sound_before(candidate, len(ending)) == source_before else "exact"
            out.append((candidate, grade, frequency.get(candidate, 0)))
    # common words first: a rhyme nobody uses is not one you can sing
    out.sort(key=lambda c: (-c[2], c[1] != "rich", len(c[0]), c[0]))
    return out[:limit]


def _utf8_stdout():
    """Windows consoles default to cp1252, which cannot encode Cyrillic at all."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


def main():
    _utf8_stdout()
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("word", help="a word, or a line whose last word is used")
    p.add_argument("--limit", type=int, default=40)
    p.add_argument("--pos", help="only this part of speech: N noun, A adjective, V verb, S pronoun")
    p.add_argument("--rhymes", help="a be-rhymes.tsv.gz; defaults to the published table")
    p.add_argument("--frequency", help="a be-freq.tsv.gz; defaults to the published table")
    a = p.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

    words = WORD_RE.findall(a.word)
    if not words:
        raise SystemExit("no word given")
    target = words[-1]
    index = None
    if a.pos:
        from .grammar import load_index
        index = load_index()
    frequency = load_frequency(a.frequency)
    found = suggest(target, load_rhymes(a.rhymes), a.limit, a.pos, index, frequency)
    print(f"{target}:" + ("" if frequency else "  (no frequency list: ranking is rough)"))
    for candidate, grade, count in found:
        print(f"  {candidate:24} {grade:6} {count if count else ''}")
    if not found:
        print("  (nothing found)")


if __name__ == "__main__":
    main()
