# belarusian-verse

Belarusian **stress, rhyme, rhythm, agreement and spelling** — the checks you need to write or
judge a line of Belarusian verse, as a small Python library.

```python
from belarusian_verse import mark_stress, rhyme, check_agreement, check_spelling

mark_stress("Побач ты, і добра мне")      # 'По́бач ты, і до́бра мне'
rhyme("вадзе", "ідзе")                    # ('rich', 1.0)
rhyme("ідзе", "знайдзе")                  # ('none', 0.0)  — зна́йдзе is stressed at the start
check_agreement("тваіх вачам")["errors"]  # 1  — no shared case
check_agreement("тваім вачам")["errors"]  # 0
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

Set `BELARUSIAN_VERSE_DATA` to a folder holding the tables to work offline.

## What it does

| Function | Question it answers |
|---|---|
| `mark_stress(text)` | Where does the stress fall? (`по́бач`, not `паба́ч`) |
| `rhyme(a, b)` | Do these rhyme, and how well: rich / exact / near / none |
| `analyse_verse(text, "AABB")` | Rhyme and rhythm scores for a whole verse, line by line |
| `check_agreement(text)` | Does each adjective match its noun in gender, case and number? |
| `check_spelling(text, dictionary=…)` | Real Belarusian words, correct orthography, syllable counts |
| `respell(text, "uk"\|"ru")` | Rewrite Belarusian so a Ukrainian- or Russian-trained model pronounces it, syllable count unchanged |

Each is also a command: `be-stress`, `be-poetry`, `be-grammar`, `be-spelling`, `be-respell`.

```bash
$ be-poetry verse.txt --rhyme AABB
 1 100111001    rhythm 1.00  Белы туман па лесе плыве,
 2 101000101    rhythm 0.44  Свежасць ранішняя тут жыве.
rhyme 1-2: rich (1.0)
rhyme 0.95  rhythm 0.78
```

## How rhyme is judged

A Belarusian rhyme matches from the **last stressed vowel** to the end of the line, so the stress
table does the real work. `маёй` and `спакой` rhyme (iotated vowels are folded: `ёй` = `ой`);
`ідзе́` and `зна́йдзе` do not, because the stress sits elsewhere. Final consonants are devoiced
before comparison, as they are when sung.

## Two Belarusian rules this encodes

- **`ё` is always stressed**, so a word containing it needs no lookup.
- **A word starting with `ў` is the same word as the one starting with `у`** (`ўдваіх` = `удваіх`),
  but `ў` is not a vowel, so every stress index shifts by one. Getting this wrong moves the stress
  a syllable — it is the kind of bug that only shows up when a singer sings it.

## Limits

- Homographs are not disambiguated by context: 20,754 forms carry more than one stress. Pass your
  own overrides file, or `pick_first=True` to accept the first reading.
- Agreement checking looks at adjacent adjective/pronoun and noun pairs on either side, not at full
  syntax; it finds the common errors, not every possible one.
- Meaning is not checked at all. A line can pass every check here and still say nothing.

## Data and licence

The code is **Apache-2.0**. The tables it downloads are **CC BY-SA 4.0**, derived from the
Belarusian Grammar Database by Aleś Bułojčyk and Uładzimir Koščanka — if you redistribute the data
or a derivative of it, keep that licence and the attribution:
https://huggingface.co/datasets/YauhenBichel/belarusian-verse

## Tests

```bash
pip install -e ".[spelling]" && python -m unittest discover tests
```
