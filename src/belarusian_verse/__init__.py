"""Tools for Belarusian verse: stress, rhyme, rhythm, agreement, spelling.

    from belarusian_verse import mark_stress, rhyme, check_agreement

    mark_stress("побач")                       # 'по́бач'
    rhyme("вадзе", "ідзе")                     # ('rich', 1.0)
    check_agreement("тваіх вачам")["errors"]   # 1

The tables behind these (about 2 million word forms) are downloaded once from
https://huggingface.co/datasets/YauhenBichel/belarusian-verse and cached.
"""
from .data import DATASET, table
from .grammar import agrees, check_text as check_agreement, load_index
from .poetry import analyse as analyse_verse, grade_rhyme, rhyme_tail, syllable_stress
from .respell import respell
from .spelling import check_text as check_spelling, load_dictionary, syllables
from .stress import load_lexicon, mark_text, mark_word

__version__ = "0.1.0"
__all__ = [
    "DATASET", "table",
    "mark_stress", "mark_text", "mark_word", "load_lexicon",
    "rhyme", "grade_rhyme", "rhyme_tail", "syllable_stress", "analyse_verse",
    "check_agreement", "agrees", "load_index",
    "check_spelling", "load_dictionary", "syllables",
    "respell",
]

_lexicon = None
_index = None


def _cached_lexicon():
    global _lexicon
    if _lexicon is None:
        _lexicon = load_lexicon()
    return _lexicon


def _cached_index():
    global _index
    if _index is None:
        _index = load_index()
    return _index


def mark_stress(text):
    """'побач' -> 'по́бач'. Words of one syllable and unknown words are left alone."""
    marked, _stats, _unknown = mark_text(text, _cached_lexicon())
    return marked


def rhyme(a, b):
    """Grade a rhyme between two lines or two words: (grade, score 0..1).

    'rich', 'exact', 'near' or 'none', judged from the last stressed vowel onward.
    """
    return grade_rhyme(a, b, _cached_lexicon())
