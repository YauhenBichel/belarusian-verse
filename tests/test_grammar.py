"""Tests for tools/be_grammar.py — Belarusian agreement checking against the GrammarDB index."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

from belarusian_verse.grammar import agrees, check_text, load_index  # noqa: E402

INDEX = None


class AgreesTests(unittest.TestCase):
    def test_same_case_number_and_gender_agree(self):
        self.assertTrue(agrees((("A", "M", "N", "S"),), (("N", "M", "N", "S"),)))

    def test_unspecified_gender_still_agrees(self):
        self.assertTrue(agrees((("S", "0", "D", "P"),), (("N", "N", "D", "P"),)))

    def test_different_case_does_not_agree(self):
        self.assertFalse(agrees((("S", "0", "G", "P"),), (("N", "N", "D", "P"),)))

    def test_different_gender_does_not_agree(self):
        self.assertFalse(agrees((("A", "F", "N", "S"),), (("N", "M", "N", "S"),)))

    def test_any_matching_reading_is_enough(self):
        modifier = (("S", "0", "G", "P"), ("S", "0", "D", "P"))
        self.assertTrue(agrees(modifier, (("N", "N", "D", "P"),)))


class RealSentenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = load_index()

    def errors(self, text):
        return check_text(text, self.index)["errors"]

    def test_wrong_case_is_caught(self):
        self.assertEqual(self.errors("Сэрца б’ецца ў такт тваіх вачам"), 1)

    def test_right_case_passes(self):
        self.assertEqual(self.errors("Сэрца б’ецца ў такт тваім вачам"), 0)

    def test_wrong_gender_is_caught(self):
        self.assertEqual(self.errors("Цёплая вечар у цішыні"), 1)

    def test_right_gender_passes(self):
        self.assertEqual(self.errors("Цёплы вечар у цішыні"), 0)

    def test_adjective_after_its_noun_is_checked(self):
        # Belarusian verse allows "свежасць ранішняя"; the wrong gender must still be caught
        self.assertEqual(self.errors("Свежасць ранішні тут жыве"), 1)
        self.assertEqual(self.errors("Свежасць ранішняя тут жыве"), 0)

    def test_modifier_belongs_to_the_noun_that_follows_it(self):
        # in "у такт тваім вачам" тваім modifies вачам, not такт before it
        self.assertEqual(self.errors("Сэрца б’ецца ў такт тваім вачам"), 0)

    def test_a_broken_pair_is_reported_once(self):
        self.assertEqual(self.errors("Сэрца б’ецца ў такт тваіх вачам"), 1)

    def test_subject_and_verb_must_agree(self):
        self.assertEqual(self.errors("Яна ідуць дадому"), 1)
        self.assertEqual(self.errors("Яна ідзе дадому"), 0)
        self.assertEqual(self.errors("Мы танцуе да раніцы"), 1)
        self.assertEqual(self.errors("Мы танцуем да раніцы"), 0)

    def test_past_tense_agrees_in_gender(self):
        self.assertEqual(self.errors("Яна спявалі песню"), 1)
        self.assertEqual(self.errors("Яна спявала песню"), 0)
        self.assertEqual(self.errors("Яны спявалі песню"), 0)

    def test_adverb_lookalike_is_not_a_false_alarm(self):
        # "тут" is an adverb here, though GrammarDB also lists a rare noun spelled the same
        self.assertEqual(self.errors("Свежасць ранішняя тут жыве"), 0)

    def test_personal_pronoun_before_a_noun_is_not_checked(self):
        self.assertEqual(self.errors("Мы п’ём гарбату"), 0)

    def test_headers_and_english_halves_are_skipped(self):
        text = "[Куплет]\nЦёплы вечар у цішыні. | A warm evening in the quiet"
        self.assertEqual(self.errors(text), 0)

    def test_capitalised_words_do_not_crash_the_checker(self):
        # a modifier after its noun, capitalised: finding its position used to raise ValueError,
        # on the second sentence of the MultiBLiMP Belarusian set
        self.errors("Дзень Цёплы прыйшоў да нас")
        self.errors("Я Мікіта, мне 19 год, вучуся ў БДУіРы на другім курсе.")

    def test_a_provenance_comment_is_skipped(self):
        # a `#` note says where a text came from; it is not a line of verse
        self.assertEqual(self.errors("# Цёплая вечар у цішыні\nЦёплы вечар у цішыні"), 0)


if __name__ == "__main__":
    unittest.main()
