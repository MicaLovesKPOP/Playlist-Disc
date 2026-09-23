"""Software-only syntax/preflight checks using the real cdrdao parser."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess

from .verify import verify_build


@dataclass(frozen=True, slots=True)
class CdrdaoPreflightReport:
    executable: str
    toc: Path
    toc_info: str
    toc_size: str


def _run(command: list[str], *, cwd: Path) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        suffix = f": {detail}" if detail else ""
        raise ValueError(
            f"cdrdao parser command failed ({completed.returncode})"
            f"{suffix}"
        )
    return (completed.stdout or completed.stderr or "").strip()


def cdrdao_preflight(
    target: str | Path,
    *,
    executable: str | None = None,
) -> CdrdaoPreflightReport:
    """Verify a PD bundle, then ask cdrdao to parse and size its TOC.

    This needs no optical drive. It is deliberately stronger than checking our own
    textual TOC parser because it exercises the external reference mastering tool
    that will later be asked to write the disc.
    """
    path = Path(target)
    if path.is_dir():
        bundle = path
        toc = path / "disc.toc"
    else:
        toc = path
        bundle = path.parent

    if not toc.is_file():
        raise ValueError(f"TOC file does not exist: {toc}")

    # Never present an external-parser success as proof when our own bundle is stale
    # or internally inconsistent.
    verify_build(bundle)

    command = executable or shutil.which("cdrdao")
    if not command:
        raise RuntimeError("cdrdao is not installed or not on PATH")

    cwd = toc.parent.resolve()
    toc_name = toc.name
    info = _run([command, "toc-info", toc_name], cwd=cwd)
    size = _run([command, "toc-size", toc_name], cwd=cwd)
    return CdrdaoPreflightReport(
        executable=command,
        toc=toc.resolve(),
        toc_info=info,
        toc_size=size,
    )
