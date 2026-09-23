from pathlib import Path
import subprocess

import pytest

from playlistdisc.cdrdao import cdrdao_preflight
from playlistdisc.identity import PDIdentity
from playlistdisc.mastering import build_bundle


def test_cdrdao_preflight_runs_real_parser_commands_logically(
    tmp_path: Path, monkeypatch
):
    bundle = build_bundle(
        PDIdentity(999901),
        tmp_path / "disc",
        title="Test",
    )
    calls: list[tuple[list[str], Path]] = []

    monkeypatch.setattr("playlistdisc.cdrdao.shutil.which", lambda name: "/usr/bin/cdrdao")

    def fake_run(command, *, cwd, check, capture_output, text):
        assert check is False
        assert capture_output is True
        assert text is True
        calls.append((command, cwd))
        output = "8 tracks" if command[1] == "toc-info" else "12345"
        return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")

    monkeypatch.setattr("playlistdisc.cdrdao.subprocess.run", fake_run)

    report = cdrdao_preflight(bundle)
    assert report.executable == "/usr/bin/cdrdao"
    assert report.toc == (bundle / "disc.toc").resolve()
    assert report.toc_info == "8 tracks"
    assert report.toc_size == "12345"
    assert calls == [
        (["/usr/bin/cdrdao", "toc-info", "disc.toc"], bundle.resolve()),
        (["/usr/bin/cdrdao", "toc-size", "disc.toc"], bundle.resolve()),
    ]


def test_cdrdao_preflight_requires_external_tool(tmp_path: Path, monkeypatch):
    bundle = build_bundle(PDIdentity(999901), tmp_path / "disc", title="Test")
    monkeypatch.setattr("playlistdisc.cdrdao.shutil.which", lambda name: None)
    with pytest.raises(RuntimeError, match="not installed"):
        cdrdao_preflight(bundle)


def test_cdrdao_preflight_surfaces_parser_failure(tmp_path: Path, monkeypatch):
    bundle = build_bundle(PDIdentity(999901), tmp_path / "disc", title="Test")

    def fake_run(command, *, cwd, check, capture_output, text):
        return subprocess.CompletedProcess(
            command,
            1,
            stdout="",
            stderr="ERROR: bad toc",
        )

    monkeypatch.setattr("playlistdisc.cdrdao.subprocess.run", fake_run)
    with pytest.raises(ValueError, match="bad toc"):
        cdrdao_preflight(bundle, executable="cdrdao")


def test_cdrdao_preflight_refuses_internally_invalid_bundle(
    tmp_path: Path, monkeypatch
):
    bundle = build_bundle(PDIdentity(999901), tmp_path / "disc", title="Test")
    (bundle / "manifest.json").unlink()
    monkeypatch.setattr("playlistdisc.cdrdao.shutil.which", lambda name: "/usr/bin/cdrdao")
    with pytest.raises(ValueError, match="missing build artifact"):
        cdrdao_preflight(bundle)
