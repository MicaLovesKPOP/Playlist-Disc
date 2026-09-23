from pathlib import Path
import wave

import pytest

from playlistdisc.local_scan import (
    extract_tag_identity,
    scan_local_library,
)


class _Audio:
    def __init__(self, tags):
        self.tags = tags


def test_extract_tag_identity_accepts_mb_trackid_and_isrc():
    tags = {
        "MusicBrainz Track Id": ["AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE"],
        "ISRC": ["KR-ABC-26-00001"],
        "title": ["Example Track"],
        "artist": ["Example Artist"],
    }
    data = extract_tag_identity(tags)
    assert data == {
        "musicbrainz_recording_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "isrcs": ["KRABC2600001"],
        "title_hint": "Example Track",
        "artist_hint": "Example Artist",
    }


def test_extract_tag_identity_rejects_multiple_recording_mbids():
    tags = {
        "musicbrainz_trackid": [
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "11111111-2222-3333-4444-555555555555",
        ]
    }
    with pytest.raises(ValueError, match="multiple distinct"):
        extract_tag_identity(tags)


def test_scan_is_deterministic_and_skips_unidentified(tmp_path: Path):
    (tmp_path / "b.flac").write_bytes(b"fake")
    (tmp_path / "a.mp3").write_bytes(b"fake")
    (tmp_path / "untagged.ogg").write_bytes(b"fake")
    (tmp_path / "ignore.txt").write_text("not audio")

    mapping = {
        "a.mp3": _Audio(
            {
                "musicbrainz_recordingid": [
                    "11111111-2222-3333-4444-555555555555"
                ],
                "title": ["A"],
            }
        ),
        "b.flac": _Audio({"isrc": ["KRABC2600002"], "title": ["B"]}),
        "untagged.ogg": _Audio({"title": ["No ID"]}),
    }

    def loader(path: Path):
        return mapping[path.name]

    report = scan_local_library(tmp_path, loader=loader)
    assert report.scanned_files == 3
    assert report.indexed_files == 2
    assert report.unidentified_files == 1
    assert report.unreadable_files == 0
    assert [item["resource"].rsplit("/", 1)[-1] for item in report.index["tracks"]] == [
        "a.mp3",
        "b.flac",
    ]
    assert report.index["provider"] == "local"


def test_scan_records_unreadable_files_without_aborting(tmp_path: Path):
    (tmp_path / "good.flac").write_bytes(b"fake")
    (tmp_path / "bad.flac").write_bytes(b"fake")

    def loader(path: Path):
        if path.name == "bad.flac":
            raise RuntimeError("decoder exploded")
        return _Audio({"isrc": ["KRABC2600001"]})

    report = scan_local_library(tmp_path, loader=loader)
    assert report.indexed_files == 1
    assert report.unreadable_files == 1
    assert "bad.flac: decoder exploded" in report.unreadable[0]


def test_non_recursive_scan_ignores_nested_files(tmp_path: Path):
    (tmp_path / "top.flac").write_bytes(b"fake")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "nested.flac").write_bytes(b"fake")

    def loader(path: Path):
        return _Audio({"isrc": ["KRABC2600001"]})

    report = scan_local_library(tmp_path, recursive=False, loader=loader)
    assert report.scanned_files == 1
    assert report.indexed_files == 1


def test_real_mutagen_wave_tags_are_scannable(tmp_path: Path):
    mutagen_wave = pytest.importorskip("mutagen.wave")
    id3 = pytest.importorskip("mutagen.id3")

    path = tmp_path / "tagged.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(44100)
        wav.writeframes(b"\x00\x00\x00\x00" * 4410)

    audio = mutagen_wave.WAVE(path)
    audio.add_tags()
    audio.tags.add(
        id3.TXXX(
            encoding=3,
            desc="MusicBrainz Recording Id",
            text=["11111111-2222-3333-4444-555555555555"],
        )
    )
    audio.tags.add(id3.TSRC(encoding=3, text=["KRABC2600001"]))
    audio.tags.add(id3.TIT2(encoding=3, text=["Tagged WAV"]))
    audio.tags.add(id3.TPE1(encoding=3, text=["Example Artist"]))
    audio.save()

    report = scan_local_library(tmp_path)
    assert report.indexed_files == 1
    item = report.index["tracks"][0]
    assert item["musicbrainz_recording_id"] == "11111111-2222-3333-4444-555555555555"
    assert item["isrcs"] == ["KRABC2600001"]
    assert item["title_hint"] == "Tagged WAV"
    assert item["artist_hint"] == "Example Artist"
