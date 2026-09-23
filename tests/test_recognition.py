from pathlib import Path

from playlistdisc.beacon import write_beacon_wav
from playlistdisc.identity import PDIdentity
from playlistdisc.recognition import (
    recognize_observations,
    validate_recognition_result,
)


def test_each_strong_channel_can_recognize_independently(tmp_path: Path):
    identity = PDIdentity(999901)

    toc = recognize_observations(track_durations=identity.track_durations)
    assert toc.status == "recognized"
    assert toc.identity == identity
    assert [item.channel for item in toc.evidence] == ["toc"]

    text = recognize_observations(cdtext_values=[f"hello {identity.machine_id} world"])
    assert text.status == "recognized"
    assert text.identity == identity

    wav = write_beacon_wav(identity, tmp_path / "beacon.wav")
    beacon = recognize_observations(beacon_wav=wav)
    assert beacon.status == "recognized"
    assert beacon.identity == identity


def test_matching_channels_strengthen_same_identity(tmp_path: Path):
    identity = PDIdentity(999902)
    wav = write_beacon_wav(identity, tmp_path / "beacon.wav")
    result = recognize_observations(
        track_durations=identity.track_durations,
        cdtext_values=[identity.machine_id],
        beacon_wav=wav,
    )
    assert result.status == "recognized"
    assert result.identity == identity
    assert {item.channel for item in result.evidence} == {
        "toc",
        "cdtext",
        "audio_beacon",
    }
    assert validate_recognition_result(result.to_dict()) == []


def test_two_valid_disagreeing_channels_fail_open():
    first = PDIdentity(999901)
    second = PDIdentity(999902)
    result = recognize_observations(
        track_durations=first.track_durations,
        cdtext_values=[second.machine_id],
    )
    assert result.status == "conflict"
    assert result.identity is None
    assert len(result.evidence) == 2


def test_bad_optional_channel_does_not_hide_valid_toc():
    identity = PDIdentity(999901)
    result = recognize_observations(
        track_durations=identity.track_durations,
        cdtext_values=["ordinary CD text", "PD1-999901-0"],
    )
    assert result.status == "recognized"
    assert result.identity == identity
    assert any("no PDv1 machine ID" in error for error in result.errors)
    assert any("check digit" in error for error in result.errors)


def test_rounded_toc_can_be_recognized_only_with_explicit_tolerance():
    identity = PDIdentity(123456)
    observed = [
        value + (0.7 if index % 2 else -0.6)
        for index, value in enumerate(identity.track_durations)
    ]

    strict = recognize_observations(track_durations=observed)
    assert strict.status == "unknown"

    tolerant = recognize_observations(
        track_durations=observed,
        toc_tolerance=1.0,
    )
    assert tolerant.status == "recognized"
    assert tolerant.identity == identity


def test_partial_or_coarse_toc_is_not_strong_evidence():
    result = recognize_observations(track_durations=[9, 16])
    assert result.status == "unknown"
    assert result.identity is None
    assert any("exactly 8 tracks" in error for error in result.errors)


def test_no_evidence_is_unknown():
    result = recognize_observations()
    assert result.status == "unknown"
    assert result.evidence == ()
    assert validate_recognition_result(result.to_dict()) == []
