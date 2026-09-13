#!/usr/bin/env python3
"""Check Belarusian song lyrics for the errors weak LLMs make.

Usage: be_check.py LYRICS.txt [--syllables 8] [--rhyme AABB] [--dict PATH/be-official] [--json]
Exit code 0 when there are no ERROR issues, 1 otherwise.
"""
import argparse
import json
import os
import re
import sys

from .data import table

LETTERS = set("абвгґдеёжзійклмнопрстуўфхцчшыьэюя")
VOWELS = set("аеёіоуыэюя")  # ў is not a vowel
CONSONANTS = set("бвгґджзйклмнпрстфхцчш")
WORD_RE = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*")
COUNT_RE = re.compile(r"\s*\(\d+\)\s*$")
RHYME_NORM = str.maketrans({"я": "а", "ю": "у", "е": "э", "ё": "о", "і": "ы", "ь": None})


ACUTE = "́"  # stress mark from be_stress.py: not part of the spelling


def load_extra(path=None):
    """Real Belarusian words the Hunspell dictionary is missing (extra-words.txt).

    The dictionary has gaps — слухаўка is an ordinary word and is not in it — and without a way to
    fill them the only way to get a line past the checker is to weaken the checker. Each entry is
    a form GrammarDB lists, not a word a model produced.
    """
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "extra-words.txt")
    words = set()
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                word = line.split("#")[0].strip().lower()
                if word:
                    words.add(word)
    except OSError:
        pass
    return frozenset(words)


EXTRA = load_extra()


def word_issues(word, dictionary, extra=None):
    w = word.lower().replace("’", "'").replace(ACUTE, "")
    extra = EXTRA if extra is None else extra
    issues = []
    bad = sorted({c for c in w if c.isalpha() and c not in LETTERS})
    if bad:
        issues.append(("ERROR", "BAD_CHAR", f"{word} [{''.join(bad)}]"))
        return issues  # other checks are meaningless for a foreign word
    if re.search(r"т[еёюяіь]|д(?![зж])[еёюяіь]", w):
        issues.append(("ERROR", "SOFT_T_D", word))
    if re.search(r"(?:[жшчр]|дж)[еёюяіь]", w):
        issues.append(("ERROR", "HARD_CONS", word))
    if w.count("о") >= 2:
        issues.append(("WARN", "MULTI_O", word))
    if any(a in VOWELS and b == "у" and c in CONSONANTS for a, b, c in zip(w, w[1:], w[2:])):
        issues.append(("WARN", "U_SHORT", word))
    if (dictionary is not None and w not in extra
            and not (dictionary.lookup(w) or dictionary.lookup(word.replace(ACUTE, "")))):
        issues.append(("ERROR", "UNKNOWN_WORD", word))
    return issues


def syllables(line):
    return sum(c in VOWELS for c in line.lower())


def rhyme_key(line):
    letters = "".join(c for c in line.lower() if c in LETTERS).translate(RHYME_NORM)
    for i in range(len(letters) - 1, -1, -1):
        if letters[i] in VOWELS:
            return letters[i:]
    return ""


def short_u_issues(line):
    """The у/ў rule between words: after a vowel it is ў, otherwise у.

    "Я іду ў школу", never "іду у школу"; "стаў у хаце", never "стаў ў хаце". The rule holds
    across the whole line, which is why a word-by-word checker never sees it. After a full stop,
    a question or exclamation mark the pause resets it and у stays у.

    The same rule governs a word that begins with у: «яна ўсё ведае», never «яна усё»; «тут усё»,
    never «тут ўсё». Abbreviations keep their у («у УНП» is read letter by letter), so all-capital
    words are skipped.
    """
    issues = []
    tokens = re.findall(r"[^\W\d_]+|[.!?…]", line)
    previous = None
    for raw in tokens:
        token = raw.lower()
        if token in ".!?…":
            previous = None
            continue
        after_vowel = bool(previous) and previous[-1] in VOWELS
        abbreviation = len(raw) > 1 and raw.isupper()
        if token[0] == "у" and after_vowel and not abbreviation:
            issues.append(("ERROR", "SHOULD_BE_U_SHORT", f"у after «{previous}» should be ў"
                           if token == "у" else f"«{raw}» after «{previous}» should start with ў"))
        elif token[0] == "ў" and not after_vowel:
            after = f"after «{previous}»" if previous else "at the start"
            issues.append(("ERROR", "SHOULD_BE_U_LONG", f"ў {after} should be у"
                           if token == "ў" else f"«{raw}» {after} should start with у"))
        previous = token
    return issues


