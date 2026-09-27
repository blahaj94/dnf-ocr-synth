"""Render glyphs, then outline and scale complete nickname rasters."""

import json
import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, features
from PIL.PngImagePlugin import PngInfo

from .fonts import FontPaths, _Face, _load_face
from .nickname import validate_nickname

COLOR = (75, 209, 255)


@dataclass
class Sample:
    """Keep the RGBA result, native ink mask, and rendering metadata."""

    image: Image.Image
    native_mask: Image.Image
    metadata: dict

    def save(self, path: str | Path) -> None:
        """Save a PNG with UTF-8 JSON metadata under 'dnf_ocr_synth'."""
        info = PngInfo()
        info.add_itxt(
            "dnf_ocr_synth", json.dumps(self.metadata, ensure_ascii=False)
        )
        self.image.save(path, format="PNG", pnginfo=info)


def _raster(text: str, face: _Face) -> tuple[Image.Image, tuple[int, int]]:
    left, top, right, bottom = face.font.getbbox(text, anchor="ls")
    canvas = Image.new(face.mode, (right - left + 8, bottom - top + 8))
    ImageDraw.Draw(canvas).text(
        (4 - left, 4 - top),
        text,
        font=face.font,
        anchor="ls",
        fill=1 if face.mode == "1" else 255,
    )
    box = canvas.getbbox()
    if box is None:
        raise ValueError(f"Font produced no visible ink for {text!r}.")
    mask = canvas.crop(box).convert("L")
    if face.bold_x:
        expanded = Image.new("L", (mask.width + 1, mask.height))
        shifted = expanded.copy()
        expanded.paste(mask, (0, 0))
        shifted.paste(mask, (1, 0))
        mask = ImageChops.lighter(expanded, shifted)
    return mask, (left + box[0] - 4, top + box[1] - 4)


def _compose(
    masks: list[Image.Image], positions: list[tuple[int, int]]
) -> Image.Image:
    left = min(x for x, _ in positions)
    top = min(y for _, y in positions)
    right = max(x + mask.width for mask, (x, _) in zip(masks, positions))
    bottom = max(y + mask.height for mask, (_, y) in zip(masks, positions))
    canvas = Image.new("L", (right - left, bottom - top))
    for mask, (x, y) in zip(masks, positions):
        layer = Image.new("L", canvas.size)
        layer.paste(mask, (x - left, y - top))
        canvas = ImageChops.lighter(canvas, layer)
    return canvas


def _colorize(mask: Image.Image, scale: float) -> Image.Image:
    # Padding holds the 1px square outline and a transparent margin.
    ink = Image.new("L", (mask.width + 4, mask.height + 4))
    ink.paste(mask, (2, 2))
    alpha = ink.filter(ImageFilter.MaxFilter(3))
    # Premultiply cyan ink by its coverage within the black outline.
    channels = [
        ink.point([round(i * c / 255) for i in range(256)]) for c in COLOR
    ]
    image = Image.merge("RGBa", (*channels, alpha))
    if scale != 1:
        size = (
            math.ceil(image.width * scale),
            math.ceil(image.height * scale),
        )
        # Ceil adds room without changing the isotropic scale.
        image = image.transform(
            size,
            Image.Transform.AFFINE,
            (1 / scale, 0, 0, 0, 1 / scale, 0),
            resample=Image.Resampling.BILINEAR,
        )
    return image.convert("RGBA")


class Renderer:
    """Reuse loaded local fonts across nickname samples.

    Glyphs use font advances and a shared baseline. Their placement
    has not been verified against the game for arbitrary nicknames.
    """

    def __init__(self, fonts: FontPaths) -> None:
        """Retain paths and lazily cache selected font faces."""
        self.fonts = fonts
        self._faces: dict[str, _Face] = {}

    def _load(self, name: str) -> _Face:
        if name not in self._faces:
            self._faces[name] = _load_face(self.fonts, name)
        return self._faces[name]

    def _select(self, character: str, profile: str) -> str:
        primary = "dotum" if profile == "dotum" else "nanum"
        choices = [primary] if profile == "dotum" else [primary, "gungsuh"]
        for name in choices:
            if ord(character) in self._load(name).coverage:
                return name
        raise ValueError(
            f"No glyph for U+{ord(character):04X} in profile {profile}."
        )

    def render(
        self,
        text: str,
        *,
        profile: str = "dotum",
        layout: str = "metrics",
        scale: float = 1.0,
    ) -> Sample:
        """Render a valid nickname as cyan ink with a 1px black outline.

        Scale in (0, 16] applies after rasterization. Missing glyphs
        raise ValueError. The label is never normalized, trimmed, or
        changed through character replacement.
        """
        validation = validate_nickname(text)
        if not validation.is_valid:
            raise ValueError(validation.reason)
        if profile not in {"dotum", "nanum-neo"}:
            raise ValueError("profile must be 'dotum' or 'nanum-neo'.")
        if layout != "metrics":
            raise ValueError("layout must be 'metrics'.")
        if (
            isinstance(scale, bool)
            or not math.isfinite(scale)
            or not 0 < scale <= 16
        ):
            raise ValueError("scale must be finite and in (0, 16].")
        names = [self._select(character, profile) for character in text]
        masks = []
        positions = []
        cursor = 0
        for character, name in zip(text, names):
            face = self._load(name)
            glyph, (x, y) = _raster(character, face)
            masks.append(glyph)
            positions.append((cursor + x, y))
            cursor += round(face.font.getlength(character)) + face.bold_x
        mask = _compose(masks, positions)
        image = _colorize(mask, scale)
        primary = "dotum" if profile == "dotum" else "nanum"
        inspected_fonts = dict.fromkeys([primary, *names])
        metadata = {
            "schema_version": 1,
            "renderer_version": "0.1.0",
            "text": text,
            "codepoints": [f"U+{ord(character):04X}" for character in text],
            "cp949_bytes": validation.byte_length,
            "profile": profile,
            "layout": layout,
            "scale": scale,
            "foreground_rgb": list(COLOR),
            "outline_rgb": [0, 0, 0],
            "outline_px": 1,
            "padding_px": 2,
            "native_ink_size": list(mask.size),
            "image_size": list(image.size),
            "resampling": "bilinear-premultiplied",
            "layout_engine": "Pillow BASIC",
            "pillow_version": Image.__version__,
            "freetype_version": features.version_module("freetype2"),
            "fonts": [
                dict(self._load(name).metadata) for name in inspected_fonts
            ],
            "glyphs": [
                {"character": character, "font": name}
                for character, name in zip(text, names)
            ],
        }
        return Sample(image, mask, metadata)
