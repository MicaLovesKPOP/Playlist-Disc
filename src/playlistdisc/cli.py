"""Command-line interface for the PDv1 draft toolkit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from .audit import assert_reference_audit, audit_encoding
from .bridge import read_bridge_jsonl, validate_bridge_transcript
from .cdrdao import cdrdao_preflight
from .catalog import (
    find_entry,
    iter_entries,
    iter_packs,
    load_json,
    load_yaml,
    validate_catalog,
)
from .compatibility import (
    iter_compatibility_profiles,
    validate_compatibility,
    write_compatibility_snapshot,
)
from .evolution import check_catalog_evolution
from .identity import PDIdentity, decode_track_durations
from .library import (
    catalog_entries,
    catalog_packs,
    library_snapshot,
    pack_by_slug,
    search_catalog,
)
from .local import (
    create_local_entry,
    find_local_entry,
    iter_local_entries,
    validate_local_library,
)
from .local_scan import scan_local_library, write_local_provider_index
from .mastering import build_bundle
from .resolver import load_provider_index, resolve_canonical_manifest
from .site import build_static_site, verify_static_site
from .testkit import build_test_kit, verify_test_kit
from .verify import verify_build


def _format_duration(seconds: float) -> str:
    rounded = round(seconds)
    if abs(seconds - rounded) < 1e-9:
        minutes, sec = divmod(rounded, 60)
        return f"{minutes}:{sec:02d}"
    minutes = int(seconds // 60)
    return f"{minutes}:{seconds - minutes * 60:05.2f}"


def _print_errors(errors: list[str]) -> None:
    for message in errors:
        print(message, file=sys.stderr)


def _parse_bindings(values: list[str]) -> dict[str, str]:
    bindings: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError("bindings must use PROVIDER=RESOURCE syntax")
        provider, resource = value.split("=", 1)
        provider = provider.strip()
        resource = resource.strip()
        if not provider or not resource:
            raise ValueError("bindings require a non-empty provider and resource")
        if provider in bindings:
            raise ValueError(f"duplicate binding for provider {provider!r}")
        bindings[provider] = resource
    if not bindings:
        raise ValueError("at least one --binding PROVIDER=RESOURCE is required")
    return bindings


def _validated_catalog(catalog: str | Path) -> bool:
    errors = validate_catalog(catalog)
    if not errors:
        return True
    _print_errors(errors)
    return False


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

    if args.local_library:
        errors = validate_local_library(args.local_library)
        if errors:
            _print_errors(errors)
            print("error: refusing to build from invalid local library", file=sys.stderr)
            return 1
        found_local = find_local_entry(args.local_library, ident)
        if found_local:
            _, entry = found_local
            title = title or entry.get("title")
            short_title = short_title or entry.get("short_title")

    if args.catalog:
        found = find_entry(args.catalog, ident)
        if found:
            _, entry = found
            title = title or entry.get("title")
            short_title = short_title or entry.get("short_title")
    if not title:
        title = ident.canonical
    output = Path(args.output or f"build/{ident.canonical}")
    build_bundle(
        ident,
        output,
        title=title,
        short_title=short_title,
        cd_text=not args.no_cdtext,
    )
    print(output)
    return 0


def cmd_verify_build(args: argparse.Namespace) -> int:
    report = verify_build(args.bundle)
    print(report.identity.machine_id)
    print("manifest: PASS")
    print("TOC: PASS")
    print("CD-TEXT: PASS" if report.cd_text_present else "CD-TEXT: OMITTED (intentional)")
    print(f"audio beacon: PASS ({report.beacon_frames} matching frames)")
    print("cross-channel identity: PASS")
    print(f"bundle SHA-256: {report.bundle_sha256}")
    return 0


def cmd_audit_encoding(args: argparse.Namespace) -> int:
    report = audit_encoding()
    assert_reference_audit(report)
    print(f"identities: {report.identities_checked:,}")
    print(
        "namespaces: "
        + ", ".join(f"{name}={count:,}" for name, count in report.namespace_counts.items())
    )
    print(
        f"duration extrema: {report.minimum_total_seconds}s "
        f"(PD1-{report.minimum_total_id}) .. "
        f"{report.maximum_total_seconds}s (PD1-{report.maximum_total_id})"
    )
    print(f"golden vector SHA-256: {report.vector_sha256}")
    print("reference mapping: PASS")
    return 0


def cmd_validate_catalog(args: argparse.Namespace) -> int:
    errors = validate_catalog(
        args.catalog,
        entry_schema_path=args.schema,
        manifest_schema_path=args.manifest_schema,
        pack_schema_path=args.pack_schema,
    )
    if errors:
        _print_errors(errors)
        return 1
    entry_count = sum(1 for _ in iter_entries(args.catalog))
    pack_count = sum(1 for _ in iter_packs(args.catalog))
    print(f"validated {entry_count} catalog entries and {pack_count} packs")
    return 0


def cmd_check_catalog_evolution(args: argparse.Namespace) -> int:
    errors = check_catalog_evolution(args.baseline, args.current)
    if errors:
        _print_errors(errors)
        return 1
    print("catalog evolution: PASS")
    return 0


def cmd_validate_compatibility(args: argparse.Namespace) -> int:
    errors = validate_compatibility(args.compatibility)
    if errors:
        _print_errors(errors)
        return 1
    count = sum(1 for _ in iter_compatibility_profiles(args.compatibility))
    print(f"validated {count} compatibility profiles")
    return 0


def cmd_export_compatibility(args: argparse.Namespace) -> int:
    errors = validate_compatibility(args.compatibility)
    if errors:
        _print_errors(errors)
        print("error: refusing to export invalid compatibility data", file=sys.stderr)
        return 1
    path = write_compatibility_snapshot(args.compatibility, args.output)
    print(path)
    return 0


def cmd_validate_provider_index(args: argparse.Namespace) -> int:
    try:
        index = load_provider_index(args.provider_index)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"provider index: PASS ({index['provider']}, {len(index['tracks'])} tracks)")
    return 0


def cmd_resolve_canonical(args: argparse.Namespace) -> int:
    if not _validated_catalog(args.catalog):
        print("error: refusing to resolve against invalid catalog", file=sys.stderr)
        return 1
    try:
        identity = PDIdentity.parse(args.id)
        found = find_entry(args.catalog, identity)
        if found is None:
            raise ValueError(f"catalog entry {identity.canonical} does not exist")
        _, entry = found
        if entry.get("definition", {}).get("type") != "canonical_manifest":
            raise ValueError("entry is not a canonical_manifest definition")
        manifest_path = Path(args.catalog) / entry["definition"]["manifest"]
        manifest = load_json(manifest_path)
        provider_index = load_provider_index(args.provider_index)
        plan = resolve_canonical_manifest(entry, manifest, provider_index)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    payload = plan.to_dict()
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
        print(output)
    else:
        print(encoded, end="")
    if args.require_complete and (plan.missing_count or plan.ambiguous_count):
        return 3
    return 0


def cmd_export_catalog(args: argparse.Namespace) -> int:
    if not _validated_catalog(args.catalog):
        print("error: refusing to export invalid catalog", file=sys.stderr)
        return 1

    payload = {
        "schema_version": 1,
        "format": "PDv1",
        "entries": catalog_entries(args.catalog),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"exported {len(payload['entries'])} entries to {output}")
    return 0


def cmd_export_library(args: argparse.Namespace) -> int:
    if not _validated_catalog(args.catalog):
        print("error: refusing to export invalid library", file=sys.stderr)
        return 1

    payload = library_snapshot(args.catalog)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"exported {len(payload['entries'])} entries and "
        f"{len(payload['packs'])} packs to {output}"
    )
    return 0


def cmd_search_catalog(args: argparse.Namespace) -> int:
    if not _validated_catalog(args.catalog):
        print("error: refusing to search invalid catalog", file=sys.stderr)
        return 1

    try:
        results = search_catalog(
            args.catalog,
            args.query,
            statuses=set(args.status) if args.status else None,
            tags=set(args.tag) if args.tag else None,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    for entry in results:
        tags = ",".join(entry.get("tags", []))
        print(f"{entry['id']}\t{entry['title']}\t{entry['status']}\t{tags}")
    return 0


def cmd_pack_list(args: argparse.Namespace) -> int:
    if not _validated_catalog(args.catalog):
        print("error: refusing to list packs from invalid catalog", file=sys.stderr)
        return 1

    packs = catalog_packs(args.catalog)
    if args.json:
        print(json.dumps(packs, indent=2))
        return 0

    for pack in packs:
        print(
            f"{pack['slug']}\t{pack['disc_count']}/{pack['capacity']}\t"
            f"{pack['status']}\t{pack['title']}"
        )
    return 0


def cmd_pack_show(args: argparse.Namespace) -> int:
    if not _validated_catalog(args.catalog):
        print("error: refusing to show pack from invalid catalog", file=sys.stderr)
        return 1

    pack = pack_by_slug(args.catalog, args.slug)
    if pack is None:
        print(f"error: pack {args.slug!r} does not exist", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(pack, indent=2))
        return 0

    print(f"{pack['title']} ({pack['disc_count']}/{pack['capacity']})")
    for slot in pack["slots"]:
        print(
            f"{slot['slot']:02d}\t{slot['id']}\t"
            f"{slot['short_title']}\t{slot['title']}"
        )
    return 0


def cmd_local_create(args: argparse.Namespace) -> int:
    try:
        bindings = _parse_bindings(args.binding)
        ident, path, _ = create_local_entry(
            args.library,
            title=args.title,
            short_title=args.short_title,
            bindings=bindings,
            preferred_id=args.id,
            order=args.order,
            start=args.start,
            repeat=args.repeat,
            tags=args.tag,
            notes=args.notes,
        )
    except (ValueError, FileExistsError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(ident.machine_id)
    print(path)
    return 0


def cmd_local_validate(args: argparse.Namespace) -> int:
    errors = validate_local_library(args.library)
    if errors:
        _print_errors(errors)
        return 1
    count = sum(1 for _ in iter_local_entries(args.library))
    print(f"validated {count} local/private entries")
    return 0


def cmd_local_list(args: argparse.Namespace) -> int:
    errors = validate_local_library(args.library)
    if errors:
        _print_errors(errors)
        print("error: refusing to list invalid local library", file=sys.stderr)
        return 1

    entries = [load_yaml(path) for path in iter_local_entries(args.library)]
    entries.sort(key=lambda item: item["id"])
    if args.json:
        print(json.dumps(entries, indent=2))
        return 0

    for entry in entries:
        providers = ",".join(sorted(entry["bindings"]))
        print(f"{entry['id']}\t{entry['title']}\t{providers}")
    return 0


def cmd_scan_local_library(args: argparse.Namespace) -> int:
    try:
        report = scan_local_library(args.root, recursive=not args.no_recursive)
        output = write_local_provider_index(report, args.output)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(output)
    print(
        f"scanned={report.scanned_files} indexed={report.indexed_files} "
        f"unidentified={report.unidentified_files} unreadable={report.unreadable_files}"
    )
    if args.show_errors:
        for message in report.unreadable:
            print(message, file=sys.stderr)
    if args.strict and (report.unidentified_files or report.unreadable_files):
        return 3
    return 0


def cmd_build_site(args: argparse.Namespace) -> int:
    try:
        output = build_static_site(args.catalog, args.output)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(output)
    return 0


def cmd_verify_site(args: argparse.Namespace) -> int:
    errors = verify_static_site(args.site)
    if errors:
        _print_errors(errors)
        return 1
    print("static site: PASS")
    return 0


def cmd_bridge_validate(args: argparse.Namespace) -> int:
    try:
        messages = read_bridge_jsonl(args.transcript)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    errors = validate_bridge_transcript(messages)
    if errors:
        _print_errors(errors)
        return 1
    print(f"validated {len(messages)} bridge messages")
    return 0


def cmd_build_test_kit(args: argparse.Namespace) -> int:
    try:
        output = build_test_kit(args.output)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(output)
    return 0


def cmd_verify_test_kit(args: argparse.Namespace) -> int:
    errors = verify_test_kit(args.kit)
    if errors:
        _print_errors(errors)
        return 1
    print("test kit: PASS")
    return 0


def cmd_cdrdao_preflight(args: argparse.Namespace) -> int:
    try:
        report = cdrdao_preflight(args.target, executable=args.executable)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"cdrdao parser: PASS ({report.toc})")
    if args.verbose:
        if report.toc_info:
            print(report.toc_info)
        if report.toc_size:
            print(report.toc_size)
    return 0


def cmd_burn(args: argparse.Namespace) -> int:
    toc = Path(args.toc)
    if not toc.exists():
        print(f"error: {toc} does not exist", file=sys.stderr)
        return 2
    try:
        report = verify_build(toc.parent)
    except (OSError, ValueError) as exc:
        print(
            f"error: refusing to burn an unverified mastering bundle: {exc}",
            file=sys.stderr,
        )
        return 2
    if report.identity.namespace != "test":
        print(
            "error: Draft 0.2 burning is restricted to development/test IDs "
            "999900-999999; public/private builds remain virtual until PDv1.0",
            file=sys.stderr,
        )
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
    build_p.add_argument(
        "--local-library",
        help="optional local/private registry used to resolve title metadata",
    )
    build_p.add_argument("--output")
    build_p.add_argument(
        "--no-cdtext",
        action="store_true",
        help="omit optional CD-TEXT while preserving the same physical PD identity",
    )
    build_p.set_defaults(func=cmd_build)

    verify_p = sub.add_parser(
        "verify-build",
        help="independently verify TOC, CD-TEXT, manifest, and beacon in a generated bundle",
    )
    verify_p.add_argument("bundle")
    verify_p.set_defaults(func=cmd_verify_build)

    audit_p = sub.add_parser(
        "audit-encoding",
        help="exhaustively round-trip all 1,000,000 Draft 0.2 identities",
    )
    audit_p.set_defaults(func=cmd_audit_encoding)

    val_p = sub.add_parser(
        "validate-catalog",
        help="validate registry schemas, packs, and cross-file invariants",
    )
    val_p.add_argument("catalog", nargs="?", default="catalog")
    val_p.add_argument("--schema")
    val_p.add_argument("--manifest-schema")
    val_p.add_argument("--pack-schema")
    val_p.set_defaults(func=cmd_validate_catalog)

    evolution_p = sub.add_parser(
        "check-catalog-evolution",
        help="compare a baseline catalog with the current catalog and protect activated public IDs",
    )
    evolution_p.add_argument("baseline")
    evolution_p.add_argument("current", nargs="?", default="catalog")
    evolution_p.set_defaults(func=cmd_check_catalog_evolution)

    compat_validate_p = sub.add_parser(
        "validate-compatibility",
        help="validate structured vehicle/head-unit compatibility profiles and test reports",
    )
    compat_validate_p.add_argument("compatibility", nargs="?", default="compatibility")
    compat_validate_p.set_defaults(func=cmd_validate_compatibility)

    compat_export_p = sub.add_parser(
        "export-compatibility",
        help="export a deterministic compatibility JSON snapshot",
    )
    compat_export_p.add_argument("compatibility", nargs="?", default="compatibility")
    compat_export_p.add_argument("--output", default="build/compatibility.json")
    compat_export_p.set_defaults(func=cmd_export_compatibility)

    provider_validate_p = sub.add_parser(
        "validate-provider-index",
        help="validate an offline provider/local-library resolution index",
    )
    provider_validate_p.add_argument("provider_index")
    provider_validate_p.set_defaults(func=cmd_validate_provider_index)

    resolve_p = sub.add_parser(
        "resolve-canonical",
        help="resolve one canonical manifest against a provider/local-library index",
    )
    resolve_p.add_argument("id")
    resolve_p.add_argument("--catalog", default="catalog")
    resolve_p.add_argument("--provider-index", required=True)
    resolve_p.add_argument("--output")
    resolve_p.add_argument("--require-complete", action="store_true")
    resolve_p.set_defaults(func=cmd_resolve_canonical)

    export_p = sub.add_parser("export-catalog", help="build a validated generated JSON catalog snapshot")
    export_p.add_argument("catalog", nargs="?", default="catalog")
    export_p.add_argument("--output", default="build/catalog.json")
    export_p.set_defaults(func=cmd_export_catalog)

    library_p = sub.add_parser(
        "export-library",
        help="build a static-library JSON snapshot containing entries, packs, and facets",
    )
    library_p.add_argument("catalog", nargs="?", default="catalog")
    library_p.add_argument("--output", default="build/library.json")
    library_p.set_defaults(func=cmd_export_library)

    search_p = sub.add_parser(
        "search-catalog",
        help="search validated catalog metadata using AND-token matching",
    )
    search_p.add_argument("query")
    search_p.add_argument("--catalog", default="catalog")
    search_p.add_argument("--status", action="append", choices=["draft", "active", "retired"])
    search_p.add_argument("--tag", action="append", default=[])
    search_p.add_argument("--json", action="store_true")
    search_p.set_defaults(func=cmd_search_catalog)

    pack_list_p = sub.add_parser("pack-list", help="list validated catalog packs")
    pack_list_p.add_argument("catalog", nargs="?", default="catalog")
    pack_list_p.add_argument("--json", action="store_true")
    pack_list_p.set_defaults(func=cmd_pack_list)

    pack_show_p = sub.add_parser("pack-show", help="show ordered wallet slots for one pack")
    pack_show_p.add_argument("slug")
    pack_show_p.add_argument("--catalog", default="catalog")
    pack_show_p.add_argument("--json", action="store_true")
    pack_show_p.set_defaults(func=cmd_pack_show)

    local_create_p = sub.add_parser(
        "local-create",
        help="allocate a private ID and create a local-only playback mapping",
    )
    local_create_p.add_argument("library")
    local_create_p.add_argument("--id", help="specific private ID; default is lowest free ID")
    local_create_p.add_argument("--title", required=True)
    local_create_p.add_argument("--short-title", required=True)
    local_create_p.add_argument(
        "--binding",
        action="append",
        default=[],
        metavar="PROVIDER=RESOURCE",
        help="repeat for each local provider/resource mapping",
    )
    local_create_p.add_argument("--order", choices=["ordered", "shuffle"], default="ordered")
    local_create_p.add_argument("--start", choices=["first", "random", "resume"], default="first")
    local_create_p.add_argument("--repeat", choices=["off", "context", "one"], default="context")
    local_create_p.add_argument("--tag", action="append", default=[])
    local_create_p.add_argument("--notes")
    local_create_p.set_defaults(func=cmd_local_create)

    local_validate_p = sub.add_parser(
        "local-validate", help="validate a local/private registry"
    )
    local_validate_p.add_argument("library")
    local_validate_p.set_defaults(func=cmd_local_validate)

    local_list_p = sub.add_parser("local-list", help="list local/private disc mappings")
    local_list_p.add_argument("library")
    local_list_p.add_argument("--json", action="store_true")
    local_list_p.set_defaults(func=cmd_local_list)

    local_scan_p = sub.add_parser(
        "scan-local-library",
        help="build a provider=local index from MusicBrainz/ISRC-tagged audio files",
    )
    local_scan_p.add_argument("root")
    local_scan_p.add_argument("--output", default="build/local-provider-index.json")
    local_scan_p.add_argument("--no-recursive", action="store_true")
    local_scan_p.add_argument("--show-errors", action="store_true")
    local_scan_p.add_argument(
        "--strict",
        action="store_true",
        help="return exit code 3 when any candidate file is unidentified or unreadable",
    )
    local_scan_p.set_defaults(func=cmd_scan_local_library)

    site_build_p = sub.add_parser(
        "build-site",
        help="build a dependency-free static HTML library from the validated catalog",
    )
    site_build_p.add_argument("catalog", nargs="?", default="catalog")
    site_build_p.add_argument("--output", default="build/site")
    site_build_p.set_defaults(func=cmd_build_site)

    site_verify_p = sub.add_parser(
        "verify-site",
        help="verify generated static-site structure and internal links",
    )
    site_verify_p.add_argument("site", nargs="?", default="build/site")
    site_verify_p.set_defaults(func=cmd_verify_site)

    bridge_validate_p = sub.add_parser(
        "bridge-validate",
        help="validate a PD Bridge JSONL transcript and state invariants",
    )
    bridge_validate_p.add_argument("transcript")
    bridge_validate_p.set_defaults(func=cmd_bridge_validate)

    kit_build_p = sub.add_parser(
        "build-test-kit",
        help="generate the Draft 0.2 physical compatibility test bundles",
    )
    kit_build_p.add_argument("--output", default="build/test-kit")
    kit_build_p.set_defaults(func=cmd_build_test_kit)

    kit_verify_p = sub.add_parser(
        "verify-test-kit",
        help="verify every generated Draft 0.2 compatibility-test bundle",
    )
    kit_verify_p.add_argument("kit", nargs="?", default="build/test-kit")
    kit_verify_p.set_defaults(func=cmd_verify_test_kit)

    cdrdao_p = sub.add_parser(
        "cdrdao-preflight",
        help="verify a bundle and parse/size its TOC with the installed cdrdao tool",
    )
    cdrdao_p.add_argument("target", help="bundle directory or disc.toc path")
    cdrdao_p.add_argument(
        "--executable",
        help="explicit cdrdao executable path/name; default searches PATH",
    )
    cdrdao_p.add_argument("--verbose", action="store_true")
    cdrdao_p.set_defaults(func=cmd_cdrdao_preflight)

    burn_p = sub.add_parser("burn", help="write a verified Draft test disc using cdrdao")
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
