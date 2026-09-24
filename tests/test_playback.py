from playlistdisc.playback import (
    compile_catalog_playback,
    compile_local_playback,
    validate_playback_plan,
)


def _entry(definition: dict, *, providers: dict | None = None) -> dict:
    data = {
        "id": "042381",
        "title": "Test collection",
        "definition": definition,
        "playback": {"order": "shuffle", "start": "random", "repeat": "context"},
    }
    if providers is not None:
        data["providers"] = providers
    return data


def _manifest() -> dict:
    return {
        "schema_version": 1,
        "disc_id": "042381",
        "recordings": [
            {
                "musicbrainz_recording_id": "11111111-2222-3333-4444-555555555555",
                "title_hint": "A",
            },
            {"isrcs": ["KRABC2600002"], "title_hint": "B"},
        ],
    }


def test_canonical_manifest_without_index_requires_resolution():
    entry = _entry(
        {
            "type": "canonical_manifest",
            "manifest": "manifests/042/042381.json",
            "membership_policy": "Exact set.",
        }
    )
    plan = compile_catalog_playback(entry, "demo", manifest=_manifest())
    assert plan.status == "requires_lookup"
    assert plan.mode == "recording_resolution"
    assert plan.lookup == {
        "type": "canonical_manifest",
        "recording_count": 2,
        "recordings": [
            {
                "musicbrainz_recording_id": "11111111-2222-3333-4444-555555555555"
            },
            {"isrcs": ["KRABC2600002"]},
        ],
    }
    assert validate_playback_plan(plan.to_dict()) == []


def test_canonical_manifest_compiles_ready_track_list():
    entry = _entry(
        {
            "type": "canonical_manifest",
            "manifest": "manifests/042/042381.json",
            "membership_policy": "Exact set.",
        }
    )
    index = {
        "schema_version": 1,
        "provider": "demo",
        "tracks": [
            {
                "resource": "demo:a",
                "musicbrainz_recording_id": "11111111-2222-3333-4444-555555555555",
            },
            {"resource": "demo:b", "isrcs": ["KRABC2600002"]},
        ],
    }
    plan = compile_catalog_playback(
        entry, "demo", manifest=_manifest(), provider_index=index
    )
    assert plan.status == "ready"
    assert plan.mode == "track_list"
    assert plan.resources == ("demo:a", "demo:b")
    assert plan.resolution["coverage"] == 1.0


def test_canonical_manifest_reports_partial_and_ambiguous():
    entry = _entry(
        {
            "type": "canonical_manifest",
            "manifest": "manifests/042/042381.json",
            "membership_policy": "Exact set.",
        }
    )
    partial = {
        "schema_version": 1,
        "provider": "demo",
        "tracks": [
            {
                "resource": "demo:a",
                "musicbrainz_recording_id": "11111111-2222-3333-4444-555555555555",
            }
        ],
    }
    plan = compile_catalog_playback(
        entry, "demo", manifest=_manifest(), provider_index=partial
    )
    assert plan.status == "partial"
    assert plan.resources == ("demo:a",)

    ambiguous = {
        "schema_version": 1,
        "provider": "demo",
        "tracks": [
            {
                "resource": "demo:a1",
                "musicbrainz_recording_id": "11111111-2222-3333-4444-555555555555",
            },
            {
                "resource": "demo:a2",
                "musicbrainz_recording_id": "11111111-2222-3333-4444-555555555555",
            },
            {"resource": "demo:b", "isrcs": ["KRABC2600002"]},
        ],
    }
    plan = compile_catalog_playback(
        entry, "demo", manifest=_manifest(), provider_index=ambiguous
    )
    assert plan.status == "ambiguous"
    assert plan.resources == ("demo:b",)


def test_provider_native_only_works_on_native_provider():
    entry = _entry(
        {"type": "provider_native", "provider": "spotify"},
        providers={
            "spotify": {
                "strategy": "direct",
                "resource": "spotify:playlist:abc",
            }
        },
    )
    ready = compile_catalog_playback(entry, "spotify")
    assert ready.status == "ready"
    assert ready.resource == "spotify:playlist:abc"

    unavailable = compile_catalog_playback(entry, "apple_music")
    assert unavailable.status == "unavailable"
    assert "spotify" in unavailable.reason


