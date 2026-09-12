"""Tests for tools/be_check.py. Run from the project root: python -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

from belarusian_verse.spelling import check_text, load_dictionary, rhyme_key, syllables  # noqa: E402

SAMPLES = ROOT / "experiments" / "2026-09-11-belarusian-lyrics" / "samples"


def codes(result):
    return {(i["code"], i["word"]) for e in result["lines"] for i in e["issues"]}


class RuleTests(unittest.TestCase):
    def test_russian_letter_is_bad_char(self):
        self.assertIn(("BAD_CHAR", "тихі [и]"), codes(check_text("Вечар тихі")))

    def test_cjk_is_bad_char(self):
        self.assertIn(("BAD_CHAR", "пры孔 [孔]"), codes(check_text("усё ўжо пры孔")))

    def test_soft_t_and_d(self):
        found = {c for c, _ in codes(check_text("тепла дед"))}
        self.assertEqual(found, {"SOFT_T_D"})

    def test_dz_and_dzh_are_not_soft_d(self):
        self.assertEqual(check_text("дзень дзякуй")["errors"], 0)

    def test_hard_consonants(self):
        self.assertIn(("HARD_CONS", "дожджь"), codes(check_text("дожджь")))
        self.assertIn(("HARD_CONS", "шепча"), codes(check_text("шепча")))

    def test_syllables_ignore_u_short(self):
        self.assertEqual(syllables("Дождж ціхенька стукае ў шкло"), 8)

    def test_syllable_error(self):
        result = check_text("Дождж ціхенька стукае ў шкло", syllables_per_line=7)
        self.assertIn("SYLLABLES", {c for c, _ in codes(result)})

    def test_tolerance_allows_near_misses(self):
        line = "Дождж ціхенька стукае ў шкло"  # 8 syllables
        self.assertIn("SYLLABLES", {c for c, _ in codes(check_text(line, syllables_per_line=7))})
        self.assertEqual(check_text(line, syllables_per_line=7, tolerance=1)["errors"], 0)
        self.assertEqual(check_text(line, syllables_per_line=6, tolerance=1)["errors"], 1)

    def test_rhyme_key_normalises_iotated_vowels(self):
        self.assertEqual(rhyme_key("зямля"), rhyme_key("вада"))

    def test_trailing_count_is_stripped(self):
        self.assertEqual(check_text("Дождж ціхенька (8)")["lines"][0]["text"], "Дождж ціхенька")


class DictionaryTests(unittest.TestCase):
    """Against the published Belarusian dictionary."""

    @classmethod
    def setUpClass(cls):
        cls.dictionary = load_dictionary()

    def test_correct_belarusian_passes(self):
        text = ("Дождж ціхенька стукае ў шкло,\nУ хаце цёпла і светла.\n"
                "Мы п’ём гарбату ўдваіх\nІ дзякуем за кожны дзень.")
        self.assertTrue(check_text(text, dictionary=self.dictionary)["pass"])

    def test_russian_and_ukrainian_forms_are_unknown(self):
        result = check_text("свічка вікон танцюе", dictionary=self.dictionary)
        self.assertEqual(result["errors"], 3)

    def test_invented_words_are_caught(self):
        result = check_text("шклярана навокны цяплёў", dictionary=self.dictionary)
        self.assertEqual(result["errors"], 3)

if __name__ == "__main__":
    unittest.main()
