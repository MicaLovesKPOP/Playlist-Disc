from pathlib import Path

from playlistdisc.cli import main
from playlistdisc.testkit import VARIANTS, build_test_kit, verify_test_kit


def test_test_kit_builds_all_reference_variants(tmp_path: Path):
    root = build_test_kit(tmp_path / "kit")
    assert verify_test_kit(root) == []
    assert len(VARIANTS) == 4
    for variant in VARIANTS:
        assert (root / "variants" / variant.name / "disc.toc").is_file()


def test_test_kit_cli_roundtrip(tmp_path: Path, capsys):
    root = tmp_path / "kit"
    assert main(["build-test-kit", "--output", str(root)]) == 0
    assert str(root) in capsys.readouterr().out
    assert main(["verify-test-kit", str(root)]) == 0
    assert "test kit: PASS" in capsys.readouterr().out
