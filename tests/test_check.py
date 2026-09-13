"""Tests for tools/be_check.py. Run from the project root: python -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

from belarusian_verse.spelling import (short_u_issues, check_text, load_dictionary, load_extra,  # noqa: E402
                                       rhyme_key, syllables, word_issues)

SAMPLES = ROOT / "experiments" / "2026-09-11-belarusian-lyrics" / "samples"


def codes(result):
    return {(i["code"], i["word"]) for e in result["lines"] for i in e["issues"]}


class ShortUTests(unittest.TestCase):
    """The у/ў rule runs between words, so only a whole-line check can see it."""

    def codes(self, line):
        return {code for _level, code, _word in short_u_issues(line)}

    def test_u_after_a_vowel_must_be_short(self):
        self.assertIn("SHOULD_BE_U_SHORT", self.codes("Я іду у школу"))
        self.assertEqual(self.codes("Я іду ў школу"), set())

    def test_u_after_a_consonant_stays_long(self):
        self.assertEqual(self.codes("Стаў у хаце"), set())
        self.assertIn("SHOULD_BE_U_LONG", self.codes("Стаў ў хаце"))

    def test_a_full_stop_resets_the_rule(self):
        self.assertEqual(self.codes("Дождж ідзе. У хаце цёпла"), set())


class WordInitialUTests(unittest.TestCase):
    """The у/ў rule reaches words that begin with у, not only the preposition."""

    def codes(self, line):
        return [code for _level, code, _word in short_u_issues(line)]

    def test_short_u_word_after_a_consonant_is_wrong(self):
        self.assertIn("SHOULD_BE_U_LONG", self.codes("Лета нас тут ўсё запрашае"))

    def test_long_u_word_after_a_consonant_is_right(self):
        self.assertEqual(self.codes("Лета нас тут усё запрашае"), [])

    def test_long_u_word_after_a_vowel_is_wrong(self):
        self.assertIn("SHOULD_BE_U_SHORT", self.codes("Яна усё ведае"))

    def test_short_u_word_after_a_vowel_is_right(self):
        self.assertEqual(self.codes("Яна ўсё ведае"), [])

    def test_a_line_may_not_start_with_a_short_u_word(self):
        self.assertIn("SHOULD_BE_U_LONG", self.codes("Ўсё будзе добра"))

    def test_an_abbreviation_keeps_its_u(self):
        # «УНП» is read letter by letter, so it keeps its у after a vowel
        self.assertEqual(self.codes("Яна УНП ведае"), [])


class ProvenanceTests(unittest.TestCase):
    """Public-domain lyrics carry a `#` note saying where the text came from."""

    def test_a_comment_is_not_checked_as_a_line(self):
        text = "# Казлоў 1827, грамадскі набытак\nВячэрні звон, вячэрні звон!"
        self.assertEqual([l["text"] for l in check_text(text)["lines"]], ["Вячэрні звон, вячэрні звон!"])


class NothingKnown:
    """A dictionary that knows no word at all."""

    def lookup(self, _word):
        return False


class ExtraWordsTests(unittest.TestCase):
    """extra-words.txt fills the dictionary's gaps without weakening the checker."""

    def test_the_file_loads_and_holds_a_known_gap(self):
        # слухаўка is an ordinary word (a telephone receiver) that be-official does not list
        self.assertIn("слухаўка", load_extra())

    def test_comments_and_blank_lines_are_not_words(self):
        words = load_extra()
        self.assertNotIn("", words)
        self.assertFalse([w for w in words if w.startswith("#") or " " in w])

    def test_a_supplemented_word_is_accepted(self):
        codes = [c for _l, c, _w in word_issues("Слухаўка", NothingKnown(), {"слухаўка"})]
        self.assertNotIn("UNKNOWN_WORD", codes)

    def test_an_invented_word_is_still_refused(self):
        codes = [c for _l, c, _w in word_issues("зяленіцься", NothingKnown(), {"слухаўка"})]
        self.assertIn("UNKNOWN_WORD", codes)


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

    def test_real_words_missing_from_the_dictionary_pass(self):
        # GrammarDB lists these forms; be-official does not
        for word in ("слухаўка", "слухаўкі", "слухаўку", "слухаўкай", "слухаўцы", "гучыш"):
            with self.subTest(word=word):
                self.assertEqual(check_text(word, dictionary=self.dictionary)["errors"], 0)


class GrammarDBFallbackTests(unittest.TestCase):
    """A word GrammarDB lists but the 2008-spelling dictionary leaves out is a warning, not an error."""

    def issues(self, word, forms):
        return [(l, c) for l, c, _w in word_issues(word, NothingKnown(), set(), forms)]

    def test_a_listed_word_outside_the_2008_list_is_only_a_warning(self):
        issues = self.issues("смаленская", {"смаленская": (("A", "F", "N", "S"),)})
        self.assertIn(("WARN", "NOT_IN_2008_LIST"), issues)
        self.assertNotIn(("ERROR", "UNKNOWN_WORD"), issues)

    def test_a_word_nobody_lists_is_still_an_error(self):
        self.assertIn(("ERROR", "UNKNOWN_WORD"), self.issues("паветры", {"паветра": ()}))

    def test_without_forms_the_old_rule_holds(self):
        self.assertIn(("ERROR", "UNKNOWN_WORD"), self.issues("смаленская", None))

    def test_extra_words_still_pass_without_a_warning(self):
        issues = [(l, c) for l, c, _w in word_issues("слухаўка", NothingKnown(), {"слухаўка"}, {})]
        self.assertEqual(issues, [])

    def test_check_text_passes_the_forms_through(self):
        result = check_text("Смаленская дарога", dictionary=NothingKnown(),
                            forms={"смаленская": (), "дарога": ()})
        self.assertEqual(result["errors"], 0)
        self.assertEqual(result["warnings"], 2)


if __name__ == "__main__":
    unittest.main()
