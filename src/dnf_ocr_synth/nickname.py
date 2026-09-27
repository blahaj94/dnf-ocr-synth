"""CP949 nickname policy and UI scale model referenced from dfragon."""

import math
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    """Describe format validity and the measurable byte length."""

    is_valid: bool
    reason: str | None = None
    byte_length: int | None = None


def validate_nickname(
    text: str, *, banned_words: Iterable[str] = ()
) -> ValidationResult:
    """Check the local 12-byte policy while preserving the label.

    This does not check name availability or the game's server policy.
    Banned words are caller-owned, case-insensitive substring rules.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text or text.isspace():
        return ValidationResult(False, "A nickname is required.")
    if any(character.isspace() for character in text):
        return ValidationResult(False, "Whitespace is not allowed.")
    # Only U+00AD and U+3164 are CP949 default-ignorable characters.
    if any(
        unicodedata.category(character) in {"Cc", "Cf"}
        or character == "\u3164"
        for character in text
    ):
        return ValidationResult(False, "Invisible characters are not allowed.")
    try:
        encoded = text.encode("cp949", errors="strict")
    except UnicodeEncodeError:
        return ValidationResult(False, "The nickname must be CP949 encodable.")
    if encoded.decode("cp949") != text:
        return ValidationResult(
            False, "The nickname must round-trip in CP949."
        )
    length = len(encoded)
    if length > 12:
        return ValidationResult(
            False, f"Nickname is {length}B; maximum 12B.", length
        )
    lowered = text.lower()
    if any(word and word.lower() in lowered for word in banned_words):
        return ValidationResult(
            False, "A caller-banned word is present.", length
        )
    return ValidationResult(True, byte_length=length)


def estimate_ui_scale(ui_percent: float, client_height: int = 1080) -> float:
    """Estimate raster scaling using dfragon's empirical 600px model."""
    if (
        isinstance(ui_percent, bool)
        or not math.isfinite(ui_percent)
        or not 0 <= ui_percent <= 100
    ):
        raise ValueError("UI percent must be finite and between 0 and 100.")
    if (
        isinstance(client_height, bool)
        or not isinstance(client_height, int)
        or not 600 <= client_height <= 1080
    ):
        raise ValueError("Client height must be an integer from 600 to 1080.")
    return client_height / (
        client_height - (client_height - 600) * ui_percent / 100
    )
