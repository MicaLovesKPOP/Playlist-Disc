import json
from pathlib import Path

from playlistdisc.identity import DRAFT_VERSION, FORMAT_NAME, PDIdentity
from playlistdisc.mastering import BEACON_PROFILE, build_bundle, render_toc


def test_toc_has_eight_tracks_and_cdtext():
    ident = PDIdentity(999903)
    toc = render_toc(
        ident,
        title="PDv1 CD-TEXT smoke test",
        short_title="PDV1 CDTEXT",
    )
    assert toc.count("TRACK AUDIO") == 8
    assert f"{FORMAT_NAME} Draft {DRAFT_VERSION}" in toc
    assert f'MESSAGE "{ident.machine_id}"' in toc
    assert 'AUDIOFILE "beacon.wav" 0' in toc
    assert "SILENCE 00:05:00" in toc


def test_toc_can_intentionally_omit_cdtext_without_changing_timing():
    ident = PDIdentity(999901)
    with_text = render_toc(ident, title="Test", cd_text=True)
    without_text = render_toc(ident, title="Test", cd_text=False)
    assert "CD_TEXT {" in with_text
    assert ident.machine_id in with_text
    assert "CD_TEXT {" not in without_text
    assert ident.machine_id not in without_text
    assert with_text.count("TRACK AUDIO") == without_text.count("TRACK AUDIO") == 8
    for duration in ident.track_durations[1:]:
        minutes, seconds = divmod(duration, 60)
        marker = f"SILENCE {minutes:02d}:{seconds:02d}:00"
        assert marker in with_text
        assert marker in without_text


def test_build_bundle(tmp_path: Path):
    ident = PDIdentity(999901)
    out = build_bundle(ident, tmp_path / "disc", title="Test", short_title="TEST")
    assert (out / "disc.toc").exists()
    assert (out / "beacon.wav").exists()
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["format"] == FORMAT_NAME
    assert manifest["draft"] == DRAFT_VERSION
    assert manifest["beacon_profile"] == BEACON_PROFILE
    assert manifest["namespace"] == ident.namespace
    assert manifest["machine_id"] == ident.machine_id
    assert manifest["track_durations_seconds"] == list(ident.track_durations)
    assert manifest["total_seconds"] == ident.total_seconds
    assert manifest["cd_text"] is True


def test_build_bundle_records_no_cdtext_variant(tmp_path: Path):
    ident = PDIdentity(999901)
    out = build_bundle(
        ident,
        tmp_path / "disc",
        title="Test",
        short_title="TEST",
        cd_text=False,
    )
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["cd_text"] is False
    assert "CD_TEXT {" not in (out / "disc.toc").read_text(encoding="utf-8")
