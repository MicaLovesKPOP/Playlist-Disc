"""Generate the deterministic PDv1 Draft 0.2 physical compatibility test kit."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

from .identity import DRAFT_VERSION, FORMAT_NAME, PDIdentity
from .mastering import build_bundle
from .verify import verify_build

TEST_KIT_FORMAT = "PDv1-test-kit"
ARTIFACT_NAMES = ("beacon.wav", "disc.toc", "manifest.json")


@dataclass(frozen=True, slots=True)
class TestVariant:
    name: str
    id_number: int
    title: str
    short_title: str
    cd_text: bool
    purpose: str


VARIANTS: tuple[TestVariant, ...] = (
    TestVariant(
        name="toc-cdtext",
        id_number=999901,
        title="PDv1 TOC lattice test",
        short_title="PDV1 TOC",
        cd_text=True,
        purpose="Baseline TOC recognition with optional CD-TEXT present.",
    ),
    TestVariant(
        name="toc-no-cdtext",
        id_number=999901,
        title="PDv1 TOC lattice test",
        short_title="PDV1 TOC",
        cd_text=False,
        purpose=(
            "Same physical PD identity as toc-cdtext but without CD-TEXT, "
            "isolating metadata compatibility."
        ),
    ),
    TestVariant(
        name="beacon-no-cdtext",
        id_number=999902,
        title="PDv1 audio beacon test",
        short_title="PDV1 BEACON",
        cd_text=False,
        purpose=(
            "Audio-beacon fallback test without CD-TEXT. TOC remains present "
            "because it is fundamental to every audio CD."
        ),
    ),
    TestVariant(
        name="cdtext",
        id_number=999903,
        title="PDv1 CD-TEXT test",
        short_title="PDV1 CDTEXT",
        cd_text=True,
        purpose="Dedicated CD-TEXT/display behavior observation.",
    ),
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_records(bundle: Path) -> dict[str, dict[str, int | str]]:
    records: dict[str, dict[str, int | str]] = {}
    for name in ARTIFACT_NAMES:
        path = bundle / name
        if not path.is_file():
            raise ValueError(f"generated bundle is missing required artifact: {name}")
        records[name] = {
            "bytes": path.stat().st_size,
            "sha256": _sha256_file(path),
        }
    return records


def _manifest_fingerprint(manifest: dict[str, Any]) -> str:
    payload = json.dumps(
        manifest,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_test_kit(output_dir: str | Path) -> Path:
    output = Path(output_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output.name}-", dir=str(output.parent))
    )
    try:
        records: list[dict[str, Any]] = []
        for variant in VARIANTS:
            identity = PDIdentity(variant.id_number)
            bundle_rel = Path("variants") / variant.name
            bundle = staging / bundle_rel
            build_bundle(
                identity,
                bundle,
                title=variant.title,
                short_title=variant.short_title,
                cd_text=variant.cd_text,
            )
            report = verify_build(bundle)
            if not report.ok:
                raise ValueError(f"generated variant {variant.name} failed verification")
            records.append(
                {
                    **asdict(variant),
                    "id": identity.canonical,
                    "machine_id": identity.machine_id,
                    "bundle": bundle_rel.as_posix(),
                    "artifacts": _artifact_records(bundle),
                }
            )

        manifest: dict[str, Any] = {
            "format": TEST_KIT_FORMAT,
            "physical_format": FORMAT_NAME,
            "draft": DRAFT_VERSION,
            "variants": records,
        }
        manifest["content_sha256"] = _manifest_fingerprint(manifest)
        (staging / "test-kit.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )

        verify_errors = verify_test_kit(staging)
        if verify_errors:
            raise ValueError(
                "generated test kit failed verification: " + "; ".join(verify_errors)
            )

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


def _expected_variant_record(variant: TestVariant) -> dict[str, Any]:
    identity = PDIdentity(variant.id_number)
    return {
        **asdict(variant),
        "id": identity.canonical,
        "machine_id": identity.machine_id,
        "bundle": (Path("variants") / variant.name).as_posix(),
    }


def _verify_artifacts(name: str, bundle: Path, value: object) -> list[str]:
    if not isinstance(value, dict):
        return [f"{name}: artifacts must be an object"]

    errors: list[str] = []
    if set(value) != set(ARTIFACT_NAMES):
        errors.append(
            f"{name}: artifact names must be exactly {list(ARTIFACT_NAMES)!r}"
        )

    for artifact_name in ARTIFACT_NAMES:
        expected = value.get(artifact_name)
        if not isinstance(expected, dict):
            errors.append(f"{name}: missing artifact record for {artifact_name}")
            continue
        if set(expected) != {"bytes", "sha256"}:
            errors.append(
                f"{name}: {artifact_name} record must contain only bytes and sha256"
            )
            continue

        expected_bytes = expected.get("bytes")
        expected_sha = expected.get("sha256")
        if not isinstance(expected_bytes, int) or expected_bytes < 0:
            errors.append(f"{name}: {artifact_name} bytes must be a non-negative integer")
            continue
        if (
            not isinstance(expected_sha, str)
            or len(expected_sha) != 64
            or any(ch not in "0123456789abcdef" for ch in expected_sha)
        ):
            errors.append(f"{name}: {artifact_name} sha256 must be lowercase hex")
            continue

        path = bundle / artifact_name
        if not path.is_file():
            errors.append(f"{name}: missing artifact {artifact_name}")
            continue
        if path.stat().st_size != expected_bytes:
            errors.append(f"{name}: {artifact_name} byte size disagrees with manifest")
        if _sha256_file(path) != expected_sha:
            errors.append(f"{name}: {artifact_name} SHA-256 disagrees with manifest")

    return errors


def verify_test_kit(root: str | Path) -> list[str]:
    base = Path(root)
    path = base / "test-kit.json"
    errors: list[str] = []
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"test-kit.json: {exc}"]

    if not isinstance(manifest, dict):
        return ["test-kit.json: expected JSON object"]
    if manifest.get("format") != TEST_KIT_FORMAT:
        errors.append(f"test-kit.json: format must be {TEST_KIT_FORMAT!r}")
    if manifest.get("physical_format") != FORMAT_NAME:
        errors.append(f"test-kit.json: physical_format must be {FORMAT_NAME!r}")
    if manifest.get("draft") != DRAFT_VERSION:
        errors.append(f"test-kit.json: draft must be {DRAFT_VERSION!r}")

    supplied_fingerprint = manifest.get("content_sha256")
    if (
        not isinstance(supplied_fingerprint, str)
        or len(supplied_fingerprint) != 64
        or any(ch not in "0123456789abcdef" for ch in supplied_fingerprint)
    ):
        errors.append("test-kit.json: content_sha256 must be lowercase hex")
    else:
        unsigned_manifest = dict(manifest)
        unsigned_manifest.pop("content_sha256", None)
        if _manifest_fingerprint(unsigned_manifest) != supplied_fingerprint:
            errors.append("test-kit.json: content_sha256 disagrees with manifest content")

    variants = manifest.get("variants")
    if not isinstance(variants, list):
        return errors + ["test-kit.json: variants must be a list"]

    expected_names = [variant.name for variant in VARIANTS]
    actual_names = [item.get("name") for item in variants if isinstance(item, dict)]
    if actual_names != expected_names or len(variants) != len(VARIANTS):
        errors.append(
            f"test-kit.json: variant order/names disagree with reference {expected_names!r}"
        )

    for index, item in enumerate(variants):
        if not isinstance(item, dict):
            errors.append(f"variant {index}: expected object")
            continue
        name = str(item.get("name", f"#{index}"))
        if index >= len(VARIANTS):
            continue
        expected = _expected_variant_record(VARIANTS[index])
        for field, expected_value in expected.items():
            if item.get(field) != expected_value:
                errors.append(
                    f"{name}: {field} disagrees with Draft {DRAFT_VERSION} test-kit reference"
                )

        bundle_value = item.get("bundle")
        if not isinstance(bundle_value, str):
            errors.append(f"{name}: bundle path missing")
            continue
        bundle = (base / bundle_value).resolve()
        try:
            bundle.relative_to(base.resolve())
        except ValueError:
            errors.append(f"{name}: bundle path escapes test kit")
            continue

        errors.extend(_verify_artifacts(name, bundle, item.get("artifacts")))

        try:
            report = verify_build(bundle)
        except (OSError, ValueError) as exc:
            errors.append(f"{name}: {exc}")
            continue

        expected_identity = PDIdentity(VARIANTS[index].id_number)
        if report.identity != expected_identity:
            errors.append(f"{name}: bundle identity disagrees with test-kit reference")
        if report.cd_text_present is not VARIANTS[index].cd_text:
            errors.append(f"{name}: CD-TEXT mode disagrees with test-kit reference")

    return errors
