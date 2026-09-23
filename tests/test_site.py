import hashlib
from pathlib import Path

from playlistdisc.cli import main
from playlistdisc.site import build_static_site, verify_static_site

ROOT = Path(__file__).parents[1]
CATALOG = ROOT / "catalog"


def _tree_hashes(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def test_static_site_builds_and_verifies(tmp_path: Path):
    site = build_static_site(CATALOG, tmp_path / "site")
    assert verify_static_site(site) == []

    assert (site / "index.html").is_file()
    assert (site / "library.json").is_file()
    assert (site / "discs/999902.html").is_file()
    assert (site / "packs/draft-0-2-test-vectors.html").is_file()

    index = (site / "index.html").read_text(encoding="utf-8")
    assert "PDv1 audio beacon smoke test" in index
    assert 'href="discs/999902.html"' in index
    assert "data-library-query" in index

    pack = (site / "packs/draft-0-2-test-vectors.html").read_text(encoding="utf-8")
    assert '../discs/999901.html' in pack


def test_static_site_generation_is_deterministic(tmp_path: Path):
    first = build_static_site(CATALOG, tmp_path / "one")
    second = build_static_site(CATALOG, tmp_path / "two")
    assert _tree_hashes(first) == _tree_hashes(second)


def test_verifier_detects_broken_internal_link(tmp_path: Path):
    site = build_static_site(CATALOG, tmp_path / "site")
    index = site / "index.html"
    index.write_text(
        index.read_text(encoding="utf-8") + '<a href="missing.html">broken</a>',
        encoding="utf-8",
    )
    errors = verify_static_site(site)
    assert any("broken local reference missing.html" in error for error in errors)


def test_site_cli_roundtrip(tmp_path: Path, capsys):
    site = tmp_path / "site"
    assert main(["build-site", str(CATALOG), "--output", str(site)]) == 0
    assert str(site) in capsys.readouterr().out

    assert main(["verify-site", str(site)]) == 0
    assert "static site: PASS" in capsys.readouterr().out
