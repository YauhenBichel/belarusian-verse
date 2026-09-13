"""Tests for tools/be_poetry.py — rhyme grading and rhythm, using the real stress lexicon."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

from belarusian_verse.poetry import analyse, grade_rhyme, rhyme_tail, syllable_stress  # noqa: E402
from belarusian_verse.stress import load_lexicon  # noqa: E402

LEXICON = None


class RhymeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = load_lexicon()

    def test_same_stressed_ending_is_a_rhyme(self):
        self.assertEqual(grade_rhyme("вадзе", "ідзе", self.lex)[0], "rich")
        self.assertEqual(grade_rhyme("плыве", "жыве", self.lex)[0], "rich")

    def test_iotated_vowel_rhymes_with_its_plain_partner(self):
        # маёй / спакой sound the same from the stressed vowel on
        self.assertEqual(grade_rhyme("маёй", "спакой", self.lex)[0], "exact")

    def test_different_stress_is_not_a_rhyme(self):
        # ідзе́ is stressed at the end, зна́йдзе at the start
        self.assertEqual(grade_rhyme("ідзе", "знайдзе", self.lex)[0], "none")

    def test_unrelated_endings_do_not_rhyme(self):
        self.assertEqual(grade_rhyme("сне", "вазе", self.lex)[0], "none")

    def test_rhyme_tail_starts_at_the_stressed_vowel(self):
        tail, before = rhyme_tail("спакой", self.lex)
        self.assertEqual(tail, "ой")
        self.assertEqual(before, "к")

    def test_stress_pattern_marks_one_beat_per_syllable(self):
        pattern = syllable_stress("Сэрца знайшло тут свой спакой.", self.lex)
        self.assertEqual(len(pattern), 8)  # э-а-а-ы-о-у-о-о
        self.assertIn(1, pattern)

    def test_function_words_are_unstressed(self):
        self.assertEqual(syllable_stress("і ў на", self.lex), [0, 0])  # ў is not a syllable

    def test_analyse_scores_a_clean_verse_highly(self):
        verse = ("Белы туман па лесе плыве,\nСвежасць ранішняя тут жыве.\n"
                 "Сосны стаяць у цішы маёй,\nСэрца знайшло тут свой спакой.")
        result = analyse(verse, "AABB", self.lex)
        self.assertGreaterEqual(result["rhyme_score"], 0.9)
        self.assertEqual(len(result["lines"]), 4)

    def test_analyse_marks_a_broken_rhyme(self):
        verse = ("Дождж за акном ціха ідзе,\nСэрца спакой тут знайдзе.\n"
                 "П’ю я гарачы свой чай,\nДом мой як сапраўдны рай.")
        result = analyse(verse, "AABB", self.lex)
        self.assertEqual(result["rhyme_pairs"][0]["grade"], "none")
        self.assertEqual(result["rhyme_pairs"][1]["grade"], "exact")

    def test_bilingual_lines_use_the_belarusian_half(self):
        result = analyse("Сосны стаяць у цішы маёй, | Pine trees stand in my silence", "A", self.lex)
        self.assertEqual(result["lines"][0]["text"], "Сосны стаяць у цішы маёй,")

    def test_a_provenance_comment_is_not_a_line(self):
        result = analyse("# Казлоў 1827\nВячэрні звон, вячэрні звон!\nЯк многа дум наводзіць ён",
                         "AA", self.lex)
        self.assertEqual(len(result["lines"]), 2)


if __name__ == "__main__":
    unittest.main()
