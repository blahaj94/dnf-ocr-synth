"""Load font files from explicit local paths."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from fontTools.ttLib import TTFont, TTLibError
from PIL import ImageFont


@dataclass(frozen=True)
class FontPaths:
    """Supply paths for the fonts needed by each render."""

    gulim: Path | None = None
    batang: Path | None = None
    nanum: Path | None = None
    uttum: Path | None = None


@dataclass
class _Face:
    font: ImageFont.FreeTypeFont
    coverage: frozenset[int]
    mode: str
    bold_x: int
    metadata: dict


def _load_face(paths: FontPaths, name: str) -> _Face:
    settings = {
        "dotum": (paths.gulim, "gulim", 2, 11, "1", 0),
        "dotumche": (paths.gulim, "gulim", 3, 11, "1", 0),
        "uttum": (paths.uttum, "uttum", 0, 12, "1", 0),
        "gungsuh": (paths.batang, "batang", 2, 12, "1", 1),
        "hanja": (paths.batang, "batang", 2, 12, "1", 0),
        "nanum": (paths.nanum, "nanum", 0, 11, "L", 0),
    }
    location, option, index, size, mode, bold_x = settings[name]
    if location is None:
        raise ValueError(f"Supply the local {option} font path.")
    path = Path(location)
    if not path.is_file():
        raise FileNotFoundError(f"Font file not found: {path}")
    try:
        with (
            path.open("rb") as stream,
            TTFont(stream, fontNumber=index, lazy=True) as table,
        ):
            coverage = frozenset((table.getBestCmap() or {}).keys())
    except TTLibError as error:
        raise ValueError(
            f"Cannot read {option} font face {index}: {error}"
        ) from error
    font = ImageFont.truetype(
        str(path.resolve()),
        size,
        index=index,
        layout_engine=ImageFont.Layout.BASIC,
    )
    return _Face(
        font,
        coverage,
        mode,
        bold_x,
        {
            "id": name,
            "file": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "family": list(font.getname()),
            "face_index": index,
            "size_px": size,
            "raster_mode": mode,
            "bold_x": bold_x,
        },
    )
