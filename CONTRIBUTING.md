# Contributing

Corrections are especially welcome: the library encodes rules of Belarusian, and a native speaker
will spot what a dictionary cannot.

## Reporting a linguistic mistake

Open an issue with the word or line, what the tool said, and what it should say. Examples that
helped shape the current behaviour:

- `ўдваіх` — stress was a syllable off, because `ў` is not a vowel while `у` is.
- `тут` — flagged as a noun disagreeing with an adjective, when it is the adverb "here".
- `ідзе́ / зна́йдзе` — accepted as a rhyme by anything that only compares final letters.

## Changing the code

```bash
pip install -e ".[spelling]"
python -m unittest discover tests
```

Every behaviour change needs a test, and a linguistic rule needs a test naming a real word. Tests
run against the published tables and download them on first use; set `BELARUSIAN_VERSE_DATA` to a
local folder to work offline.

Keep the tools deterministic: this library answers questions from a dictionary, not from a model.

## Data

The tables live in a separate dataset (CC BY-SA 4.0, from the Belarusian Grammar Database). Fixes
to the *data* belong upstream at https://github.com/Belarus/GrammarDB; fixes to how we read it
belong here. `data/stress-overrides.tsv` in the dataset is for homographs where the dictionary
lists several stresses and one must be chosen.

## Licence

Code contributions are accepted under Apache-2.0.
