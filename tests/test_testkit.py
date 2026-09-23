import json
from pathlib import Path

from playlistdisc.cli import main
from playlistdisc.testkit import VARIANTS, build_test_kit, verify_test_kit


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_test_kit_builds_all_reference_variants(tmp_path: Path):
    root = build_test_kit(tmp_path / "kit")
    assert verify_test_kit(root) == []
    assert len(VARIANTS) == 4
    manifest = json.loads((root / "test-kit.json").read_text(encoding="utf-8"))
    assert len(manifest["content_sha256"]) == 64
    for record, variant in zip(manifest["variants"], VARIANTS, strict=True):
        bundle = root / "variants" / variant.name
        assert (bundle / "disc.toc").is_file()
        assert set(record["artifacts"]) == {
            "beacon.wav",
            "disc.toc",
            "manifest.json",
        }
        for artifact in record["artifacts"].values():
            assert artifact["bytes"] > 0
            assert len(artifact["sha256"]) == 64


def test_test_kit_is_byte_reproducible(tmp_path: Path):
    first = build_test_kit(tmp_path / "first")
    second = build_test_kit(tmp_path / "second")
    assert _tree_bytes(first) == _tree_bytes(second)


def test_test_kit_detects_semantically_harmless_artifact_drift(tmp_path: Path):
    root = build_test_kit(tmp_path / "kit")
    toc = root / "variants" / "toc-cdtext" / "disc.toc"
    toc.write_text(toc.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    errors = verify_test_kit(root)
    assert any("disc.toc byte size disagrees" in error for error in errors)
    assert any("disc.toc SHA-256 disagrees" in error for error in errors)


def test_test_kit_manifest_metadata_is_pinned_to_reference(tmp_path: Path):
    root = build_test_kit(tmp_path / "kit")
    path = root / "test-kit.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["variants"][0]["purpose"] = "Different experiment"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    errors = verify_test_kit(root)
    assert any("purpose disagrees with Draft" in error for error in errors)
    assert any("content_sha256 disagrees" in error for error in errors)


def test_test_kit_cli_roundtrip(tmp_path: Path, capsys):
    root = tmp_path / "kit"
    assert main(["build-test-kit", "--output", str(root)]) == 0
    assert str(root) in capsys.readouterr().out
    assert main(["verify-test-kit", str(root)]) == 0
    assert "test kit: PASS" in capsys.readouterr().out
