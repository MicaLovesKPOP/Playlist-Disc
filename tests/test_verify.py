import json
from pathlib import Path

import pytest

from playlistdisc.identity import DRAFT_VERSION, PDIdentity
from playlistdisc.mastering import build_bundle
from playlistdisc.verify import verify_build


def _rewrite_manifest(bundle: Path, **updates: object) -> None:
    path = bundle / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest.update(updates)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


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
    assert report.cd_text_present is True
    assert report.beacon_identity == identity
    assert report.beacon_frames == 2
    assert len(report.bundle_sha256) == 64


def test_intentional_no_cdtext_bundle_verifies_remaining_channels(tmp_path: Path):
    identity = PDIdentity(999901)
    bundle = build_bundle(
        identity,
        tmp_path / "disc",
        title="No CD-TEXT",
        cd_text=False,
    )
    report = verify_build(bundle)
    assert report.ok
    assert report.cdtext_identity is None
    assert report.cd_text_present is False
    assert report.toc_identity == identity
    assert report.beacon_identity == identity


def test_malformed_beacon_artifact_is_rejected_cleanly(tmp_path: Path):
    identity = PDIdentity(999901)
    bundle = build_bundle(identity, tmp_path / "disc", title="Test")
    (bundle / "beacon.wav").write_bytes(b"not a wav")
    with pytest.raises(ValueError, match="invalid WAV"):
        verify_build(bundle)


def test_cross_channel_mismatch_is_rejected(tmp_path: Path):
    identity = PDIdentity(999901)
    bundle = build_bundle(identity, tmp_path / "disc", title="Test")
    toc = bundle / "disc.toc"
    text = toc.read_text(encoding="utf-8")
    text = text.replace(identity.machine_id, PDIdentity(123456).machine_id)
    toc.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="channels disagree"):
        verify_build(bundle)


def test_cdtext_manifest_must_match_mastering_mode(tmp_path: Path):
    identity = PDIdentity(999901)
    bundle = build_bundle(identity, tmp_path / "disc", title="Test", cd_text=False)
    _rewrite_manifest(bundle, cd_text=True)
    with pytest.raises(ValueError, match="declares CD-TEXT but mastering TOC omits"):
        verify_build(bundle)


def test_stale_draft_metadata_is_rejected(tmp_path: Path):
    identity = PDIdentity(999901)
    bundle = build_bundle(identity, tmp_path / "disc", title="Test")
    _rewrite_manifest(bundle, draft="0.1")
    with pytest.raises(ValueError, match=f"manifest draft must be '{DRAFT_VERSION}'"):
        verify_build(bundle)


def test_manifest_namespace_mismatch_is_rejected(tmp_path: Path):
    identity = PDIdentity(999901)
    bundle = build_bundle(identity, tmp_path / "disc", title="Test")
    _rewrite_manifest(bundle, namespace="public")
    with pytest.raises(ValueError, match="namespace disagrees"):
        verify_build(bundle)


def test_manifest_total_duration_mismatch_is_rejected(tmp_path: Path):
    identity = PDIdentity(999901)
    bundle = build_bundle(identity, tmp_path / "disc", title="Test")
    _rewrite_manifest(bundle, total_seconds=identity.total_seconds + 1)
    with pytest.raises(ValueError, match="total duration disagrees"):
        verify_build(bundle)


def test_manifest_duration_vector_mismatch_is_rejected(tmp_path: Path):
    identity = PDIdentity(999901)
    bundle = build_bundle(identity, tmp_path / "disc", title="Test")
    durations = list(identity.track_durations)
    durations[-1] += 4
    _rewrite_manifest(bundle, track_durations_seconds=durations)
    with pytest.raises(ValueError, match="track durations disagree with identity"):
        verify_build(bundle)


def test_bundle_fingerprint_changes_when_exact_artifact_changes(tmp_path: Path):
    identity = PDIdentity(999901)
    first = build_bundle(identity, tmp_path / "one", title="Test")
    second = build_bundle(identity, tmp_path / "two", title="Test")
    assert verify_build(first).bundle_sha256 == verify_build(second).bundle_sha256

    toc = second / "disc.toc"
    toc.write_text(toc.read_text(encoding="utf-8") + "// harmless textual drift\n", encoding="utf-8")
    assert verify_build(first).bundle_sha256 != verify_build(second).bundle_sha256
