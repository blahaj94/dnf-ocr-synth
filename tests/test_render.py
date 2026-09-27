import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from dnf_ocr_synth import FontPaths, Renderer

WINDOWS_FONTS = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
NANUM = os.environ.get("DNF_SYNTH_NANUM")
FONTS = FontPaths(
    gulim=WINDOWS_FONTS / "gulim.ttc",
    batang=WINDOWS_FONTS / "batang.ttc",
    nanum=Path(NANUM) if NANUM else None,
)
NICKNAME = "ァÐぎ★"


class InputTests(unittest.TestCase):
    def test_invalid_requests_fail_before_loading_fonts(self):
        renderer = Renderer(FontPaths())
        for text, options in (
            ("", {}),
            ("검 신", {}),
            (NICKNAME, {"profile": "missing"}),
            (NICKNAME, {"layout": "missing"}),
            (NICKNAME, {"scale": 0}),
            (NICKNAME, {"scale": 17}),
            (NICKNAME, {"scale": float("nan")}),
        ):
            with self.subTest(text=text, options=options):
                with self.assertRaises(ValueError):
                    renderer.render(text, **options)

    def test_missing_fonts_have_an_actionable_error(self):
        with self.assertRaisesRegex(ValueError, "gulim"):
            Renderer(FontPaths()).render(NICKNAME)

    def test_explicit_path_is_not_a_pillow_font_search(self):
        with self.assertRaises(FileNotFoundError):
            Renderer(FontPaths(gulim=Path("missing/gulim.ttc"))).render(
                NICKNAME
            )

    def test_invalid_font_file_reports_a_value_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.ttc"
            path.write_bytes(b"not a font")
            with self.assertRaisesRegex(ValueError, "gulim font face 2"):
                Renderer(FontPaths(gulim=path)).render(NICKNAME)


@unittest.skipUnless(FONTS.gulim.is_file(), "Local Windows font unavailable")
class DotumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer(FONTS)

    def test_metadata_round_trip_preserves_label_and_has_no_paths(self):
        sample = self.renderer.render(NICKNAME, scale=1.8)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.png"
            sample.save(path)
            with Image.open(path) as image:
                metadata = json.loads(image.info["dnf_ocr_synth"])
                self.assertEqual(image.mode, "RGBA")
                self.assertEqual(metadata, sample.metadata)
                self.assertEqual(metadata["text"], NICKNAME)
                self.assertEqual(metadata["layout"], "metrics")
                self.assertEqual(metadata["image_size"], list(image.size))
                self.assertNotIn("C:", json.dumps(metadata))
                self.assertEqual(image.getpixel((0, 0))[3], 0)

    def test_general_layout_and_missing_coverage(self):
        for text in ("검신", "가나다라마바", "MyGM", NICKNAME):
            sample = self.renderer.render(text)
            self.assertEqual(sample.metadata["text"], text)
            self.assertEqual(sample.metadata["layout"], "metrics")
            self.assertIsNotNone(sample.native_mask.getbbox())
        face = self.renderer._load("dotum")
        original = face.coverage
        try:
            face.coverage = frozenset()
            with self.assertRaisesRegex(ValueError, "U\\+AC80"):
                self.renderer.render("검신")
        finally:
            face.coverage = original

    def test_cli_produces_readable_training_sample(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.png"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "dnf_ocr_synth",
                    NICKNAME,
                    "--gulim",
                    str(FONTS.gulim),
                    "--ui-percent",
                    "100",
                    "--output",
                    str(path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with Image.open(path) as image:
                metadata = json.loads(image.info["dnf_ocr_synth"])
                self.assertEqual(metadata["text"], NICKNAME)
                self.assertEqual(metadata["layout"], "metrics")
                self.assertEqual(metadata["scale"], 1.8)


@unittest.skipUnless(
    FONTS.batang.is_file() and NANUM and Path(NANUM).is_file(),
    "Set DNF_SYNTH_NANUM to run local mixed-font tests",
)
class NanumTests(unittest.TestCase):
    def test_mixed_script_fallback_sources(self):
        sample = Renderer(FONTS).render(NICKNAME, profile="nanum-neo")
        self.assertEqual(
            [entry["font"] for entry in sample.metadata["glyphs"]],
            ["gungsuh", "gungsuh", "gungsuh", "nanum"],
        )
        self.assertEqual(sample.metadata["layout"], "metrics")
        self.assertIsNotNone(sample.native_mask.getbbox())

    def test_metrics_uses_primary_and_fallback(self):
        sample = Renderer(FONTS).render("검신Ð", profile="nanum-neo")
        self.assertEqual(
            [entry["font"] for entry in sample.metadata["glyphs"]],
            ["nanum", "nanum", "gungsuh"],
        )

    def test_metadata_keeps_primary_when_every_glyph_uses_fallback(self):
        sample = Renderer(FONTS).render("Ð", profile="nanum-neo")
        self.assertEqual(sample.metadata["glyphs"][0]["font"], "gungsuh")
        self.assertEqual(
            {font["id"] for font in sample.metadata["fonts"]},
            {"nanum", "gungsuh"},
        )
