import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from dnf_ocr_synth import FontPaths, Renderer

GULIM = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/gulim.ttc"
UTTUM = os.environ.get("DNF_SYNTH_UTTUM")


@unittest.skipUnless(GULIM.is_file(), "Local Windows font unavailable")
class AsciiTests(unittest.TestCase):
    def test_digits_and_capital_o_match_game_without_uttum(self):
        sample = Renderer(FontPaths(gulim=GULIM)).render("1O456")
        self.assertEqual(sample.image.size, (32, 12))
        self.assertEqual(
            hashlib.sha256(sample.image.tobytes()).hexdigest(),
            "102097b95c9d6a5c2da8e20a3bfe3cc0cb5781aff9bb1009287bd6630bb8f720",
        )
        self.assertEqual(
            [font["id"] for font in sample.metadata["fonts"]],
            ["dotumche"],
        )
        self.assertEqual(sample.metadata["fonts"][0]["face_index"], 3)

    def test_capital_i_requires_an_explicit_uttum_path(self):
        with self.assertRaisesRegex(ValueError, "uttum"):
            Renderer(FontPaths(gulim=GULIM)).render("I")


@unittest.skipUnless(
    GULIM.is_file() and UTTUM and Path(UTTUM).is_file(),
    "Set DNF_SYNTH_UTTUM and supply the local Windows font",
)
class UttumTests(unittest.TestCase):
    def test_unscaled_ascii_nicknames_match_game_pixels(self):
        # Extracted from the 1920x1080, UI 0% game screenshots.
        # Keep cyan text and black outline; remove the game background.
        expected = {
            "MWmwgjI1O456": (
                (69, 14),
                "5d1ba47bc3d962dd2cfa82f1547fc360"
                "388892c8645f4c4dfe09c525b2e46a1f",
            ),
            "Il1O0I123789": (
                (65, 12),
                "5da61f160533f4f879fd061722acb0370"
                "f068c0f9a144494b25f9b6ea606d4d0",
            ),
            "IlIlIIllIlIl": (
                (39, 12),
                "e9be276a05d5a13c79d5ceb86feb5d33"
                "aa4d2edc1f83a5c7e2069d2c7c566748",
            ),
        }
        renderer = Renderer(FontPaths(gulim=GULIM, uttum=Path(UTTUM)))
        for text, (size, digest) in expected.items():
            with self.subTest(text=text):
                sample = renderer.render(text)
                self.assertEqual(sample.metadata["text"], text)
                self.assertEqual(sample.image.size, size)
                self.assertEqual(
                    hashlib.sha256(sample.image.tobytes()).hexdigest(),
                    digest,
                )

    def test_capital_i_alone_does_not_load_other_fonts(self):
        sample = Renderer(FontPaths(uttum=Path(UTTUM))).render("I")
        self.assertEqual(sample.native_mask.size, (3, 8))
        self.assertEqual(
            [font["id"] for font in sample.metadata["fonts"]], ["uttum"]
        )

    def test_cli_passes_uttum_path_to_the_renderer(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.png"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "dnf_ocr_synth",
                    "MWmwgjI1O456",
                    "--gulim",
                    str(GULIM),
                    "--uttum",
                    UTTUM,
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
                self.assertEqual(metadata["native_ink_size"], [65, 10])
                self.assertEqual(
                    {font["id"] for font in metadata["fonts"]},
                    {"dotumche", "uttum"},
                )
