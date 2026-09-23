from pathlib import Path

import pytest

from playlistdisc.identity import PDIdentity
from playlistdisc.mastering import build_bundle
from playlistdisc.verify import verify_build


def test_generated_bundle_verifies_all_identity_channels(tmp_path: Path):
    identity = PDIdentity(999901)
    bundle = build_bundle(
        identity,
        tmp_path / "PD1-999901",
        title="PDv1 TOC lattice smoke test",
        short_title="PDV1 TOC TEST",
    )
    report = verify_build(bundle)
    assert report.ok
    assert report.identity == identity
    assert report.manifest_identity == identity
    assert report.toc_identity == identity
    assert report.cdtext_identity == identity
    assert report.beacon_identity == identity
    assert report.beacon_frames == 2


def test_cross_channel_mismatch_is_rejected(tmp_path: Path):
    identity = PDIdentity(999901)
    bundle = build_bundle(identity, tmp_path / "disc", title="Test", short_title="TEST")
    toc = bundle / "disc.toc"
    text = toc.read_text(encoding="utf-8")
    text = text.replace(identity.machine_id, PDIdentity(123456).machine_id)
    toc.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="channels disagree"):
        verify_build(bundle)
