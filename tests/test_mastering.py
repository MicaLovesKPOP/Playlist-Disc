import json
from pathlib import Path

from playlistdisc.identity import DRAFT_VERSION, FORMAT_NAME, PDIdentity
from playlistdisc.mastering import BEACON_PROFILE, build_bundle, render_toc


def test_toc_has_eight_tracks_and_cdtext():
    ident = PDIdentity(999903)
    toc = render_toc(ident, title="PDv1 CD-TEXT smoke test", short_title="PDV1 CDTEXT")
    assert toc.count("TRACK AUDIO") == 8
    assert f"{FORMAT_NAME} Draft {DRAFT_VERSION}" in toc
    assert f'MESSAGE "{ident.machine_id}"' in toc
    assert 'AUDIOFILE "beacon.wav" 0' in toc
    assert "SILENCE 00:05:00" in toc


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
