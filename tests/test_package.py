"""The public API, against the real published tables (downloaded on first run)."""
import unittest

from belarusian_verse import (analyse_verse, check_agreement, check_spelling, mark_stress,
                              respell, rhyme)


class PublicApiTests(unittest.TestCase):
    def test_mark_stress(self):
        self.assertEqual(mark_stress("побач"), "по́бач")
        self.assertEqual(mark_stress("Побач ты, і добра мне"), "По́бач ты, і до́бра мне")

    def test_rhyme_grades(self):
        self.assertEqual(rhyme("вадзе", "ідзе"), ("rich", 1.0))
        self.assertEqual(rhyme("маёй", "спакой")[0], "exact")
        self.assertEqual(rhyme("ідзе", "знайдзе")[0], "none")

    def test_agreement(self):
        self.assertEqual(check_agreement("тваіх вачам")["errors"], 1)
        self.assertEqual(check_agreement("тваім вачам")["errors"], 0)

    def test_spelling_finds_a_foreign_letter(self):
        codes = {i["code"] for line in check_spelling("Вечар тихі")["lines"] for i in line["issues"]}
        self.assertIn("BAD_CHAR", codes)

    def test_verse_analysis(self):
        verse = ("Белы туман па лесе плыве,\nСвежасць ранішняя тут жыве.\n"
                 "Сосны стаяць у цішы маёй,\nСэрца знайшло тут свой спакой.")
        result = analyse_verse(verse, "AABB")
        self.assertGreaterEqual(result["rhyme_score"], 0.9)

    def test_respell_keeps_the_syllable_count(self):
        line = "Мы п’ём гарбату ўдваіх"
        for target in ("uk", "ru"):
            self.assertEqual(sum(c in "аеёіоуыэюяиєї" for c in respell(line, target).lower()),
                             sum(c in "аеёіоуыэюя" for c in line.lower()))


if __name__ == "__main__":
    unittest.main()