def check_text(text, syllables_per_line=None, rhyme=None, dictionary=None, tolerance=0):
    sections, lines = [[]], []
    for n, raw in enumerate(text.splitlines(), 1):
        line = COUNT_RE.sub("", raw).strip()
        if not line:
            continue
        if line.startswith("#"):   # a provenance note, not a line of the song
            continue
        if line.startswith("["):
            sections.append([])
            continue
        line = line.split("|")[0].strip()  # bilingual lyrics: judge the Belarusian half
        entry = {"n": n, "text": line, "syllables": syllables(line), "issues": []}
        for word in WORD_RE.findall(line):
            entry["issues"] += [dict(level=l, code=c, word=w) for l, c, w in word_issues(word, dictionary)]
        entry["issues"] += [dict(level=l, code=c, word=w) for l, c, w in short_u_issues(line)]
        if syllables_per_line and abs(entry["syllables"] - syllables_per_line) > tolerance:
            want = f"{syllables_per_line}±{tolerance}" if tolerance else str(syllables_per_line)
            entry["issues"].append(dict(level="ERROR", code="SYLLABLES",
                                        word=f"{entry['syllables']} != {want}"))
        lines.append(entry)
        sections[-1].append(entry)
    if rhyme:
        for sec in sections:
            for i, a in enumerate(sec):
                for j in range(i + 1, len(sec)):
                    b = sec[j]
                    if rhyme[i % len(rhyme)] == rhyme[j % len(rhyme)]:
                        if rhyme_key(a["text"]) != rhyme_key(b["text"]):
                            b["issues"].append(dict(level="WARN", code="RHYME",
                                                    word=f"-{rhyme_key(b['text'])} vs line {a['n']} -{rhyme_key(a['text'])}"))
                        break
    errors = sum(i["level"] == "ERROR" for e in lines for i in e["issues"])
    warnings = sum(i["level"] == "WARN" for e in lines for i in e["issues"])
    return {"lines": lines, "errors": errors, "warnings": warnings, "pass": errors == 0}


def load_dictionary(base=None):
    """Belarusian spell checker. Defaults to the dictionary published with the tables."""
    from spylls.hunspell import Dictionary
    if base is None:
        table("hunspell_aff")  # both files must sit side by side in the cache
        base = table("hunspell_dic")[: -len(".dic")]
    return Dictionary.from_files(base)


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
    p.add_argument("file")
    p.add_argument("--syllables", type=int)
    p.add_argument("--tolerance", type=int, default=0,
                   help="allowed syllables off target; the singing model fits its melody to the words")
    p.add_argument("--rhyme")
    p.add_argument("--dict", help="Hunspell base path without .dic/.aff")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    text = open(a.file, encoding="utf-8").read()
    result = check_text(text, a.syllables, a.rhyme, load_dictionary(a.dict) if a.dict else None, a.tolerance)
    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for e in result["lines"]:
            print(f"{e['n']:>3} ({e['syllables']:>2}) {e['text']}")
            for i in e["issues"]:
                print(f"      {i['level']:5} {i['code']:12} {i['word']}")
        print(f"errors={result['errors']} warnings={result['warnings']} -> {'PASS' if result['pass'] else 'FAIL'}")
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
