"""Dependency-free static HTML library generation for PDv1."""

from __future__ import annotations

from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any
from urllib.parse import unquote, urlsplit

from .catalog import validate_catalog
from .library import library_snapshot


_STYLE = """\
:root {
  color-scheme: light dark;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.5;
  --page: #f4f5f7;
  --card: #ffffff;
  --text: #17191c;
  --muted: #616873;
  --border: #d7dbe0;
  --accent: #3157c8;
}
@media (prefers-color-scheme: dark) {
  :root {
    --page: #111317;
    --card: #1b1f24;
    --text: #eef1f4;
    --muted: #a9b0ba;
    --border: #353b44;
    --accent: #8da7ff;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--text); }
header, main, footer { width: min(1100px, calc(100% - 2rem)); margin-inline: auto; }
header { padding: 1.25rem 0 .75rem; display: flex; gap: 1rem; align-items: baseline; justify-content: space-between; }
header a { color: var(--text); text-decoration: none; font-weight: 750; }
main { padding-bottom: 3rem; }
footer { border-top: 1px solid var(--border); color: var(--muted); padding: 1.25rem 0 2rem; font-size: .9rem; }
h1 { line-height: 1.15; margin-bottom: .5rem; }
h2 { margin-top: 2rem; }
.lede { color: var(--muted); max-width: 75ch; }
.controls { display: grid; grid-template-columns: minmax(15rem, 2fr) repeat(3, minmax(8rem, 1fr)); gap: .75rem; margin: 1.5rem 0; }
.controls label { font-size: .85rem; color: var(--muted); }
.controls input, .controls select { width: 100%; margin-top: .25rem; padding: .65rem .7rem; border: 1px solid var(--border); border-radius: .5rem; background: var(--card); color: var(--text); }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(255px, 1fr)); gap: .8rem; }
.card { display: block; padding: 1rem; border: 1px solid var(--border); background: var(--card); border-radius: .7rem; color: var(--text); text-decoration: none; }
.card:hover { border-color: var(--accent); }
.card h3 { margin: 0 0 .35rem; font-size: 1rem; }
.meta { color: var(--muted); font-size: .88rem; }
.badges { display: flex; gap: .4rem; flex-wrap: wrap; margin-top: .65rem; }
.badge { display: inline-block; border: 1px solid var(--border); border-radius: 999px; padding: .12rem .48rem; font-size: .75rem; color: var(--muted); }
.detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: .8rem; }
.panel { padding: 1rem; border: 1px solid var(--border); background: var(--card); border-radius: .7rem; overflow-wrap: anywhere; }
.panel h2, .panel h3 { margin-top: 0; }
dl { display: grid; grid-template-columns: max-content 1fr; gap: .35rem .8rem; margin: 0; }
dt { color: var(--muted); }
dd { margin: 0; }
pre { overflow: auto; padding: .75rem; background: var(--page); border: 1px solid var(--border); border-radius: .45rem; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: .55rem; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }
code { overflow-wrap: anywhere; }
.empty { color: var(--muted); font-style: italic; }
[hidden] { display: none !important; }
@media (max-width: 760px) {
  .controls { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 500px) {
  .controls { grid-template-columns: 1fr; }
  dl { grid-template-columns: 1fr; }
}
"""

_SCRIPT = """\
(() => {
  const query = document.querySelector('[data-library-query]');
  const status = document.querySelector('[data-filter-status]');
  const type = document.querySelector('[data-filter-type]');
  const portability = document.querySelector('[data-filter-portability]');
  const cards = Array.from(document.querySelectorAll('[data-entry-card]'));
  const count = document.querySelector('[data-result-count]');
  if (!query || !status || !type || !portability) return;

  function update() {
    const tokens = query.value.trim().toLocaleLowerCase().split(/\\s+/).filter(Boolean);
    let visible = 0;
    for (const card of cards) {
      const text = card.dataset.search || '';
      const matchesText = tokens.every(token => text.includes(token));
      const matchesStatus = !status.value || card.dataset.status === status.value;
      const matchesType = !type.value || card.dataset.type === type.value;
      const matchesPortability = !portability.value || card.dataset.portability === portability.value;
      card.hidden = !(matchesText && matchesStatus && matchesType && matchesPortability);
      if (!card.hidden) visible += 1;
    }
    if (count) count.textContent = String(visible);
  }

  for (const element of [query, status, type, portability]) {
    element.addEventListener('input', update);
    element.addEventListener('change', update);
  }
  update();
})();
"""


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def _page(title: str, body: str, *, prefix: str = "", script: bool = False) -> str:
    script_tag = (
        f'<script src="{prefix}assets/site.js" defer></script>' if script else ""
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} · Playlist Disc</title>
  <link rel="stylesheet" href="{prefix}assets/site.css">
  {script_tag}
