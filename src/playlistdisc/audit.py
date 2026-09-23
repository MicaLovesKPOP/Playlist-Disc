"""Software-only exhaustive validation of the PDv1 identity/TOC mapping."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib

from .identity import MAX_ID, PDIdentity, decode_track_durations

GOLDEN_VECTOR_SHA256 = "5048cb0d893e1949573c28ea10ef480bd9dd81bfdda0fdd3afc95e1c1825f618"


@dataclass(frozen=True, slots=True)
class EncodingAuditReport:
    identities_checked: int
    namespace_counts: dict[str, int]
    vector_sha256: str
    minimum_total_seconds: int
    minimum_total_id: str
    maximum_total_seconds: int
    maximum_total_id: str


def audit_encoding() -> EncodingAuditReport:
    """Exhaustively round-trip every six-digit PDv1 identity.

    The audit intentionally covers 000000 too: it is invalid for allocation but still
    has a deterministic physical representation and must not collide with anything else.
    """
    digest = hashlib.sha256()
    namespaces: Counter[str] = Counter()
    minimum_total: int | None = None
    minimum_id = ""
    maximum_total: int | None = None
    maximum_id = ""

    for number in range(MAX_ID + 1):
        identity = PDIdentity(number)
        durations = identity.track_durations

        if decode_track_durations(durations) != identity:
            raise AssertionError(f"TOC round-trip failed for {identity.canonical}")
        if PDIdentity.parse(identity.machine_id) != identity:
            raise AssertionError(f"machine-ID round-trip failed for {identity.canonical}")

        namespaces[identity.namespace] += 1
        total = identity.total_seconds
        if minimum_total is None or total < minimum_total:
            minimum_total = total
            minimum_id = identity.id6
        if maximum_total is None or total > maximum_total:
            maximum_total = total
            maximum_id = identity.id6

        vector = (
            f"{identity.id6}|{identity.check_digit}|"
            f"{','.join(str(value) for value in durations)}\n"
        )
        digest.update(vector.encode("ascii"))

    assert minimum_total is not None and maximum_total is not None
    return EncodingAuditReport(
        identities_checked=MAX_ID + 1,
        namespace_counts=dict(sorted(namespaces.items())),
        vector_sha256=digest.hexdigest(),
        minimum_total_seconds=minimum_total,
        minimum_total_id=minimum_id,
        maximum_total_seconds=maximum_total,
        maximum_total_id=maximum_id,
    )


def assert_reference_audit(report: EncodingAuditReport) -> None:
    """Fail if the current encoder no longer matches the Draft 0.2 golden mapping."""
    expected_namespaces = {
        "invalid": 1,
        "private": 90_000,
        "public": 899_999,
        "reserved": 9_900,
        "test": 100,
    }
    if report.identities_checked != 1_000_000:
        raise AssertionError("audit did not cover all six-digit identities")
    if report.namespace_counts != expected_namespaces:
        raise AssertionError(
            f"namespace partition changed: {report.namespace_counts!r}"
        )
    if report.vector_sha256 != GOLDEN_VECTOR_SHA256:
        raise AssertionError(
            "physical encoding changed: "
            f"{report.vector_sha256} != {GOLDEN_VECTOR_SHA256}"
        )
    if (
        report.minimum_total_seconds,
        report.minimum_total_id,
        report.maximum_total_seconds,
        report.maximum_total_id,
    ) != (97, "010000", 341, "999899"):
        raise AssertionError(
            "valid-ID duration extrema changed: "
            f"{report.minimum_total_seconds}s/{report.minimum_total_id} .. "
            f"{report.maximum_total_seconds}s/{report.maximum_total_id}"
        )
