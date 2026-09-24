import json
from pathlib import Path

import yaml

from playlistdisc.compatibility import (
    compatibility_snapshot,
    validate_compatibility,
    validate_compatibility_profile,
)
from playlistdisc.catalog import load_schema

ROOT = Path(__file__).parents[1]
COMPAT = ROOT / "compatibility"
SCHEMA = load_schema(COMPAT / "schema/profile.schema.json")


def _base_profile() -> dict:
    return {
        "schema_version": 1,
        "profile_id": "test-radio",
        "status": "planned",
        "vehicle": {"make": "Example", "model": "Car"},
        "audio_system": {"head_unit": "Example Radio", "controls": ["head_unit"]},
        "test_plan": ["cd_r", "cold_start_inserted"],
        "reports": [],
    }


def _report() -> dict:
    return {
        "report_id": "first-test",
        "date": "2026-09-23",
        "disc_machine_id": "PD1-999901-7",
        "bundle_sha256": "0" * 64,
        "media": {"type": "cd_r", "finalized": True, "cd_text": True},
        "write": {"mode": "dao"},
        "attempts": {"total": 3, "successful_loads": 3},
        "results": {
            "load": "pass",
            "tracks": "pass",
            "toc_duration": "exact",
            "cd_text": "displayed",
            "cold_start": "pass",
            "reinsert": "pass",
            "vehicle_bus_toc": "not_tested",
            "audio_beacon": "not_tested",
        },
    }


def test_repository_compatibility_profiles_validate():
    assert validate_compatibility(COMPAT) == []


def test_planned_profile_cannot_contain_results():
    profile = _base_profile()
    profile["reports"] = [_report()]
    errors = validate_compatibility_profile(profile, SCHEMA)
    assert any("planned profile cannot already contain" in error for error in errors)


def test_partial_profile_requires_report_and_valid_test_id():
    profile = _base_profile()
    profile["status"] = "partial"
    assert any("requires at least one test report" in error for error in validate_compatibility_profile(profile, SCHEMA))

    profile["reports"] = [_report()]
    profile["reports"][0]["disc_machine_id"] = "PD1-123456-3"
    errors = validate_compatibility_profile(profile, SCHEMA)
    assert any("development/test namespace" in error for error in errors)


def test_test_variant_pins_reference_identity_and_cdtext_semantics():
    profile = _base_profile()
    profile["status"] = "partial"

    report = _report()
    report["test_variant"] = "toc-cdtext"
    profile["reports"] = [report]
    assert validate_compatibility_profile(profile, SCHEMA) == []

    wrong_identity = _report()
    wrong_identity["test_variant"] = "toc-cdtext"
    wrong_identity["disc_machine_id"] = "PD1-999902-5"
    profile["reports"] = [wrong_identity]
    errors = validate_compatibility_profile(profile, SCHEMA)
    assert any("does not match test variant" in error for error in errors)

    wrong_cdtext = _report()
    wrong_cdtext["test_variant"] = "toc-cdtext"
    wrong_cdtext["media"]["cd_text"] = False
    profile["reports"] = [wrong_cdtext]
    errors = validate_compatibility_profile(profile, SCHEMA)
    assert any("media.cd_text" in error and "test variant" in error for error in errors)

    unknown = _report()
    unknown["test_variant"] = "made-up-variant"
    profile["reports"] = [unknown]
    errors = validate_compatibility_profile(profile, SCHEMA)
    assert any("unknown Draft 0.2 test-kit variant" in error for error in errors)


def test_attempt_successes_cannot_exceed_attempts():
    profile = _base_profile()
    profile["status"] = "partial"
    report = _report()
    report["attempts"] = {"total": 2, "successful_loads": 3}
    profile["reports"] = [report]
    errors = validate_compatibility_profile(profile, SCHEMA)
    assert any("successful_loads cannot exceed total" in error for error in errors)




def test_physical_report_requires_valid_bundle_fingerprint():
    profile = _base_profile()
    profile["status"] = "partial"
    report = _report()
    report["bundle_sha256"] = "not-a-sha256"
    profile["reports"] = [report]
    errors = validate_compatibility_profile(profile, SCHEMA)
    assert any("bundle_sha256" in error for error in errors)

def test_snapshot_is_deterministic_and_counts_profiles():
    first = compatibility_snapshot(COMPAT)
    second = compatibility_snapshot(COMPAT)
    assert first == second
    assert first["format"] == "PDv1-compatibility"
    assert first["summary"]["profile_count"] == 3
    assert first["summary"]["report_count"] == 0
    source_count = sum(
        len(
            (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get(
                "research_evidence", []
            )
        )
        for path in sorted((COMPAT / "vehicles").glob("*.yaml"))
    )
    assert source_count >= 8
    assert first["summary"]["research_evidence_count"] == source_count
    assert first["summary"]["statuses"]["planned"] == 3



def _research_evidence() -> dict:
    return {
        "topic": "cd_changer",
        "claim": "A documented changer interface exists.",
        "implication": "Treat it as planning evidence until the target unit is tested.",
        "source": {
            "source_type": "component_vendor",
            "title": "Example interface",
            "publisher": "Example Vendor",
            "url": "https://example.test/interface",
            "accessed": "2026-09-23",
        },
    }


def test_planned_profile_accepts_documentation_research_without_becoming_tested():
    profile = _base_profile()
    profile["research_evidence"] = [_research_evidence()]
    assert validate_compatibility_profile(profile, SCHEMA) == []


def test_research_evidence_requires_https_source():
    profile = _base_profile()
    evidence = _research_evidence()
    evidence["source"]["url"] = "http://example.test/interface"
    profile["research_evidence"] = [evidence]
    errors = validate_compatibility_profile(profile, SCHEMA)
    assert any("research_evidence.0.source.url" in error for error in errors)