</head>
<body>
<header>
  <a href="{prefix}index.html">Playlist Disc</a>
  <span class="meta">PDv1 Draft 0.2 library</span>
</header>
<main>
{body}
</main>
<footer>
  Generated from the validated provider-neutral Playlist Disc catalog. No accounts, telemetry, or external JavaScript dependencies.
</footer>
</body>
</html>
"""


def _badges(entry: dict[str, Any]) -> str:
    values = [
        entry["status"],
        entry["definition"]["type"].replace("_", " "),
        entry["portability"].replace("_", " "),
        entry["lifecycle"],
    ]
    return '<div class="badges">' + "".join(
        f'<span class="badge">{escape(value)}</span>' for value in values
    ) + "</div>"


def _entry_card(entry: dict[str, Any]) -> str:
    search = json.dumps(entry, ensure_ascii=False, sort_keys=True).casefold()
    return f"""<a class="card" data-entry-card
  data-search="{escape(search, quote=True)}"
  data-status="{escape(entry["status"], quote=True)}"
  data-type="{escape(entry["definition"]["type"], quote=True)}"
  data-portability="{escape(entry["portability"], quote=True)}"
  href="discs/{entry["id"]}.html">
  <h3>{escape(entry["title"])}</h3>
  <div class="meta">{escape(entry["machine_id"])} · {escape(entry["short_title"])}</div>
  {_badges(entry)}
</a>"""


def _select(name: str, values: list[str], label: str, attr: str) -> str:
    options = '<option value="">All</option>' + "".join(
        f'<option value="{escape(value, quote=True)}">{escape(value.replace("_", " "))}</option>'
        for value in values
    )
    return (
        f'<label>{escape(label)}<select {attr} name="{escape(name, quote=True)}">'
        f"{options}</select></label>"
    )


def _index_page(snapshot: dict[str, Any]) -> str:
    facets = snapshot["facets"]
    entries = snapshot["entries"]
    packs = snapshot["packs"]
    controls = (
        '<div class="controls">'
        '<label>Search<input data-library-query type="search" placeholder="artist, genre, ID, tag…" autocomplete="off"></label>'
        + _select("status", facets["statuses"], "Status", "data-filter-status")
        + _select("type", facets["definition_types"], "Definition", "data-filter-type")
        + _select("portability", facets["portability"], "Portability", "data-filter-portability")
        + "</div>"
    )
    cards = "\n".join(_entry_card(entry) for entry in entries)
    pack_cards = "\n".join(
        f"""<a class="card" href="packs/{escape(pack["slug"], quote=True)}.html">
  <h3>{escape(pack["title"])}</h3>
  <div class="meta">{pack["disc_count"]}/{pack["capacity"]} slots · {escape(pack["status"])}</div>
  <div class="badges">{''.join(f'<span class="badge">{escape(tag)}</span>' for tag in pack.get("tags", []))}</div>
</a>"""
        for pack in packs
    )
    if not pack_cards:
        pack_cards = '<p class="empty">No packs are currently defined.</p>'
    body = f"""<h1>Playlist Disc library</h1>
