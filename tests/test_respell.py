"""Tests for tools/be_respell.py. Run from the project root: python -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from belarusian_verse.respell import respell, syllables  # noqa: E402

LINES = [
    "Дождж ціхенька стукае ў шкло,",
    "У хаце цёпла і светла.",
    "Мы п’ём гарбату ўдваіх",
    "І дзякуем за кожны дзень.",
    "Ён сказаў: «Еду ў поле».",
]


class UkrainianTests(unittest.TestCase):
    def test_letters(self):
        self.assertEqual(respell("мы", "uk"), "ми")
        self.assertEqual(respell("гэта", "uk"), "гета")
        self.assertEqual(respell("праўда", "uk"), "правда")

    def test_e_is_iotated_at_word_start_and_after_vowel(self):
        self.assertEqual(respell("еду стукае", "uk"), "єду стукає")
        self.assertEqual(respell("светла", "uk"), "светла")

    def test_yo(self):
        self.assertEqual(respell("Ён цёпла", "uk"), "Йон цьопла")
        self.assertEqual(respell("п’ём", "uk"), "п'йом")

    def test_i_after_vowel_becomes_yi(self):
        self.assertEqual(respell("удваіх", "uk"), "удваїх")
        self.assertEqual(respell("ціха", "uk"), "ціха")

    def test_word_start_after_space_and_punctuation(self):
        self.assertEqual(respell("«еду» (ёсць)", "uk"), "«єду» (йосць)")


class RussianTests(unittest.TestCase):
    def test_letters(self):
        self.assertEqual(respell("ціха ўдваіх", "ru"), "циха вдваих")
        self.assertEqual(respell("п’ём п'ём", "ru"), "пъём пъём")

    def test_russian_keeps_e_yo_y(self):
        self.assertEqual(respell("мы ёсць гэта", "ru"), "мы ёсць гэта")


class CommonTests(unittest.TestCase):
    def test_syllable_count_never_changes(self):
        for target in ("uk", "ru"):
            for line in LINES:
                with self.subTest(target=target, line=line):
                    self.assertEqual(syllables(respell(line, target)), syllables(line))

    def test_capitals_and_non_letters_kept(self):
        self.assertEqual(respell("[Куплет]\nІ Ёсць!", "uk"), "[Куплет]\nІ Йосць!")
        self.assertEqual(respell("[Куплет]\nІ Ёсць!", "ru"), "[Куплет]\nИ Ёсць!")

    def test_leading_apostrophe_is_not_a_letter(self):
        self.assertEqual(respell("'ён'", "ru"), "'ён'")


if __name__ == "__main__":
    unittest.main()
