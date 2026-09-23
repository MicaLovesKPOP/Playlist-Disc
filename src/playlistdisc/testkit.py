"""Generate the deterministic PDv1 Draft 0.2 physical compatibility test kit."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

from .identity import DRAFT_VERSION, FORMAT_NAME, PDIdentity
from .mastering import build_bundle
from .verify import bundle_fingerprint, verify_build

TEST_KIT_FORMAT = "PDv1-test-kit"


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


def _expected_variant_record(variant: TestVariant) -> dict[str, Any]:
    identity = PDIdentity(variant.id_number)
    return {
        **asdict(variant),
        "id": identity.canonical,
        "machine_id": identity.machine_id,
        "bundle": (Path("variants") / variant.name).as_posix(),
    }


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
                    **_expected_variant_record(variant),
                    "bundle_sha256": report.bundle_sha256,
                }
            )

        manifest = {
            "format": TEST_KIT_FORMAT,
            "physical_format": FORMAT_NAME,
            "draft": DRAFT_VERSION,
            "variants": records,
        }
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

        variant = VARIANTS[index]
        expected = _expected_variant_record(variant)
        for field, expected_value in expected.items():
            if item.get(field) != expected_value:
                errors.append(
                    f"{name}: {field} disagrees with Draft {DRAFT_VERSION} test-kit reference"
                )

        # Verification deliberately follows the immutable reference path rather
        # than a mutable path supplied by test-kit.json. This prevents a
        # self-consistent manifest edit from silently repointing one named test
        # vector at another valid bundle.
        bundle = (base / expected["bundle"]).resolve()
        try:
            bundle.relative_to(base.resolve())
        except ValueError:
            errors.append(f"{name}: reference bundle path escapes test kit")
            continue
        try:
            report = verify_build(bundle)
        except (OSError, ValueError) as exc:
            errors.append(f"{name}: {exc}")
            continue

        expected_identity = PDIdentity(variant.id_number)
        if report.identity != expected_identity:
            errors.append(f"{name}: bundle identity disagrees with test-kit reference")
        if report.cd_text_present is not variant.cd_text:
            errors.append(f"{name}: CD-TEXT mode disagrees with test-kit reference")

        expected_fingerprint = item.get("bundle_sha256")
        if not isinstance(expected_fingerprint, str):
            errors.append(f"{name}: bundle_sha256 missing")
        elif expected_fingerprint != bundle_fingerprint(bundle):
            errors.append(f"{name}: bundle SHA-256 disagrees with test-kit manifest")

    return errors