<p class="lede">Browse the validated PDv1 catalog. Physical IDs describe musical intent; provider bindings and playback services are separate realization layers.</p>
{controls}
<p class="meta"><span data-result-count>{len(entries)}</span> disc entries</p>
<div class="grid">{cards}</div>
<h2>Packs / wallet views</h2>
<div class="grid">{pack_cards}</div>
<noscript><p class="meta">JavaScript is optional; all entries and links remain visible, but interactive filtering is disabled.</p></noscript>"""
    return _page("Library", body, script=True)


def _definition_panel(entry: dict[str, Any]) -> str:
    return f"""<section class="panel">
<h2>Meaning</h2>
<dl>
  <dt>Definition</dt><dd>{escape(entry["definition"]["type"].replace("_", " "))}</dd>
  <dt>Portability</dt><dd>{escape(entry["portability"].replace("_", " "))}</dd>
  <dt>Lifecycle</dt><dd>{escape(entry["lifecycle"])}</dd>
  <dt>Authority</dt><dd>{escape(entry["provenance"]["authority"])}</dd>
</dl>
<h3>Definition data</h3>
<pre>{escape(_json_text(entry["definition"]))}</pre>
</section>"""


def _entry_page(entry: dict[str, Any]) -> str:
    tags = ", ".join(entry.get("tags", [])) or "none"
    playback = entry["playback"]
    providers = entry.get("providers", {})
    provider_rows = "".join(
        f"<tr><td>{escape(name)}</td><td>{escape(binding['strategy'])}</td>"
        f"<td>{escape(binding.get('resource', ''))}</td></tr>"
        for name, binding in sorted(providers.items())
    )
    if not provider_rows:
        provider_rows = '<tr><td colspan="3" class="empty">No provider bindings declared.</td></tr>'

    manifest = entry.get("canonical_manifest")
    manifest_html = ""
    if manifest:
        manifest_html = (
            "<h3>Canonical manifest</h3><dl>"
            f"<dt>Recordings</dt><dd>{manifest['recording_count']}</dd>"
            f"<dt>SHA-256</dt><dd><code>{escape(manifest['sha256'])}</code></dd>"
            "</dl>"
        )

    durations = ", ".join(str(value) for value in entry["track_durations_seconds"])
    body = f"""<p><a href="../index.html">← Library</a></p>
<h1>{escape(entry["title"])}</h1>
<p class="lede">{escape(entry["machine_id"])} · {escape(entry["short_title"])}</p>
{_badges(entry)}
<div class="detail-grid">
  {_definition_panel(entry)}
  <section class="panel">
    <h2>Playback</h2>
    <dl>
      <dt>Order</dt><dd>{escape(playback["order"])}</dd>
      <dt>Start</dt><dd>{escape(playback["start"])}</dd>
      <dt>Repeat</dt><dd>{escape(playback["repeat"])}</dd>
      <dt>Tags</dt><dd>{escape(tags)}</dd>
    </dl>
    {manifest_html}
  </section>
  <section class="panel">
    <h2>Physical identity</h2>
    <dl>
      <dt>ID</dt><dd><code>{escape(entry["id"])}</code></dd>
      <dt>Machine ID</dt><dd><code>{escape(entry["machine_id"])}</code></dd>
      <dt>Track seconds</dt><dd><code>{escape(durations)}</code></dd>
      <dt>TOC SHA-256</dt><dd><code>{escape(entry["toc_sha256"])}</code></dd>
    </dl>
  </section>
</div>
<section class="panel">
<h2>Provider bindings</h2>
<table>
<thead><tr><th>Provider</th><th>Strategy</th><th>Resource</th></tr></thead>
<tbody>{provider_rows}</tbody>
</table>
</section>"""
    return _page(entry["title"], body, prefix="../")


def _pack_page(pack: dict[str, Any]) -> str:
    rows = "".join(
        f"""<tr>
<td>{slot["slot"]:02d}</td>
<td><a href="../discs/{slot["id"]}.html">{escape(slot["id"])}</a></td>
<td>{escape(slot["short_title"])}</td>
<td>{escape(slot["title"])}</td>
</tr>"""
        for slot in pack["slots"]
    )
    description = pack.get("description", "")
    body = f"""<p><a href="../index.html">← Library</a></p>
