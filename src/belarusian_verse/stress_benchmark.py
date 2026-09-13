#!/usr/bin/env python3
"""Score homograph stress against the Belarusian Homographs Stress Benchmark.

The benchmark (https://huggingface.co/datasets/alex73/benchmarks-stress-bel, CC BY-SA 4.0, created
for BelVoice by Aleś Bułojčyk and contributors) is downloaded at a pinned revision and not shipped.
It has three sets: Common Voice sentences, the literary «Засценак Малінаўка» marked by hand, and
10×10, where every stress of a homograph appears exactly ten times so that frequency alone cannot
win. Only tokens the lexicon lists with more than one stress are scored: for every other word the
lexicon has one answer.

Usage: python -m belarusian_verse.stress_benchmark [--data FOLDER]
"""
import argparse
import os
import re

from .stress import ACUTE, load_lexicon, stress_index

REPO = "alex73/benchmarks-stress-bel"
REVISION = "94bb5a86120feb531107132eef7466c399420c18"
FILES = {"common_voice": "datasets/common_voice.txt",
         "literary": "datasets/zascienak_Malinauka.txt",
         "10x10": "datasets/10x10.tsv"}
TOKEN_RE = re.compile(r"[а-яёіўА-ЯЁІЎ'’+" + ACUTE + r"]+")


def download(folder=None):
    """name -> path of each benchmark file, from FOLDER or the pinned dataset revision."""
    if folder:
        return {name: os.path.join(folder, os.path.basename(f)) for name, f in FILES.items()}
    from huggingface_hub import hf_hub_download
    return {name: hf_hub_download(REPO, f, repo_type="dataset", revision=REVISION)
            for name, f in FILES.items()}


def plain(token):
    return token.replace("+", "").replace(ACUTE, "").lower()


def marked_tokens(path):
    """Every stress-marked token of a text file (the + or acute follows the stressed vowel)."""
    with open(path, encoding="utf-8") as handle:
        return [t for line in handle for t in TOKEN_RE.findall(line) if "+" in t or ACUTE in t]


def gold_words(path):
    """10x10.tsv: the marked word is the first column of every row."""
    with open(path, encoding="utf-8") as handle:
        return [line.split("\t")[0] for line in handle if "\t" in line]


def score(tokens, lexicon):
    """-> (right, homograph tokens): how often the lexicon's first stress is the marked one."""
    right = total = 0
    for token in tokens:
        options, gold = lexicon.get(plain(token)), stress_index(token)
        if not options or len(options) < 2 or gold is None:
            continue
        total += 1
        right += options[0] == gold
    return right, total


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", help="a folder holding the three benchmark files; default: download them")
    a = p.parse_args()
    files = download(a.data)
    sets = [("Common Voice sentences", marked_tokens(files["common_voice"])),
            ("Засценак Малінаўка (literary)", marked_tokens(files["literary"])),
            ("10x10 (every stress equally often)", gold_words(files["10x10"]))]
    orders = [("GrammarDB order", load_lexicon(homographs="")), ("BelVoice first", load_lexicon())]
    for name, tokens in sets:
        results = []
        for label, lexicon in orders:
            right, total = score(tokens, lexicon)
            results.append(f"{label} {right:>5}/{total:<5} ({right / max(total, 1):.1%})")
        print(f"{name:36} " + "   ".join(results))


if __name__ == "__main__":
    main()
