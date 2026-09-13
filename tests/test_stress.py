"""Tests for tools/be_stress.py and for stress marks passing through the other tools."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

from belarusian_verse.spelling import check_text, syllables  # noqa: E402
from belarusian_verse.respell import respell  # noqa: E402
from belarusian_verse.stress import ACUTE, load_lexicon, mark_text, mark_word  # noqa: E402

LEXICON = None


class StressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = load_lexicon()

    def test_pobach_is_stressed_on_the_first_syllable(self):
        self.assertEqual(mark_word("побач", self.lex), ("по" + ACUTE + "бач", "marked"))

    def test_capitalised_word_keeps_its_capital(self):
        self.assertEqual(mark_word("Побач", self.lex)[0], "По" + ACUTE + "бач")

    def test_one_syllable_words_are_left_alone(self):
        self.assertEqual(mark_word("ліст", self.lex), ("ліст", "single"))

    def test_word_starting_with_u_short_is_found(self):
        marked, status = mark_word("ўдваіх", self.lex)
        self.assertEqual(status, "marked")
        self.assertEqual(marked, "ўдваі" + ACUTE + "х")

    def test_ambiguous_word_is_left_alone_unless_asked(self):
        plain = load_lexicon(overrides="")  # without the overrides file
        self.assertEqual(mark_word("вадзе", plain)[1], "ambiguous")
        self.assertEqual(mark_word("вадзе", plain, pick_first=True)[1], "marked")

    def test_overrides_resolve_an_ambiguous_word(self):
        # data/stress/overrides.tsv pins вадзе to the second vowel (вадзе́)
        self.assertEqual(mark_word("вадзе", self.lex), ("вадзе" + ACUTE, "marked"))

    def test_marking_does_not_change_syllable_count(self):
        text = "Побач ты, і добра мне,"
        marked, _, _ = mark_text(text, self.lex)
        self.assertEqual(syllables(marked), syllables(text))

    def test_section_tags_and_notes_are_left_alone(self):
        # «[Купле́т]» is no longer a tag a singing model recognises
        marked, _stats, _unknown = mark_text("# Казлоў 1827\n[Куплет]\nВячэрні звон", self.lex)
        lines = marked.split("\n")
        self.assertEqual(lines[0], "# Казлоў 1827")
        self.assertEqual(lines[1], "[Куплет]")
        self.assertIn(ACUTE, lines[2])


class PassThroughTests(unittest.TestCase):
    def test_checker_ignores_stress_marks(self):
        self.assertEqual(check_text("по" + ACUTE + "бач")["errors"], 0)

    def test_respell_keeps_stress_and_still_iotates(self):
        # "Ёсць" with a stress mark still becomes "Йосць" for Ukrainian
        self.assertEqual(respell("Ё" + ACUTE + "сць", "uk"), "Йо" + ACUTE + "сць")
        self.assertEqual(respell("ці" + ACUTE + "ха", "ru"), "ци" + ACUTE + "ха")


if __name__ == "__main__":
    unittest.main()
