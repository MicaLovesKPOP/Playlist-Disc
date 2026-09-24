from pathlib import Path

from playlistdisc.cli import main
from playlistdisc.library import pack_by_slug
from playlistdisc.wallet import build_wallet_index, render_wallet_index

ROOT = Path(__file__).parents[1]
CATALOG = ROOT / "catalog"


def test_wallet_index_renders_all_capacity_slots_deterministically():
    pack = pack_by_slug(CATALOG, "draft-0-2-test-vectors")
    assert pack is not None

    first = render_wallet_index(pack)
    second = render_wallet_index(pack)

    assert first == second
    assert first.count('class="slot filled"') == 3
    assert first.count('class="slot empty"') == 9
    assert first.count('data-slot="') == 12
    assert 'data-disc-id="999901"' in first
    assert "PD1-999903-0" in first
    assert "3/12 discs" in first


def test_wallet_index_escapes_catalog_display_text():
    pack = {
        "slug": "safe-pack",
        "title": "<Unsafe & title>",
        "status": "draft",
        "capacity": 12,
        "slots": [
            {
                "slot": 1,
                "id": "999901",
                "machine_id": "PD1-999901-7",
                "title": "Track <One>",
                "short_title": "A & B",
                "status": "draft",
                "tags": [],
            }
        ],
    }
    html = render_wallet_index(pack)
    assert "<Unsafe & title>" not in html
    assert "&lt;Unsafe &amp; title&gt;" in html
    assert "Track &lt;One&gt;" in html
    assert "A &amp; B" in html


def test_wallet_index_paginates_large_capacity_without_reordering():
    pack = {
        "slug": "large-pack",
        "title": "Large pack",
        "status": "draft",
        "capacity": 48,
        "slots": [],
    }
    html = render_wallet_index(pack)
    assert html.count('class="page"') == 2
    assert 'data-page="1"' in html
    assert 'data-page="2"' in html
    assert 'data-slot="24"' in html
    assert 'data-slot="25"' in html
    assert 'data-slot="48"' in html
    assert html.index('data-slot="24"') < html.index('data-slot="25"')


def test_build_wallet_cli_writes_reproducible_html(tmp_path: Path, capsys):
    output = tmp_path / "wallet.html"
    args = [
        "build-wallet",
        "draft-0-2-test-vectors",
        "--catalog",
        str(CATALOG),
        "--output",
        str(output),
    ]
    assert main(args) == 0
    first = output.read_bytes()
    capsys.readouterr()
    assert main(args) == 0
    second = output.read_bytes()
    assert first == second
    text = second.decode("utf-8")
    assert "PDv1 Draft 0.2 test vectors" in text
    assert 'data-slot="12"' in text


def test_build_wallet_rejects_unknown_pack(tmp_path: Path, capsys):
    output = tmp_path / "missing.html"
    assert main([
        "build-wallet",
        "does-not-exist",
        "--catalog",
        str(CATALOG),
        "--output",
        str(output),
    ]) == 2
    captured = capsys.readouterr()
    assert "does not exist" in captured.err
    assert not output.exists()
