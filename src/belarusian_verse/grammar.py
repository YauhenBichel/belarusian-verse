#!/usr/bin/env python3
"""Check Belarusian agreement: does the adjective actually match its noun?

be_check.py asks "are these real words", be_poetry.py asks "does it rhyme and scan". This asks
"is it grammatical": an adjective or possessive pronoun must share case, number and gender with
the noun it stands before. "тваіх вачам" fails — тваіх is accusative/genitive/locative plural,
вачам is dative plural, so no reading of the phrase works. "тваім вачам" passes.

The evidence comes from GrammarDB (build_grammar_index.py), so this is a dictionary lookup and a
set intersection, not a guess. Words the dictionary does not know are skipped, and personal
pronouns are ignored because they do not modify the noun that follows them ("мне спакой").

Usage: be_grammar.py LYRICS.txt [--json]
"""
import argparse
import gzip
import json
import os
import re
import sys

from .data import table

WORD_RE = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*", re.UNICODE)

# personal pronouns stand next to nouns without modifying them
PERSONAL = {"я", "мяне", "мне", "мной", "мною", "ты", "цябе", "табе", "табой", "тобой",
            "ён", "яго", "яму", "ім", "яна", "яе", "ёй", "яно", "мы", "нас", "нам", "намі",
            "вы", "вас", "вам", "вамі", "яны", "іх", "ім", "імі", "сябе", "сабе", "сабой"}
MODIFIERS = {"A", "S"}  # adjectives and adjective-like pronouns (мой, твой, гэты …)
# personal pronouns as subjects: person, number, gender (for the past tense, which has no person)
SUBJECTS = {
    "я": ("1", "S", "0"), "ты": ("2", "S", "0"), "ён": ("3", "S", "M"),
    "яна": ("3", "S", "F"), "яно": ("3", "S", "N"),
    "мы": ("1", "P", "0"), "вы": ("2", "P", "0"), "яны": ("3", "P", "0"),
}


def load_index(path=None):
    """Load word -> morphological readings. Defaults to the published table."""
    path = path or table("forms")
    index = {}
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            word, _, codes = line.rstrip("\n").partition("\t")
            index[word] = tuple(c.split(":") for c in codes.split(","))
    return index


def agrees(modifier, noun):
    """True when some reading of the two words shares gender, case and number."""
    for _, g1, c1, n1 in modifier:
        for _, g2, c2, n2 in noun:
            if c1 == c2 and n1 == n2 and (g1 == "0" or g2 == "0" or g1 == g2):
                return True
    return False


def readings(word, index, pos):
    return tuple(c for c in index.get(word, ()) if c[0] in pos)


def order(a, b, words, index):
    """Decide which of the two words modifies which, or None when the pair should be left alone.

    Belarusian verse puts the adjective on either side of its noun — "цёплы вечар" and
    "свежасць ранішняя" are both normal. But in "у такт тваім вачам" the pronoun belongs to the
    noun that FOLLOWS it, not to "такт" before it, so a trailing modifier is only tied to the
    preceding noun when it does not fit the next word.
    """
    a_mod, a_noun = readings(a, index, MODIFIERS), readings(a, index, "N")
    b_mod, b_noun = readings(b, index, MODIFIERS), readings(b, index, "N")
    if a_mod and not a_noun and b_noun:          # modifier before its noun
        return a_mod, b_noun
    if b_mod and not b_noun and a_noun:          # modifier after its noun
        following = words[words.index(b) + 1].lower().replace("’", "'") if words[-1] != b else None
        # only an unambiguous noun can claim the modifier; "тут" reads as an adverb here
        if following and not readings(following, index, "X") and readings(following, index, "N"):
            return None                          # it belongs to the next noun instead
        return b_mod, a_noun
    return None


def verb_fits_subject(verb_readings, subject):
    """Does any reading of the verb go with this pronoun?

    Present, future and imperative carry a person: «я іду», never «я ідуць». The past tense has no
    person but does have gender and number: «яна спявала», «яны спявалі», never «яна спявалі».
    """
    person, number, gender = subject
    for _pos, g, p, n in verb_readings:
        if p == "0":                      # infinitive: goes with anything
            return True
        if p == "P":                      # past: gender and number
            if n == number and (gender == "0" or g == "0" or g == gender):
                return True
        elif p == person and n == number:  # present, future, imperative
            return True
    return False


def check_subject_verb(words, index):
    """«Яна ідуць» — a pronoun next to a verb that cannot belong to it."""
    issues = []
    for first, second in zip(words, words[1:]):
        for subject_word, verb_word in ((first, second), (second, first)):
            subject = SUBJECTS.get(subject_word.lower())
            readings = index.get(verb_word.lower().replace("’", "'"), ())
            verb = tuple(c for c in readings if c[0] == "V")
            # only when the other word is unmistakably a verb, so nouns spelled alike stay quiet
            if not subject or not verb or len(verb) != len(readings):
                continue
            if not verb_fits_subject(verb, subject):
                issues.append({"words": f"{first} {second}",
                               "modifier": [f"{subject[0]}:{subject[1]}"],
                               "noun": sorted({":".join(c[1:]) for c in verb})})
            break
    return issues


def check_line(line, index):
    issues = []
    words = [w for w in WORD_RE.findall(line)]
    issues += check_subject_verb(words, index)
    for first, second in zip(words, words[1:]):
        a, b = first.lower().replace("’", "'"), second.lower().replace("’", "'")
        if a in PERSONAL or b in PERSONAL or a not in index or b not in index:
            continue
        # a word that also reads as an adverb, verb or particle ("тут") is not reliably part of
        # this pair, so leave it alone rather than raise a false alarm
        if any(c[0] == "X" for c in index[a]) or any(c[0] == "X" for c in index[b]):
            continue
        pair = order(a, b, words, index)
        if not pair:
            continue
        modifier, noun = pair
        if not agrees(modifier, noun):
            issues.append({"words": f"{first} {second}",
                           "modifier": sorted({":".join(c[1:]) for c in modifier}),
                           "noun": sorted({":".join(c[1:]) for c in noun})})
    return issues


def check_text(text, index=None):
    index = index if index is not None else load_index()
    lines = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("["):
            continue
        line = line.split("|")[0].strip()
        lines.append({"n": n, "text": line, "issues": check_line(line, index)})
    errors = sum(len(l["issues"]) for l in lines)
    return {"lines": lines, "errors": errors, "pass": errors == 0}


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
    p.add_argument("--index", help="a be-forms.tsv.gz; defaults to the published table")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    result = check_text(open(a.file, encoding="utf-8").read(), load_index(a.index))
    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for line in result["lines"]:
            print(f"{line['n']:>2} {line['text']}")
            for issue in line["issues"]:
                print(f"     does not agree: «{issue['words']}»  "
                      f"{'/'.join(issue['modifier'])} vs {'/'.join(issue['noun'])}")
        print(f"agreement errors: {result['errors']}")
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
