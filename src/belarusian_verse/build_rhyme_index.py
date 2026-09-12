#!/usr/bin/env python3
"""Build a Belarusian rhyme index: rhyme ending -> the words that have it.

A Belarusian rhyme matches from the last STRESSED vowel to the end of the word, so the stress
table is what makes this possible. Words are grouped by that ending, with iotated vowels folded
(ёй = ой) and the final consonant devoiced (мароз = марос), exactly as be_poetry.py grades rhymes.

Usage: build_rhyme_index.py --stress data/stress/be-stress.tsv.gz --out data/rhyme/be-rhymes.tsv.gz
"""
import argparse
import gzip
from collections import defaultdict

VOWELS = "аеёіоуыэюя"
DEVOICE = str.maketrans({"б": "п", "д": "т", "ж": "ш", "з": "с", "г": "х", "в": "ф"})
SOFT_VOWELS = str.maketrans({"ё": "о", "я": "а", "ю": "у", "е": "э", "і": "ы"})


def rhyme_ending(word, stressed_vowel):
    """Everything from the stressed vowel to the end, normalised for sound."""
    positions = [i for i, c in enumerate(word) if c in VOWELS]
    if not positions or stressed_vowel > len(positions):
        return None
    tail = word[positions[stressed_vowel - 1]:]
    return tail.replace("ь", "").translate(DEVOICE).translate(SOFT_VOWELS)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--stress", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--min-length", type=int, default=2, help="skip very short words")
    a = p.parse_args()

    groups = defaultdict(set)
    with gzip.open(a.stress, "rt", encoding="utf-8") as fh:
        for line in fh:
            word, _, marks = line.rstrip("\n").partition("\t")
            if len(word) < a.min_length:
                continue
            for mark in marks.split(","):
                ending = rhyme_ending(word, int(mark))
                if ending:  # a one-letter ending still rhymes: мне / дне / ране
                    groups[ending].add(word)

    with gzip.open(a.out, "wt", encoding="utf-8") as out:
        for ending in sorted(groups):
            words = sorted(groups[ending])
            if len(words) > 1:  # an ending only one word has is not a rhyme
                out.write(f"{ending}\t{' '.join(words)}\n")
    rhymable = sum(1 for words in groups.values() if len(words) > 1)
    print(f"{a.out}: {rhymable} endings, {sum(len(w) for w in groups.values())} words")


if __name__ == "__main__":
    main()
