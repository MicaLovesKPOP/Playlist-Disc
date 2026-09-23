"""Command-line interface for the PDv1 draft toolkit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from .catalog import find_entry, iter_entries, load_schema, load_yaml, validate_entry
from .identity import PDIdentity, decode_track_durations
from .mastering import build_bundle


def _format_duration(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


def cmd_inspect(args: argparse.Namespace) -> int:
    ident = PDIdentity.parse(args.id)
    print(ident.machine_id)
    print(f"namespace: {ident.namespace}")
    print(f"check digit: {ident.check_digit}")
    print("tracks: " + ", ".join(_format_duration(x) for x in ident.track_durations))
    print(f"total: {_format_duration(ident.total_seconds)}")
    print(f"TOC SHA-256: {ident.toc_signature}")
    print(f"beacon: {ident.beacon_symbols}")
    return 0


def cmd_decode(args: argparse.Namespace) -> int:
    ident = decode_track_durations(args.seconds, tolerance=args.tolerance)
    print(ident.machine_id)
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    ident = PDIdentity.parse(args.id)
    title = args.title
    short_title = args.short_title
    if args.catalog:
        found = find_entry(args.catalog, ident)
        if found:
            _, entry = found
            title = title or entry.get("title")
            short_title = short_title or entry.get("short_title")
    if not title:
        title = ident.canonical
    output = Path(args.output or f"build/{ident.canonical}")
    build_bundle(ident, output, title=title, short_title=short_title)
    print(output)
    return 0


def cmd_validate_catalog(args: argparse.Namespace) -> int:
    schema_path = Path(args.schema or Path(args.catalog) / "schema" / "disc.schema.json")
    schema = load_schema(schema_path)
    failed = False
    count = 0
    seen: dict[str, Path] = {}
    for path in iter_entries(args.catalog):
        count += 1
        data = load_yaml(path)
        errors = validate_entry(data, schema)
        ident = str(data.get("id", "")).zfill(6)
        if ident in seen:
            errors.append(f"id: duplicate of {seen[ident]}")
        else:
            seen[ident] = path
        if errors:
            failed = True
            print(f"{path}:", file=sys.stderr)
            for message in errors:
                print(f"  - {message}", file=sys.stderr)
    if failed:
        return 1
    print(f"validated {count} catalog entries")
    return 0


def cmd_export_catalog(args: argparse.Namespace) -> int:
    entries = []
    for path in iter_entries(args.catalog):
        data = load_yaml(path)
        ident = PDIdentity.parse(str(data["id"]))
        item = dict(data)
        item["machine_id"] = ident.machine_id
        item["namespace"] = ident.namespace
        item["track_durations_seconds"] = list(ident.track_durations)
        item["toc_sha256"] = ident.toc_signature
        entries.append(item)
    entries.sort(key=lambda item: item["id"])
    payload = {"schema_version": 1, "format": "PDv1", "entries": entries}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"exported {len(entries)} entries to {output}")
    return 0


def cmd_burn(args: argparse.Namespace) -> int:
    toc = Path(args.toc)
    if not toc.exists():
        print(f"error: {toc} does not exist", file=sys.stderr)
        return 2
    cdrdao = shutil.which("cdrdao")
    if not cdrdao:
        print("error: cdrdao is not installed or not on PATH", file=sys.stderr)
        return 2
    command = [cdrdao, "write"]
    if args.device:
        command += ["--device", args.device]
    if args.speed:
        command += ["--speed", str(args.speed)]
    if args.simulate:
        command.append("--simulate")
    command.append(toc.name)
    print("running:", " ".join(command))
    return subprocess.call(command, cwd=toc.parent)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pdv1", description="Playlist Disc v1 draft toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_p = sub.add_parser("inspect", help="show the deterministic physical encoding for an ID")
    inspect_p.add_argument("id")
    inspect_p.set_defaults(func=cmd_inspect)

    decode_p = sub.add_parser("decode", help="decode eight track durations in seconds")
    decode_p.add_argument("seconds", nargs=8, type=float)
    decode_p.add_argument("--tolerance", type=float, default=0.0)
    decode_p.set_defaults(func=cmd_decode)

    build_p = sub.add_parser("build", help="generate a cdrdao-ready PDv1 bundle")
    build_p.add_argument("id")
    build_p.add_argument("--title")
    build_p.add_argument("--short-title")
    build_p.add_argument("--catalog", default="catalog")
    build_p.add_argument("--output")
    build_p.set_defaults(func=cmd_build)

    val_p = sub.add_parser("validate-catalog", help="validate all registry entries")
    val_p.add_argument("catalog", nargs="?", default="catalog")
    val_p.add_argument("--schema")
    val_p.set_defaults(func=cmd_validate_catalog)

    export_p = sub.add_parser("export-catalog", help="build a single generated JSON catalog snapshot")
    export_p.add_argument("catalog", nargs="?", default="catalog")
    export_p.add_argument("--output", default="build/catalog.json")
    export_p.set_defaults(func=cmd_export_catalog)

    burn_p = sub.add_parser("burn", help="write a generated disc.toc using cdrdao")
    burn_p.add_argument("toc")
    burn_p.add_argument("--device")
    burn_p.add_argument("--speed", type=int)
    burn_p.add_argument("--simulate", action="store_true")
    burn_p.set_defaults(func=cmd_burn)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