<h1>{escape(pack["title"])}</h1>
<p class="lede">{escape(description)}</p>
<p class="meta">{pack["disc_count"]}/{pack["capacity"]} slots · {escape(pack["status"])}</p>
<section class="panel">
<table>
<thead><tr><th>Slot</th><th>ID</th><th>Short title</th><th>Title</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</section>"""
    return _page(pack["title"], body, prefix="../")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def build_static_site(catalog_dir: str | Path, output_dir: str | Path) -> Path:
    """Build a deterministic, dependency-free static library site."""
    errors = validate_catalog(catalog_dir)
    if errors:
        raise ValueError("invalid catalog: " + "; ".join(errors))

    snapshot = library_snapshot(catalog_dir)
    output = Path(output_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output.name}-", dir=str(output.parent))
    )
    try:
        _write(staging / "assets/site.css", _STYLE)
        _write(staging / "assets/site.js", _SCRIPT)
        _write(
            staging / "library.json",
            json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        )
        _write(staging / "index.html", _index_page(snapshot))
        for entry in snapshot["entries"]:
            _write(staging / "discs" / f"{entry['id']}.html", _entry_page(entry))
        for pack in snapshot["packs"]:
            _write(staging / "packs" / f"{pack['slug']}.html", _pack_page(pack))

        verify_errors = verify_static_site(staging)
        if verify_errors:
            raise ValueError("generated site failed verification: " + "; ".join(verify_errors))

        if output.exists():
            if output.is_dir():
                shutil.rmtree(output)
            else:
                output.unlink()
        staging.replace(output)
        return output
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


class _ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = "href" if tag in {"a", "link"} else "src" if tag == "script" else None
        if attr is None:
            return
        for name, value in attrs:
            if name == attr and value:
                self.references.append(value)


def _local_reference_target(root: Path, page: Path, reference: str) -> Path | None:
    split = urlsplit(reference)
    if split.scheme or split.netloc or reference.startswith("#"):
        return None
    decoded = unquote(split.path)
    if not decoded:
        return None
    if decoded.startswith("/"):
        raise ValueError(f"root-relative reference is not portable: {reference}")
    target = (page.parent / decoded).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"reference escapes generated site: {reference}") from exc
    return target


def verify_static_site(site_dir: str | Path) -> list[str]:
    """Verify generated files, library/detail-page coverage, and local links."""
    root = Path(site_dir)
    errors: list[str] = []
    required = [
        root / "index.html",
        root / "library.json",
        root / "assets/site.css",
        root / "assets/site.js",
    ]
    for path in required:
        if not path.is_file():
            try:
                label = path.relative_to(root)
            except ValueError:
                label = path
            errors.append(f"missing required file: {label}")
    if errors:
        return errors

    try:
        snapshot = json.loads((root / "library.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"library.json: {exc}"]

    if snapshot.get("format") != "PDv1-library":
        errors.append("library.json: unexpected format")

    expected_discs = {entry["id"] for entry in snapshot.get("entries", [])}
    actual_discs = {path.stem for path in (root / "discs").glob("*.html")}
    if actual_discs != expected_discs:
        errors.append(
            "disc detail pages disagree with library.json: "
            f"expected={sorted(expected_discs)}, actual={sorted(actual_discs)}"
        )

    expected_packs = {pack["slug"] for pack in snapshot.get("packs", [])}
    actual_packs = {path.stem for path in (root / "packs").glob("*.html")}
    if actual_packs != expected_packs:
        errors.append(
            "pack pages disagree with library.json: "
            f"expected={sorted(expected_packs)}, actual={sorted(actual_packs)}"
        )

    for page in sorted(root.rglob("*.html")):
        parser = _ReferenceParser()
        try:
            parser.feed(page.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            errors.append(f"{page.relative_to(root)}: {exc}")
            continue
        for reference in parser.references:
            try:
                target = _local_reference_target(root, page, reference)
            except ValueError as exc:
                errors.append(f"{page.relative_to(root)}: {exc}")
                continue
            if target is not None and not target.exists():
                errors.append(
                    f"{page.relative_to(root)}: broken local reference {reference}"
                )

    return errors
