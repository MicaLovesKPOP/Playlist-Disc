import json
from pathlib import Path

from playlistdisc.cli import main
from playlistdisc.library import library_snapshot, pack_by_slug, search_catalog

ROOT = Path(__file__).parents[1]
CATALOG = ROOT / "catalog"


def test_library_snapshot_resolves_pack_slots_and_facets():
    payload = library_snapshot(CATALOG)

    assert payload["format"] == "PDv1-library"
    assert len(payload["entries"]) == 3
    assert len(payload["packs"]) == 1
    pack = payload["packs"][0]
    assert pack["slug"] == "draft-0-2-test-vectors"
    assert pack["disc_count"] == 3
    assert [slot["id"] for slot in pack["slots"]] == [
        "999901",
        "999902",
        "999903",
    ]
    assert [slot["slot"] for slot in pack["slots"]] == [1, 2, 3]
    assert all(slot["machine_id"].startswith("PD1-") for slot in pack["slots"])
    assert "diagnostic" in payload["facets"]["tags"]


def test_pack_lookup_returns_resolved_wallet():
    pack = pack_by_slug(CATALOG, "draft-0-2-test-vectors")
    assert pack is not None
    assert pack["capacity"] == 12
    assert pack["slots"][1]["short_title"] == "PDV1 BEACON"
    assert pack_by_slug(CATALOG, "does-not-exist") is None


def test_search_uses_and_tokens_and_tag_filters():
    results = search_catalog(CATALOG, "diagnostic beacon")
    assert [entry["id"] for entry in results] == ["999902"]

    results = search_catalog(CATALOG, "test", tags={"cd-text"})
    assert [entry["id"] for entry in results] == ["999903"]


def test_library_cli_export_search_and_pack_commands(tmp_path: Path, capsys):
    output = tmp_path / "library.json"
    assert main(["export-library", str(CATALOG), "--output", str(output)]) == 0
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["packs"][0]["disc_count"] == 3

    assert main(
        ["search-catalog", "audio beacon", "--catalog", str(CATALOG), "--json"]
    ) == 0
    search_output = capsys.readouterr().out
    assert '"999902"' in search_output

    assert main(["pack-list", str(CATALOG)]) == 0
    pack_list_output = capsys.readouterr().out
    assert "draft-0-2-test-vectors" in pack_list_output
    assert "3/12" in pack_list_output

    assert main(
        [
            "pack-show",
            "draft-0-2-test-vectors",
            "--catalog",
            str(CATALOG),
        ]
    ) == 0
    pack_output = capsys.readouterr().out
    assert "01\t999901" in pack_output
    assert "03\t999903" in pack_output
