#!/usr/bin/env python3
"""Respell Belarusian so a Ukrainian or Russian reader (or singing model) says it the Belarusian way.

The syllable count never changes. Usage: be_respell.py --target uk|ru [FILE]  (stdin if no FILE)
Rules: docs/architecture/2026-09-11-build-vs-reuse.md and the tables below.
"""
import argparse
import sys

ACUTE = "́"  # combining stress mark, added by be_stress.py
VOWELS = set("аеёіоуыэюя")
COUNT_VOWELS = set("аеёіоуыэюяиєї")
APOSTROPHES = set("'’")
LETTERS = set("абвгґдеёжзійклмнопрстуўфхцчшщъыьэюяиєї")

# Ukrainian: ы→и, э→е, ў→в (Ukrainian в after a vowel is already [u̯]); е/ё/і depend on position.
UK_FIXED = {"ы": "и", "э": "е", "ў": "в"}
# Russian: і→и, ў→в (keeps the syllable count; Russian has no [u̯]), ґ→г, apostrophe→ъ.
RU_FIXED = {"і": "и", "ў": "в", "ґ": "г"}


def _iotated(prev):
    """е/ё sound [je]/[jo] at a word start and after a vowel, apostrophe, ь or ў."""
    return prev is None or prev in VOWELS or prev in APOSTROPHES or prev in "ьў"


def _uk(ch, prev):
    if ch in UK_FIXED:
        return UK_FIXED[ch]
    if ch == "е":
        return "є" if _iotated(prev) else "е"
    if ch == "ё":
        return "йо" if _iotated(prev) else "ьо"
    if ch == "і":
        return "ї" if prev is not None and (prev in VOWELS or prev in APOSTROPHES) else "і"
    if ch in APOSTROPHES:
        return "'"
    return ch


def _ru(ch, prev):
    if ch in APOSTROPHES:
        return "ъ"
    return RU_FIXED.get(ch, ch)


def respell(text, target):
    rule = {"uk": _uk, "ru": _ru}[target]
    out, prev = [], None  # prev: previous lowercase letter/apostrophe inside the current word
    for i, ch in enumerate(text):
        low = ch.lower()
        if low == ACUTE:  # stress mark: keep it, and let it not break the word
            out.append(ch)
            continue
        # an apostrophe belongs to the word only between two letters (п’ём), not as a quote mark
        in_word_apostrophe = (low in APOSTROPHES and prev is not None
                              and i + 1 < len(text) and text[i + 1].lower() in LETTERS)
        if low in LETTERS or in_word_apostrophe:
            rep = rule(low, prev)
            out.append(rep[:1].upper() + rep[1:] if ch != low else rep)
            prev = low
        else:
            out.append(ch)
            prev = None
    return "".join(out)


def syllables(text):
    return sum(c in COUNT_VOWELS for c in text.lower())


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
    p.add_argument("--target", required=True, choices=["uk", "ru"])
    p.add_argument("file", nargs="?")
    a = p.parse_args()
    text = open(a.file, encoding="utf-8").read() if a.file else sys.stdin.read()
    sys.stdout.write(respell(text, a.target))


if __name__ == "__main__":
    main()
