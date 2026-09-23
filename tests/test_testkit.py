import json
from pathlib import Path

from playlistdisc.cli import main
from playlistdisc.testkit import VARIANTS, build_test_kit, verify_test_kit


def test_test_kit_builds_all_reference_variants(tmp_path: Path):
    root = build_test_kit(tmp_path / "kit")
    assert verify_test_kit(root) == []
    assert len(VARIANTS) == 4
    manifest = json.loads((root / "test-kit.json").read_text(encoding="utf-8"))
    assert len(manifest["variants"]) == len(VARIANTS)
    for variant, record in zip(VARIANTS, manifest["variants"], strict=True):
        assert (root / "variants" / variant.name / "disc.toc").is_file()
        assert len(record["bundle_sha256"]) == 64


def test_test_kit_cli_roundtrip(tmp_path: Path, capsys):
    root = tmp_path / "kit"
    assert main(["build-test-kit", "--output", str(root)]) == 0
    assert str(root) in capsys.readouterr().out
    assert main(["verify-test-kit", str(root)]) == 0
    assert "test kit: PASS" in capsys.readouterr().out


def test_test_kit_detects_bundle_fingerprint_drift(tmp_path: Path):
    root = build_test_kit(tmp_path / "kit")
    toc = root / "variants" / "toc-cdtext" / "disc.toc"
    toc.write_text(toc.read_text(encoding="utf-8") + "// drift\n", encoding="utf-8")
    errors = verify_test_kit(root)
    assert any("bundle SHA-256 disagrees" in error for error in errors)