def test_federated_provider_uses_selected_equivalent_resource():
    entry = _entry(
        {
            "type": "federated_collection",
            "concept": "Current provider pop hits.",
        },
        providers={
            "spotify": {
                "strategy": "equivalent",
                "resource": "spotify:playlist:hits",
            },
            "apple_music": {
                "strategy": "best_available",
                "resource": "apple:playlist:hits",
            },
        },
    )
    plan = compile_catalog_playback(entry, "apple_music")
    assert plan.status == "ready"
    assert plan.strategy == "best_available"
    assert plan.resource == "apple:playlist:hits"


def test_artist_and_album_fall_back_to_service_neutral_entity_lookup():
    artist = _entry(
        {
            "type": "artist_catalog",
            "musicbrainz_artist_id": "11111111-2222-3333-4444-555555555555",
        }
    )
    artist_plan = compile_catalog_playback(artist, "demo")
    assert artist_plan.status == "requires_lookup"
    assert artist_plan.lookup["type"] == "artist"

    album = _entry(
        {
            "type": "album",
            "musicbrainz_release_group_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        }
    )
    album_plan = compile_catalog_playback(album, "demo")
    assert album_plan.status == "requires_lookup"
    assert album_plan.lookup["type"] == "release_group"


def test_diagnostic_entry_is_deliberately_unplayable():
    entry = _entry({"type": "diagnostic", "purpose": "test"})
    plan = compile_catalog_playback(entry, "demo")
    assert plan.status == "unplayable"
    assert plan.mode == "none"


def test_private_local_binding_uses_same_plan_contract():
    entry = {
        "id": "900000",
        "title": "Private favourites",
        "bindings": {"local": {"resource": "library:playlist:favourites"}},
        "playback": {"order": "shuffle", "start": "random", "repeat": "context"},
    }
    plan = compile_local_playback(entry, "local")
    assert plan.status == "ready"
    assert plan.mode == "direct_resource"
    assert plan.resource == "library:playlist:favourites"
    assert validate_playback_plan(plan.to_dict()) == []

    missing = compile_local_playback(entry, "spotify")
    assert missing.status == "unavailable"


def test_provider_index_must_match_requested_provider():
    entry = _entry(
        {
            "type": "canonical_manifest",
            "manifest": "manifests/042/042381.json",
            "membership_policy": "Exact set.",
        }
    )
    index = {"schema_version": 1, "provider": "other", "tracks": []}
    try:
        compile_catalog_playback(
            entry, "demo", manifest=_manifest(), provider_index=index
        )
    except ValueError as exc:
        assert "not requested provider" in str(exc)
    else:
        raise AssertionError("expected provider mismatch to fail")


def test_unresolved_canonical_plan_carries_selected_provider_override_only():
    entry = _entry(
        {
            "type": "canonical_manifest",
            "manifest": "manifests/042/042381.json",
            "membership_policy": "Exact set.",
        }
    )
    manifest = _manifest()
    manifest["recordings"][0]["provider_overrides"] = {
        "demo": "demo:track:override",
        "other": "other:track:secret",
    }
    plan = compile_catalog_playback(entry, "demo", manifest=manifest)
    row = plan.lookup["recordings"][0]
    assert row["provider_override"] == "demo:track:override"
    assert "other:track:secret" not in str(plan.to_dict())


def test_recording_resolution_plan_rejects_count_mismatch_and_duplicate_identity():
    entry = _entry(
        {
            "type": "canonical_manifest",
            "manifest": "manifests/042/042381.json",
            "membership_policy": "Exact set.",
        }
    )
    plan = compile_catalog_playback(entry, "demo", manifest=_manifest()).to_dict()

    bad_count = dict(plan)
    bad_count["lookup"] = dict(plan["lookup"])
    bad_count["lookup"]["recording_count"] = 999
    errors = validate_playback_plan(bad_count)
    assert any("recording_count" in error for error in errors)

    duplicate = dict(plan)
    duplicate["lookup"] = dict(plan["lookup"])
    duplicate["lookup"]["recordings"] = [
        {
            "musicbrainz_recording_id": "11111111-2222-3333-4444-555555555555"
        },
        {
            "musicbrainz_recording_id": "11111111-2222-3333-4444-555555555555"
        },
    ]
    duplicate["lookup"]["recording_count"] = 2
    errors = validate_playback_plan(duplicate)
    assert any("duplicate recording MBID" in error for error in errors)
