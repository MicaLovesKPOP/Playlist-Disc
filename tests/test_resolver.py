from pathlib import Path

from playlistdisc.resolver import (
    resolve_canonical_manifest,
    validate_provider_index,
)


def _entry() -> dict:
    return {
        "id": "042381",
        "definition": {
            "type": "canonical_manifest",
            "manifest": "manifests/042/042381.json",
            "membership_policy": "Exact test set.",
        },
        "playback": {"order": "shuffle", "start": "random", "repeat": "context"},
    }


def _manifest() -> dict:
    return {
        "schema_version": 1,
        "disc_id": "042381",
        "recordings": [
            {
                "musicbrainz_recording_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "isrcs": ["KRABC2600001"],
                "provider_overrides": {"demo": "demo:override"},
                "title_hint": "Override",
            },
            {
                "musicbrainz_recording_id": "11111111-2222-3333-4444-555555555555",
                "title_hint": "MBID",
            },
            {
                "isrcs": ["KRABC2600003"],
                "title_hint": "ISRC",
            },
            {
                "musicbrainz_recording_id": "22222222-2222-3333-4444-555555555555",
                "isrcs": ["KRABC2600004"],
                "title_hint": "Conflict",
            },
            {
                "musicbrainz_recording_id": "33333333-2222-3333-4444-555555555555",
                "title_hint": "Missing despite same human title",
                "artist_hint": "Same Artist",
            },
            {
                "musicbrainz_recording_id": "44444444-2222-3333-4444-555555555555",
                "title_hint": "Preferred duplicate",
            },
        ],
    }


def _index() -> dict:
    return {
        "schema_version": 1,
        "provider": "demo",
        "market": "NL",
        "tracks": [
            {
                "resource": "demo:mbid",
                "musicbrainz_recording_id": "11111111-2222-3333-4444-555555555555",
            },
            {"resource": "demo:isrc", "isrcs": ["KRABC2600003"]},
            {
                "resource": "demo:conflict-mbid",
                "musicbrainz_recording_id": "22222222-2222-3333-4444-555555555555",
            },
            {"resource": "demo:conflict-isrc", "isrcs": ["KRABC2600004"]},
            {
                "resource": "demo:preferred-a",
                "musicbrainz_recording_id": "44444444-2222-3333-4444-555555555555",
            },
            {
                "resource": "demo:preferred-b",
                "musicbrainz_recording_id": "44444444-2222-3333-4444-555555555555",
                "preferred": True,
            },
            {
                "resource": "demo:human-only-does-not-match",
                "musicbrainz_recording_id": "99999999-2222-3333-4444-555555555555",
                "title_hint": "Missing despite same human title",
                "artist_hint": "Same Artist",
            },
        ],
    }


def test_resolution_uses_override_exact_ids_and_explicit_ambiguity():
    plan = resolve_canonical_manifest(_entry(), _manifest(), _index())
    assert plan.provider == "demo"
    assert plan.market == "NL"
    assert plan.total_recordings == 6
    assert plan.resolved_count == 4
    assert plan.ambiguous_count == 1
    assert plan.missing_count == 1
    assert plan.coverage == 4 / 6

    by_position = {item.position: item for item in plan.items}
    assert by_position[1].method == "override"
    assert by_position[1].resource == "demo:override"
    assert by_position[2].method == "mbid"
    assert by_position[2].resource == "demo:mbid"
    assert by_position[3].method == "isrc"
    assert by_position[3].resource == "demo:isrc"
    assert by_position[4].status == "ambiguous"
    assert by_position[4].method == "identifier_conflict"
    assert by_position[5].status == "missing"
    assert by_position[6].method == "mbid+preferred"
    assert by_position[6].resource == "demo:preferred-b"


def test_unavailable_provider_rows_do_not_resolve():
    index = _index()
    index["tracks"][0]["available"] = False
    plan = resolve_canonical_manifest(_entry(), _manifest(), index)
    assert plan.items[1].status == "missing"


def test_provider_index_rejects_duplicate_resources():
    index = _index()
    index["tracks"].append(dict(index["tracks"][0]))
    errors = validate_provider_index(index)
    assert any("duplicate provider resource" in error for error in errors)


def test_human_title_artist_are_never_fuzzy_identity():
    plan = resolve_canonical_manifest(_entry(), _manifest(), _index())
    missing = plan.items[4]
    assert missing.title_hint == "Missing despite same human title"
    assert missing.artist_hint == "Same Artist"
    assert missing.status == "missing"
