import json
from pathlib import Path

from playlistdisc.identity import PDIdentity
from playlistdisc.mastering import build_bundle, render_toc


def test_toc_has_eight_tracks_and_cdtext():
    ident = PDIdentity(999903)
    toc = render_toc(ident, title="PDv1 CD-TEXT smoke test", short_title="PDV1 CDTEXT")
    assert toc.count("TRACK AUDIO") == 8
    assert f'MESSAGE "{ident.machine_id}"' in toc
    assert 'AUDIOFILE "beacon.wav" 0' in toc
    assert "SILENCE 00:05:00" in toc


def test_build_bundle(tmp_path: Path):
    ident = PDIdentity(999901)
    out = build_bundle(ident, tmp_path / "disc", title="Test", short_title="TEST")
    assert (out / "disc.toc").exists()
    assert (out / "beacon.wav").exists()
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["machine_id"] == ident.machine_id
    assert manifest["track_durations_seconds"] == list(ident.track_durations)
