from pathlib import Path

from playlistdisc.cli import main
from playlistdisc.identity import PDIdentity
from playlistdisc.mastering import build_bundle


def test_burn_command_refuses_non_test_namespace_during_draft(tmp_path: Path, capsys):
    bundle = build_bundle(
        PDIdentity(900000),
        tmp_path / "private",
        title="Private virtual disc",
    )
    assert main(["burn", str(bundle / "disc.toc"), "--simulate"]) == 2
    error = capsys.readouterr().err
    assert "restricted to development/test IDs" in error


def test_burn_command_refuses_unverified_toc(tmp_path: Path, capsys):
    root = tmp_path / "not-a-bundle"
    root.mkdir()
    toc = root / "disc.toc"
    toc.write_text("CD_DA\n", encoding="utf-8")
    assert main(["burn", str(toc), "--simulate"]) == 2
    assert "unverified mastering bundle" in capsys.readouterr().err
