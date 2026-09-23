import pytest

from playlistdisc.identity import PDIdentity, decode_track_durations


def test_known_identity():
    ident = PDIdentity(123456)
    assert ident.machine_id == "PD1-123456-3"
    assert ident.track_durations == (9, 16, 20, 24, 28, 32, 36, 24)
    assert ident.total_seconds == 189


def test_roundtrip():
    for number in (1, 12437, 123456, 899999, 900000, 989999, 999901, 999999):
        ident = PDIdentity(number)
        assert decode_track_durations(ident.track_durations) == ident


def test_rounded_duration_tolerance():
    ident = PDIdentity(123456)
    observed = [9.2, 15.4, 20.7, 23.2, 28.4, 31.1, 36.5, 24.4]
    assert decode_track_durations(observed, tolerance=1.0) == ident


def test_bad_checksum_is_rejected():
    durations = list(PDIdentity(123456).track_durations)
    durations[-1] = 28
    with pytest.raises(ValueError, match="checksum"):
        decode_track_durations(durations)


def test_namespace():
    assert PDIdentity(1).namespace == "public"
    assert PDIdentity(900000).namespace == "private"
    assert PDIdentity(990000).namespace == "reserved"
    assert PDIdentity(999901).namespace == "test"
