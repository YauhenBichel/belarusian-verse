"""Tests for tools/be_rhymes.py — rhyme suggestion, ranked by how common a word actually is."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

from belarusian_verse.rhymes import endings_of, load_frequency, load_rhymes, suggest  # noqa: E402
from belarusian_verse.build_rhyme_index import rhyme_ending  # noqa: E402

RHYMES = FREQUENCY = None  # the package downloads its tables


class EndingTests(unittest.TestCase):
    def test_ending_starts_at_the_stressed_vowel(self):
        self.assertEqual(rhyme_ending("спакой", 2), "ой")
        self.assertEqual(rhyme_ending("вадзе", 2), "э")

    def test_iotated_vowels_are_folded(self):
        # маёй and спакой must land in the same group
        self.assertEqual(rhyme_ending("маёй", 2), rhyme_ending("спакой", 2))

    def test_final_consonant_is_devoiced(self):
        self.assertEqual(rhyme_ending("мароз", 2), "ос")

    def test_overrides_settle_an_ambiguous_word(self):
        # вадзе is written with two possible stresses; our override picks вадзе́
        self.assertEqual(endings_of("вадзе"), ["э"])


class SuggestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rhymes = load_rhymes()
        cls.frequency = load_frequency()

    def words(self, word, **kw):
        found = suggest(word, self.rhymes, frequency=self.frequency, **kw)
        return [w for w, _grade, _count in found]

    def test_finds_a_real_rhyme(self):
        self.assertIn("дзе", self.words("вадзе", limit=20))

    def test_one_syllable_words_can_rhyme(self):
        self.assertTrue(self.words("мне", limit=10))

    def test_the_word_itself_is_not_suggested(self):
        self.assertNotIn("вадзе", self.words("вадзе", limit=50))

    def test_common_words_come_first(self):
        found = suggest("вадзе", self.rhymes, limit=10, frequency=self.frequency)
        counts = [count for _w, _g, count in found]
        self.assertEqual(counts, sorted(counts, reverse=True))
        # the rare derivations that used to dominate are gone from the top
        self.assertNotIn("кувадзе", [w for w, _g, _c in found])


if __name__ == "__main__":
    unittest.main()
