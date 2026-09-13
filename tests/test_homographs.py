"""Homograph stress: BelVoice's most frequent stress first, and a silent fallback when it is missing."""
import os
import tempfile
import unittest
from unittest import mock
from urllib.error import URLError

from belarusian_verse import data
from belarusian_verse.stress import (ACUTE, frequent_first, load_homographs, load_lexicon,  # noqa: E402
                                     mark_word, stress_index)
from belarusian_verse.stress_benchmark import download, marked_tokens, score  # noqa: E402


class IndexTests(unittest.TestCase):
    def test_the_acute_or_plus_follows_the_stressed_vowel(self):
        self.assertEqual(stress_index("вада" + ACUTE), 2)
        self.assertEqual(stress_index("ба+цькі"), 1)
        self.assertIsNone(stress_index("вада"))


class OrderTests(unittest.TestCase):
    def test_the_frequent_stress_moves_to_the_front(self):
        lexicon = frequent_first({"вада": (1, 2)}, {"вада": "вада" + ACUTE})
        self.assertEqual(lexicon["вада"], (2, 1))

    def test_a_stress_grammardb_does_not_list_is_ignored(self):
        lexicon = frequent_first({"вада": (1, 2)}, {"вада": "вадаа" + ACUTE})  # a stress on a third vowel
        self.assertEqual(lexicon["вада"], (1, 2))

    def test_a_word_with_one_stress_is_left_alone(self):
        self.assertEqual(frequent_first({"вада": (1,)}, {"вада": "вада" + ACUTE})["вада"], (1,))

    def test_a_capitalised_name_does_not_decide_the_common_word(self):
        table = {"мая": "мая" + ACUTE, "Мая": "Ма" + ACUTE + "я"}
        self.assertEqual(frequent_first({"мая": (1, 2)}, table)["мая"], (2, 1))


class OfflineTests(unittest.TestCase):
    """No network here: every download is refused or faked."""

    def test_an_unreachable_table_means_grammardb_order(self):
        with mock.patch("belarusian_verse.stress.table", side_effect=URLError("offline")):
            self.assertEqual(load_homographs(), {})

    def test_a_failed_download_leaves_nothing_in_the_cache(self):
        with tempfile.TemporaryDirectory() as cache, \
                mock.patch.object(data, "LOCAL_DIR", None), \
                mock.patch.object(data, "_cache_dir", return_value=cache), \
                mock.patch("urllib.request.urlopen", side_effect=URLError("offline")):
            with self.assertRaises(OSError):
                data.table("homographs")
            self.assertEqual(os.listdir(cache), [])

    def test_a_download_that_does_not_match_its_checksum_is_refused(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'{"vada": "vada"}'
        with tempfile.TemporaryDirectory() as cache, \
                mock.patch.object(data, "LOCAL_DIR", None), \
                mock.patch.object(data, "_cache_dir", return_value=cache), \
                mock.patch("urllib.request.urlopen", return_value=response):
            with self.assertRaises(ValueError):
                data.table("homographs")
            self.assertEqual(os.listdir(cache), [])


class SongWordTests(unittest.TestCase):
    """Homographs from real songs that GrammarDB's first listed variant got wrong (2026-09-13)."""

    @classmethod
    def setUpClass(cls):
        if not load_homographs():
            raise unittest.SkipTest("BelVoice's stress table could not be downloaded")
        cls.lex = load_lexicon()

    def assertStressed(self, word, expected):
        self.assertEqual(mark_word(word, self.lex, pick_first=True)[0], expected)

    def test_vada(self):
        self.assertStressed("вада", "вада" + ACUTE)

    def test_byli(self):
        self.assertStressed("былі", "былі" + ACUTE)

    def test_raki(self):
        self.assertStressed("ракі", "ракі" + ACUTE)

    def test_niby(self):
        self.assertStressed("нібы", "нібы" + ACUTE)


class BenchmarkTests(unittest.TestCase):
    """Floors just under what was measured, so a regression fails the suite."""

    @classmethod
    def setUpClass(cls):
        if not load_homographs():
            raise unittest.SkipTest("BelVoice's stress table could not be downloaded")
        try:
            files = download()
        except Exception as exc:  # the benchmark is a second dataset; do not fail on its absence
            raise unittest.SkipTest(f"benchmark could not be downloaded: {exc}")
        cls.lex = load_lexicon()
        cls.common_voice = marked_tokens(files["common_voice"])
        cls.literary = marked_tokens(files["literary"])

    def rate(self, tokens, lexicon):
        right, total = score(tokens, lexicon)
        self.assertGreater(total, 1000)
        return right / total

    def test_common_voice_sentences(self):
        self.assertGreaterEqual(self.rate(self.common_voice, self.lex), 0.82)

    def test_literary_text(self):
        self.assertGreaterEqual(self.rate(self.literary, self.lex), 0.68)

    def test_grammardb_order_alone_was_a_coin_toss(self):
        self.assertLess(self.rate(self.common_voice, load_lexicon(homographs="")), 0.55)


if __name__ == "__main__":
    unittest.main()
