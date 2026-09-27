import unittest

from dnf_ocr_synth import estimate_ui_scale, validate_nickname


class NicknameTests(unittest.TestCase):
    def test_cp949_boundaries_and_original_characters(self):
        cases = {
            "ァÐぎ★": 8,
            "★검신★": 8,
            "가나다라마바": 12,
            "Ab0123456789": 12,
            "가나다라마12": 12,
            "アラド": 6,
            "ㄱ검신": 6,
            "검신♡": 6,
            "A$": 2,
            "아라드郞": 8,
        }
        for text, length in cases.items():
            with self.subTest(text=text):
                result = validate_nickname(text)
                self.assertTrue(result.is_valid, result.reason)
                self.assertEqual(result.byte_length, length)

    def test_rejects_unusable_labels_without_normalizing(self):
        for text in (
            "",
            " ",
            "검 신",
            "검신\n",
            "검\t신",
            "검\u00a0신",
            "검\u3000신",
            "검\x05신",
            "검\x00신",
            "검\x7f신",
            "검\u200b신",
            "검\u200d신",
            "검\u3164신",
            "검\u00ad신",
            "\ud800",
            "\udc00",
            "가",
            "사쿠라🌸",
            "검신🫠",
            "검신🇰🇷",
            "검신1️⃣",
            "검신♥️",
            "𠀀",
            "龥",
            "검신〆",
            "아라드郎",
            "가나다라마바A",
            "Ab01234567890",
            "가나다라마바사",
        ):
            with self.subTest(text=repr(text)):
                self.assertFalse(validate_nickname(text).is_valid)

    def test_banned_words_are_caller_policy(self):
        self.assertTrue(validate_nickname("운영자").is_valid)
        self.assertTrue(validate_nickname("검신", banned_words=[""]).is_valid)
        self.assertFalse(
            validate_nickname("MyGM", banned_words=["gm"]).is_valid
        )

    def test_length_failure_retains_measured_bytes(self):
        self.assertEqual(validate_nickname("가나다라마바A").byte_length, 13)

    def test_ui_scale_model(self):
        self.assertEqual(estimate_ui_scale(0), 1)
        self.assertEqual(estimate_ui_scale(100), 1.8)
        self.assertEqual(estimate_ui_scale(50, 900), 1.2)
        self.assertEqual(estimate_ui_scale(100, 600), 1)
        for percent, height in (
            (-1, 1080),
            (101, 1080),
            (float("nan"), 1080),
            (float("inf"), 1080),
            (50, 599),
            (50, 1081),
            (50, 900.5),
        ):
            with self.subTest(percent=percent, height=height):
                with self.assertRaises(ValueError):
                    estimate_ui_scale(percent, height)
