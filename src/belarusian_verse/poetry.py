#!/usr/bin/env python3
"""Judge Belarusian lyrics as verse: rhyme quality and rhythm, not just spelling.

be_check.py answers "are these real Belarusian words". This answers "is this a singable verse":

* **Rhyme** — a real rhyme matches from the last STRESSED vowel to the end of the line
  (вадзе́ / ідзе́), not merely the last letter. Graded: rich (the sound before the stressed vowel
  matches too), exact, near (same vowel, close endings), none.
* **Rhythm** — the pattern of stressed and unstressed syllables. Lines that are sung together
  should carry a similar pattern; the score says how close the lines are to the song's own
  dominant pattern, so an odd line stands out.

Stress comes from the GrammarDB lexicon (be_stress.py). One-syllable function words (і, у, на, не …)
count as unstressed, which is how they are actually sung.

Usage: be_poetry.py LYRICS.txt [--rhyme AABB] [--json]
"""
import argparse
import json
import re
import sys

from .stress import ACUTE, load_lexicon, mark_word

VOWELS = "аеёіоуыэюя"
WORD_RE = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*", re.UNICODE)
# short words that carry no stress of their own when sung
CLITICS = {"і", "у", "ў", "а", "але", "з", "са", "на", "за", "да", "ад", "пад", "над", "пра", "без",
           "для", "як", "што", "не", "ні", "бы", "б", "ж", "жа", "ці", "то", "вось", "той", "то",
           "мы", "ты", "вы", "я", "ён", "яна", "яны", "мне", "нам", "вам", "ім", "у́", "ва"}
# final consonants are devoiced when sung, so they rhyme with their voiceless partner
DEVOICE = str.maketrans({"б": "п", "д": "т", "ж": "ш", "з": "с", "г": "х", "в": "ф"})
# an iotated vowel rhymes with its plain partner: маёй rhymes with спакой
SOFT_VOWELS = str.maketrans({"ё": "о", "я": "а", "ю": "у", "е": "э", "і": "ы"})


def syllable_stress(line, lexicon):
    """-> list of 0/1 per syllable, one entry per vowel in the line."""
    pattern = []
    for word in WORD_RE.findall(line):
        marked, status = mark_word(word, lexicon, pick_first=True)
        plain = marked.lower()
        vowels = [i for i, c in enumerate(plain) if c in VOWELS]
        if len(vowels) == 1:
            pattern.append(0 if word.lower().strip("’'") in CLITICS else 1)
            continue
        stressed_at = plain.find(ACUTE)
        for n, at in enumerate(vowels):
            pattern.append(1 if stressed_at == at + 1 else 0)
    return pattern


def rhyme_tail(line, lexicon):
    """Everything from the last stressed vowel to the end, plus the sound before it."""
    words = WORD_RE.findall(line)
    if not words:
        return "", ""
    marked, _ = mark_word(words[-1], lexicon, pick_first=True)
    word = marked.lower().replace("’", "'")
    at = word.find(ACUTE)
    if at > 0:
        start = at - 1
    else:  # one-syllable word, or unknown: take the last vowel
        positions = [i for i, c in enumerate(word) if c in VOWELS]
        if not positions:
            return "", ""
        start = positions[-1]
    tail = word[start:].replace(ACUTE, "").replace("ь", "").translate(DEVOICE).translate(SOFT_VOWELS)
    before = word[start - 1] if start > 0 else ""
    return tail, before


def grade_rhyme(a, b, lexicon):
    tail_a, before_a = rhyme_tail(a, lexicon)
    tail_b, before_b = rhyme_tail(b, lexicon)
    if not tail_a or not tail_b:
        return "none", 0.0
    if tail_a == tail_b:
        if before_a and before_a == before_b:
            return "rich", 1.0
        return "exact", 0.9
    if tail_a[0] == tail_b[0]:  # same stressed vowel
        shared = len({tail_a[1:], tail_b[1:]}) == 1
        if shared or tail_a[1:2] == tail_b[1:2]:
            return "near", 0.6
        return "near", 0.4
    return "none", 0.0


def rhythm_scores(patterns):
    """How close each line is to the song's dominant stress pattern (1.0 = identical)."""
    width = max((len(p) for p in patterns), default=0)
    if not width:
        return [], []
    dominant = [1 if sum(p[i] for p in patterns if i < len(p)) * 2 >= sum(1 for p in patterns if i < len(p))
                else 0 for i in range(width)]
    scores = []
    for p in patterns:
        if not p:
            scores.append(0.0)
            continue
        same = sum(1 for i, v in enumerate(p) if dominant[i] == v)
        scores.append(round(same / len(p), 2))
    return dominant, scores


def analyse(text, rhyme="AABB", lexicon=None):
    lexicon = lexicon or load_lexicon()
    lines = [l.strip() for l in text.splitlines()
             if l.strip() and not l.strip().startswith(("[", "#"))]
    lines = [l.split("|")[0].strip() for l in lines]
    patterns = [syllable_stress(l, lexicon) for l in lines]
    dominant, rhythm = rhythm_scores(patterns)

    pairs, seen = [], {}
    for i, line in enumerate(lines):
        if rhyme and i % len(rhyme) == 0:
            # A scheme shorter than the song repeats for each stanza. Without this reset «ABCB» paired
            # every B line with line 2 — a verse line graded against the chorus.
            seen = {}
        letter = rhyme[i % len(rhyme)] if rhyme else None
        if letter and letter in seen:
            grade, score = grade_rhyme(lines[seen[letter]], line, lexicon)
            pairs.append({"lines": [seen[letter] + 1, i + 1], "grade": grade, "score": score})
        elif letter:
            seen[letter] = i
    rhyme_score = round(sum(p["score"] for p in pairs) / len(pairs), 2) if pairs else 0.0
    return {
        "lines": [{"n": i + 1, "text": l, "syllables": len(patterns[i]),
                   "stress": "".join(str(s) for s in patterns[i]), "rhythm": rhythm[i]}
                  for i, l in enumerate(lines)],
        "dominant_stress": "".join(str(s) for s in dominant),
        "rhyme_pairs": pairs,
        "rhyme_score": rhyme_score,
        "rhythm_score": round(sum(rhythm) / len(rhythm), 2) if rhythm else 0.0,
    }


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
    p.add_argument("file")
    p.add_argument("--rhyme", default="AABB")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    result = analyse(open(a.file, encoding="utf-8").read(), a.rhyme)
    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    for line in result["lines"]:
        print(f"{line['n']:>2} {line['stress']:<12} rhythm {line['rhythm']:.2f}  {line['text']}")
    print(f"dominant rhythm: {result['dominant_stress']}")
    for pair in result["rhyme_pairs"]:
        print(f"rhyme {pair['lines'][0]}-{pair['lines'][1]}: {pair['grade']} ({pair['score']})")
    print(f"rhyme {result['rhyme_score']}  rhythm {result['rhythm_score']}")
    sys.exit(0 if result["rhyme_score"] >= 0.6 and result["rhythm_score"] >= 0.7 else 1)


if __name__ == "__main__":
    main()
