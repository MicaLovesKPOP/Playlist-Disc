"""PDv1 draft identity and table-of-contents encoding."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Iterable

from .checksum import damm_digit, damm_validate

FORMAT_VERSION = 1
TRACK_COUNT = 8
IDENT_TRACK_SECONDS = 9
DIGIT_BASE_SECONDS = 12
DIGIT_STEP_SECONDS = 4
MAX_ID = 999_999

PUBLIC_MIN = 1
PUBLIC_MAX = 899_999
PRIVATE_MIN = 900_000
PRIVATE_MAX = 989_999
RESERVED_MIN = 990_000
RESERVED_MAX = 999_899
TEST_MIN = 999_900
TEST_MAX = 999_999


@dataclass(frozen=True, slots=True)
class PDIdentity:
    """A Playlist Disc draft-v1 identifier."""

    number: int
    version: int = FORMAT_VERSION

    def __post_init__(self) -> None:
        if self.version != FORMAT_VERSION:
            raise ValueError(f"only PDv{FORMAT_VERSION} is implemented")
        if not 0 <= self.number <= MAX_ID:
            raise ValueError("PDv1 number must be between 000000 and 999999")

    @classmethod
    def parse(cls, value: int | str) -> "PDIdentity":
        if isinstance(value, int):
            return cls(value)
        text = value.strip().upper()
        if text.startswith("PD1-"):
            text = text[4:]
            if "-" in text:
                disc, supplied = text.split("-", 1)
                ident = cls(int(disc))
                if supplied != str(ident.check_digit):
                    raise ValueError("identifier check digit does not validate")
                return ident
        if not text.isascii() or not text.isdigit() or len(text) > 6:
            raise ValueError("expected a 1-6 digit ID or PD1-123456[-C]")
        return cls(int(text))

    @property
    def id6(self) -> str:
        return f"{self.number:06d}"

    @property
    def check_digit(self) -> int:
        return damm_digit(f"{self.version}{self.id6}")

    @property
    def canonical(self) -> str:
        return f"PD{self.version}-{self.id6}"

    @property
    def machine_id(self) -> str:
        return f"{self.canonical}-{self.check_digit}"

    @property
    def namespace(self) -> str:
        if self.number == 0:
            return "invalid"
        if PUBLIC_MIN <= self.number <= PUBLIC_MAX:
            return "public"
        if PRIVATE_MIN <= self.number <= PRIVATE_MAX:
            return "private"
        if RESERVED_MIN <= self.number <= RESERVED_MAX:
            return "reserved"
        if TEST_MIN <= self.number <= TEST_MAX:
            return "test"
        raise AssertionError("namespace ranges are incomplete")

    @property
    def track_durations(self) -> tuple[int, ...]:
        digits = [int(ch) for ch in self.id6]
        digits.append(self.check_digit)
        return (IDENT_TRACK_SECONDS,) + tuple(
            DIGIT_BASE_SECONDS + DIGIT_STEP_SECONDS * digit for digit in digits
        )

    @property
    def total_seconds(self) -> int:
        return sum(self.track_durations)

    @property
    def toc_signature(self) -> str:
        payload = "PDV1|" + ",".join(str(x) for x in self.track_durations)
        return hashlib.sha256(payload.encode("ascii")).hexdigest()

    @property
    def beacon_symbols(self) -> str:
        # '*' and '#' are framing symbols. Version + six digits + Damm digit is payload.
        return f"*{self.version}{self.id6}{self.check_digit}#"


def _nearest_digit(seconds: float, tolerance: float) -> int:
    raw = (seconds - DIGIT_BASE_SECONDS) / DIGIT_STEP_SECONDS
    digit = round(raw)
    if not 0 <= digit <= 9:
        raise ValueError(f"duration {seconds:g}s is outside the PDv1 digit bands")
    expected = DIGIT_BASE_SECONDS + DIGIT_STEP_SECONDS * digit
    if abs(seconds - expected) > tolerance:
        raise ValueError(
            f"duration {seconds:g}s is {abs(seconds - expected):.3g}s from nearest PDv1 value"
        )
    return int(digit)


def decode_track_durations(
    durations: Iterable[float], *, tolerance: float = 0.0
) -> PDIdentity:
    """Decode eight reported track durations into a PDv1 identity.

    ``tolerance`` is in seconds. A value below half the four-second digit spacing is
    intentionally required so adjacent digits can never both match.
    """
    if tolerance < 0 or tolerance >= DIGIT_STEP_SECONDS / 2:
        raise ValueError("tolerance must be >= 0 and < 2 seconds")
    values = tuple(float(x) for x in durations)
    if len(values) != TRACK_COUNT:
        raise ValueError(f"PDv1 requires exactly {TRACK_COUNT} tracks")
    if abs(values[0] - IDENT_TRACK_SECONDS) > tolerance:
        raise ValueError("track 1 does not contain the PDv1 9-second marker")

    digits = [_nearest_digit(value, tolerance) for value in values[1:]]
    id_digits = "".join(str(x) for x in digits[:6])
    check = digits[6]
    if not damm_validate(f"{FORMAT_VERSION}{id_digits}{check}"):
        raise ValueError("TOC digits fail the PDv1 Damm checksum")
    return PDIdentity(int(id_digits))
