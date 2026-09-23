import copy
from pathlib import Path

import pytest

from playlistdisc.materialization import (
    compare_materialization,
    make_materialization_record,
    materialization_path,
    plan_fingerprint,
    read_materialization,
    scope_fingerprint,
    validate_materialization_record,
    write_materialization,
)


def _plan() -> dict:
    return {
        "schema_version": 1,
        "format": "PDv1-playback-plan",
        "disc_id": "042381",
        "machine_id": "PD1-042381-8",
        "title": "Canonical test collection",
        "provider": "demo",
        "status": "ready",
        "mode": "track_list",
        "resources": ["demo:a", "demo:b"],
        "playback": {"order": "shuffle", "start": "random", "repeat": "context"},
    }


def test_plan_and_scope_fingerprints_are_deterministic():
    first = _plan()
    second = copy.deepcopy(first)
    second["playback"] = {
        "repeat": "context",
        "start": "random",
        "order": "shuffle",
    }
    assert plan_fingerprint(first) == plan_fingerprint(second)
    assert scope_fingerprint("default") == scope_fingerprint("default")
    assert scope_fingerprint("default") != scope_fingerprint("other")


def test_materialization_record_roundtrip(tmp_path: Path):
    plan = _plan()
    path = write_materialization(
        tmp_path,
        plan,
        scope="account-a",
        materialized_resource="demo:playlist:generated",
        provider_revision="rev-1",
    )
    assert path == materialization_path(tmp_path, plan, "account-a")
    record, reasons = read_materialization(tmp_path, plan, scope="account-a")
    assert reasons == []
    assert record is not None
    assert record["materialized_resource"] == "demo:playlist:generated"
    assert record["provider_revision"] == "rev-1"
    assert validate_materialization_record(record) == []


def test_plan_change_invalidates_cached_materialization(tmp_path: Path):
    plan = _plan()
    write_materialization(
        tmp_path,
        plan,
        scope="account-a",
        materialized_resource="demo:playlist:generated",
    )
    changed = copy.deepcopy(plan)
    changed["resources"].append("demo:c")
    record, reasons = read_materialization(tmp_path, changed, scope="account-a")
    assert record is None
    assert any("plan_sha256" in reason for reason in reasons)
    assert any("source_count" in reason for reason in reasons)


def test_playback_policy_change_invalidates_cache():
    plan = _plan()
    record = make_materialization_record(
        plan,
        scope="account-a",
        materialized_resource="demo:playlist:generated",
    )
    changed = copy.deepcopy(plan)
    changed["playback"]["order"] = "ordered"
    reasons = compare_materialization(record, changed, scope="account-a")
    assert any("plan_sha256" in reason for reason in reasons)


def test_account_scope_does_not_leak_plaintext_into_path(tmp_path: Path):
    plan = _plan()
    scope = "mica@example.test"
    path = materialization_path(tmp_path, plan, scope)
    assert scope not in str(path)
    assert scope_fingerprint(scope) in str(path)


def test_different_scope_is_a_cache_miss(tmp_path: Path):
    plan = _plan()
    write_materialization(
        tmp_path,
        plan,
        scope="account-a",
        materialized_resource="demo:playlist:generated",
    )
    record, reasons = read_materialization(tmp_path, plan, scope="account-b")
    assert record is None
    assert reasons == ["cache record does not exist"]


def test_non_track_list_plans_are_not_materialized():
    plan = _plan()
    plan["mode"] = "direct_resource"
    plan.pop("resources")
    plan["resource"] = "demo:playlist:already-existing"
    with pytest.raises(ValueError, match="only deterministic track_list"):
        make_materialization_record(
            plan,
            scope="account-a",
            materialized_resource="demo:playlist:generated",
        )


def test_partial_track_list_can_be_cached_and_invalidates_when_coverage_changes():
    plan = _plan()
    plan["status"] = "partial"
    plan["reason"] = "one canonical recording missing"
    record = make_materialization_record(
        plan,
        scope="account-a",
        materialized_resource="demo:playlist:partial",
    )
    assert record["plan_status"] == "partial"

    improved = copy.deepcopy(plan)
    improved["status"] = "ready"
    improved.pop("reason")
    improved["resources"].append("demo:c")
    reasons = compare_materialization(record, improved, scope="account-a")
    assert reasons
