"""Deterministic printable HTML indexes for Playlist Disc wallet packs."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

from .library import pack_by_slug

SLOTS_PER_PAGE = 24


def _validated_slots(pack: dict[str, Any]) -> tuple[int, list[dict[str, Any]]]:
    capacity = pack.get("capacity")
    slots = pack.get("slots")
    if capacity not in {12, 24, 48, 96}:
        raise ValueError("wallet pack capacity must be one of 12, 24, 48, or 96")
    if not isinstance(slots, list) or len(slots) > capacity:
        raise ValueError("wallet pack slots must be a list no larger than capacity")
    expected = list(range(1, len(slots) + 1))
    if [slot.get("slot") for slot in slots if isinstance(slot, dict)] != expected:
        raise ValueError("wallet pack slots must be consecutive and 1-based")
    return capacity, slots


def _slot_html(number: int, slot: dict[str, Any] | None) -> str:
    if slot is None:
        return (
            f'        <li class="slot empty" data-slot="{number}">'
            f'<span class="slot-number">{number:02d}</span>'
            '<span class="empty-label">Empty slot</span></li>'
        )
    disc_id = escape(str(slot["id"]), quote=True)
    machine_id = escape(str(slot["machine_id"]), quote=True)
    short_title = escape(str(slot["short_title"]))
    title = escape(str(slot["title"]))
    status = escape(str(slot["status"]))
    return (
        f'        <li class="slot filled" data-slot="{number}" data-disc-id="{disc_id}">'
        f'<span class="slot-number">{number:02d}</span>'
        '<span class="disc-copy">'
        f'<strong>{short_title}</strong>'
        f'<span class="full-title">{title}</span>'
        f'<code>{machine_id}</code>'
        f'<span class="status">{status}</span>'
        '</span></li>'
    )


def render_wallet_index(pack: dict[str, Any]) -> str:
    """Render one resolved pack as deterministic, dependency-free printable HTML."""
    capacity, slots = _validated_slots(pack)
    by_number = {slot["slot"]: slot for slot in slots}
    title = escape(str(pack["title"]))
    slug = escape(str(pack["slug"]), quote=True)
    status = escape(str(pack["status"]))
    disc_count = len(slots)
    page_count = (capacity + SLOTS_PER_PAGE - 1) // SLOTS_PER_PAGE

    lines = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '  <meta charset="utf-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1">',
        f"  <title>{title} - Playlist Disc wallet index</title>",
        "  <style>",
        "    :root { font-family: system-ui, sans-serif; color: #111; background: #fff; }",
        "    body { margin: 0; }",
        "    .page { box-sizing: border-box; padding: 1rem; break-after: page; }",
        "    .page:last-child { break-after: auto; }",
        "    header { display: flex; justify-content: space-between; gap: 1rem; align-items: baseline; }",
        "    h1 { margin: 0; font-size: 1.2rem; }",
        "    .meta { margin: .25rem 0 .75rem; font-size: .8rem; }",
        "    .slots { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .35rem .75rem; }",
        "    .slot { min-height: 3.2rem; border: 1px solid #777; padding: .35rem; display: flex; gap: .5rem; break-inside: avoid; }",
        "    .slot-number { font: 700 .9rem ui-monospace, monospace; min-width: 2.2em; }",
        "    .disc-copy { min-width: 0; display: grid; gap: .05rem; }",
        "    .full-title, .status, .empty-label { font-size: .75rem; }",
        "    code { font-size: .72rem; overflow-wrap: anywhere; }",
        "    .empty { color: #666; border-style: dashed; }",
        "    @media print { @page { margin: 12mm; } .page { padding: 0; } }",
        "  </style>",
        "</head>",
        f'<body data-pack="{slug}">',
    ]

    for page_index in range(page_count):
        start = page_index * SLOTS_PER_PAGE + 1
        end = min(capacity, start + SLOTS_PER_PAGE - 1)
        lines.extend(
            [
                f'  <section class="page" data-page="{page_index + 1}">',
                "    <header>",
                f"      <h1>{title}</h1>",
                f"      <span>Page {page_index + 1}/{page_count}</span>",
                "    </header>",
                f'    <p class="meta">{disc_count}/{capacity} discs - {status} - slots {start:02d}-{end:02d}</p>',
                '    <ol class="slots">',
            ]
        )
        for number in range(start, end + 1):
            lines.append(_slot_html(number, by_number.get(number)))
        lines.extend(["    </ol>", "  </section>"])

    lines.extend(["</body>", "</html>", ""])
    return "\n".join(lines)


def build_wallet_index(
    catalog_dir: str | Path,
    slug: str,
    output: str | Path,
) -> Path:
    """Resolve a catalog pack and write its deterministic printable wallet index."""
    pack = pack_by_slug(catalog_dir, slug)
    if pack is None:
        raise ValueError(f"catalog pack {slug!r} does not exist")
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = render_wallet_index(pack)
    temporary = output_path.with_name(output_path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(output_path)
    return output_path
