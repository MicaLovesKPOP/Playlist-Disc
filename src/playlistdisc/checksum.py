"""Damm check digit implementation used by PDv1 draft identifiers."""

# Standard Damm quasigroup table.
_DAMM_TABLE: tuple[tuple[int, ...], ...] = (
    (0, 3, 1, 7, 5, 9, 8, 6, 4, 2),
    (7, 0, 9, 2, 1, 5, 4, 8, 6, 3),
    (4, 2, 0, 6, 8, 7, 1, 3, 5, 9),
    (1, 7, 5, 0, 9, 8, 3, 4, 2, 6),
    (6, 1, 2, 3, 0, 4, 5, 9, 7, 8),
    (3, 6, 7, 4, 2, 0, 9, 5, 8, 1),
    (5, 8, 6, 9, 7, 2, 0, 1, 3, 4),
    (8, 9, 4, 5, 3, 6, 2, 0, 1, 7),
    (9, 4, 3, 8, 6, 1, 7, 2, 0, 5),
    (2, 5, 8, 1, 4, 3, 6, 7, 9, 0),
)


def _validate_digits(value: str) -> None:
    if not value or not value.isascii() or not value.isdigit():
        raise ValueError("Damm input must be a non-empty ASCII decimal string")


def damm_digit(value: str) -> int:
    """Return the Damm check digit for *value*."""
    _validate_digits(value)
    interim = 0
    for char in value:
        interim = _DAMM_TABLE[interim][ord(char) - ord("0")]
    return interim


def damm_validate(value_with_check: str) -> bool:
    """Return True when a decimal string including its Damm digit validates."""
    _validate_digits(value_with_check)
    interim = 0
    for char in value_with_check:
        interim = _DAMM_TABLE[interim][ord(char) - ord("0")]
    return interim == 0
