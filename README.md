# belarusian-verse

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](./LICENSE)
[![PyPI](https://img.shields.io/pypi/v/belarusian-verse.svg)](https://pypi.org/project/belarusian-verse/)
[![CI](https://github.com/YauhenBichel/belarusian-verse/actions/workflows/ci.yml/badge.svg)](https://github.com/YauhenBichel/belarusian-verse/actions/workflows/ci.yml)
[![Dataset](https://img.shields.io/badge/%F0%9F%A4%97%20dataset-belarusian--verse-yellow)](https://huggingface.co/datasets/YauhenBichel/belarusian-verse)
[![Data licence](https://img.shields.io/badge/data-CC%20BY--SA%204.0-lightgrey)](https://huggingface.co/datasets/YauhenBichel/belarusian-verse)
[![Contributors](https://img.shields.io/github/contributors/YauhenBichel/belarusian-verse)](https://github.com/YauhenBichel/belarusian-verse/graphs/contributors)

Belarusian **stress, rhyme, rhythm, agreement and spelling** — the checks you need to write or
judge a line of Belarusian verse, as a small Python library.

The tables behind it — about 2 million word forms — are published separately as
[🤗 **YauhenBichel/belarusian-verse**](https://huggingface.co/datasets/YauhenBichel/belarusian-verse)
and downloaded on first use.

```python
from belarusian_verse import mark_stress, rhyme, suggest_rhymes, check_agreement

mark_stress("Побач ты, і добра мне")      # 'По́бач ты, і до́бра мне'
rhyme("вадзе", "ідзе")                    # ('rich', 1.0)
rhyme("ідзе", "знайдзе")                  # ('none', 0.0)  — зна́йдзе is stressed at the start
check_agreement("тваіх вачам")["errors"]  # 1  — no shared case
check_agreement("Яна ідуць")["errors"]    # 1  — singular subject, plural verb
suggest_rhymes("вадзе")[:4]               # what *would* rhyme, commonest first
```

## Why

Belarusian has good dictionaries and good speech models, and little in between:

- **no rhyme dictionary in software** — only Minkin's printed one;
- **LanguageTool's Belarusian module has ~66 rules and almost no morphology**, so it cannot see
  that «тваіх вачам» is ungrammatical;
- a spell checker accepts every real word, so «ідзе́ / зна́йдзе» passes as a rhyme even though the
  two words are stressed on different syllables.

Everything needed was already inside the [Belarusian Grammar Database](https://github.com/Belarus/GrammarDB):
stress marks and full morphological tags for millions of forms. This library is those tables plus
the rules that make them answer musical questions.

## Install

```bash
pip install belarusian-verse            # tables download on first use, then cached
pip install "belarusian-verse[spelling]"  # adds the spell checker (spylls)
```

Set `BELARUSIAN_VERSE_DATA` to a folder holding the tables to work offline. Put BelVoice's
`stresses-stat.json` there too for homograph stress; without it homographs keep GrammarDB's order.

## What it does

| Function | Question it answers |
|---|---|
| `mark_stress(text)` | Where does the stress fall? (`по́бач`, not `паба́ч`) |
| `rhyme(a, b)` | Do these rhyme, and how well: rich / exact / near / none |
| `analyse_verse(text, "AABB")` | Rhyme and rhythm scores for a whole verse, line by line |
| `check_agreement(text)` | Does each adjective match its noun in gender, case and number? |
| `check_spelling(text, dictionary=…, forms=…)` | Real Belarusian words, correct orthography, syllable counts |
| `respell(text, "uk"\|"ru")` | Rewrite Belarusian so a Ukrainian- or Russian-trained model pronounces it, syllable count unchanged |
| `suggest_rhymes(word)` | Words that rhyme with it, commonest first — rhyme as help, not just a verdict |

Each is also a command: `be-stress`, `be-poetry`, `be-grammar`, `be-spelling`, `be-respell`, `be-rhymes`.

```bash
$ be-poetry verse.txt --rhyme AABB
 1 100111001    rhythm 1.00  Белы туман па лесе плыве,
 2 101000101    rhythm 0.44  Свежасць ранішняя тут жыве.
rhyme 1-2: rich (1.0)
rhyme 0.95  rhythm 0.78
```

## What it checks that a spell checker cannot

- **Agreement.** An adjective must match its noun in gender, case and number, on either side of it
  («цёплы вечар», «свежасць ранішняя»); a verb must match its subject in person and number, or in
  gender for the past tense («яна спявала», «яны спявалі»).
- **The у/ў rule between words.** `у` becomes `ў` after a vowel — «Я іду **ў** школу» — and stays
  `у` after a consonant. The decision lives in the gap between two words, so no word-by-word
  checker can see it.
- **Rhyme and rhythm**, from the stressed vowel, not from the final letters.
- **Spelling, with the dictionary's gaps marked as gaps.** The bundled Hunspell dictionary is
  GrammarDB's own 2008-spelling export, which leaves out forms whose only source is Піскуноў 2012
  («слухаўка») and adjectives from place names («смаленская»). Pass `forms=load_index()` and a word
  the dictionary rejects but GrammarDB lists is a warning (`NOT_IN_2008_LIST`) instead of an
  `UNKNOWN_WORD` error. By default `forms` is not loaded and the old rule holds; `extra-words.txt`
  still accepts its words outright.

## How rhyme is judged

A Belarusian rhyme matches from the **last stressed vowel** to the end of the line, so the stress
table does the real work. `маёй` and `спакой` rhyme (iotated vowels are folded: `ёй` = `ой`);
`ідзе́` and `зна́йдзе` do not, because the stress sits elsewhere. Final consonants are devoiced
before comparison, as they are when sung.

A scheme shorter than the verse repeats for each stanza: `ABCB` over eight lines pairs 2–4 and 6–8,
and `AABB` pairs 1–2, 3–4, 5–6, 7–8.

## Homograph stress

GrammarDB lists the stresses of a homograph in no particular order. Where one reading must be
chosen (`pick_first=True`, and rhyme and rhythm in `analyse_verse`), the library puts first the most
frequent stress from [BelVoice](https://github.com/Belarus/BelVoice)'s table of common homographs,
when that stress is one GrammarDB lists. On the
[Belarusian Homographs Stress Benchmark](https://huggingface.co/datasets/alex73/benchmarks-stress-bel)
(`python -m belarusian_verse.stress_benchmark`), share of homograph tokens stressed right:

| Set | GrammarDB order | BelVoice first |
|---|---|---|
| Common Voice sentences | 48.9 % | 82.9 % |
| «Засценак Малінаўка» (literary) | 24.9 % | 68.8 % |
| 10×10 (every stress equally often) | 50.0 % | 50.0 % |

10×10 is built so that frequency alone cannot win; only context could. If BelVoice's table cannot be
downloaded, homographs silently keep GrammarDB's order. `load_lexicon(homographs="")` asks for that
order explicitly.

## Two Belarusian rules this encodes

- **`ё` is always stressed**, so a word containing it needs no lookup.
- **A word starting with `ў` is the same word as the one starting with `у`** (`ўдваіх` = `удваіх`),
  but `ў` is not a vowel, so every stress index shifts by one. Getting this wrong moves the stress
  a syllable — it is the kind of bug that only shows up when a singer sings it.

## Limits

- Homographs are not disambiguated by context: 20,754 forms carry more than one stress, and
  `mark_stress` leaves them unmarked. Pass your own overrides file, or `pick_first=True` to accept
  the most frequent reading — wrong about one time in six in ordinary sentences, and about one in
  three in literary text.
- Agreement checking looks at adjacent adjective/pronoun and noun pairs on either side, not at full
  syntax; it finds the common errors, not every possible one.
- Meaning is not checked at all. A line can pass every check here and still say nothing.
- Preposition government (`да` wants the genitive, `у` the accusative or locative) is not checked.
- Rhyme suggestions are ranked by Wikipedia frequency, which leans encyclopaedic: place names are
  commoner there than in song.

## Data and licence

The code is **Apache-2.0**. The tables it downloads are **CC BY-SA 4.0**, derived from the
Belarusian Grammar Database by Aleś Bułojčyk and Uładzimir Koščanka — if you redistribute the data
or a derivative of it, keep that licence and the attribution:
https://huggingface.co/datasets/YauhenBichel/belarusian-verse

Two more sources are downloaded at run time and never shipped with the package:

- **BelVoice's `stresses-stat.json`** (most frequent stress of common homographs), by Aleś Bułojčyk
  and contributors, **LGPL-3.0-or-later**, fetched from
  [a pinned commit](https://github.com/Belarus/BelVoice/blob/60401e614210f8788d13cbfd9df6bb4726845c38/framework/belvoice/synth/stress/stresses-stat.json)
  and checked against its SHA-256.
- **The Belarusian Homographs Stress Benchmark**, used only by `stress_benchmark`, created for
  BelVoice by Aleś Bułojčyk and contributors, **CC BY-SA 4.0**:
  https://huggingface.co/datasets/alex73/benchmarks-stress-bel (revision `94bb5a8`).

## Tests

```bash
pip install -e ".[spelling]" && python -m unittest discover tests
```
