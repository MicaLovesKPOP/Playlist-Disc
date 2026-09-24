import pytest

from playlistdisc.identity import PDIdentity
from playlistdisc.playback import validate_playback_plan


PLAYBACK = {"order": "ordered", "start": "first", "repeat": "context"}
MBID = "11111111-2222-3333-4444-555555555555"


def _plan(status: str, mode: str, **extra) -> dict:
    identity = PDIdentity.parse("042381")
    return {
        "schema_version": 1,
        "format": "PDv1-playback-plan",
        "disc_id": identity.id6,
        "machine_id": identity.machine_id,
        "title": "Contract test",
        "provider": "demo",
        "status": status,
        "mode": mode,
        "playback": dict(PLAYBACK),
        **extra,
    }


@pytest.mark.parametrize(
    ("status", "mode", "extra"),
    [
        ("ready", "direct_resource", {"resource": "demo:playlist:one"}),
        ("ready", "track_list", {"resources": ["demo:a"]}),
        (
            "partial",
            "track_list",
            {"resources": ["demo:a"], "resolution": {"coverage": 0.5}},
        ),
        (
            "ambiguous",
            "track_list",
            {"resources": ["demo:b"], "resolution": {"ambiguous_count": 1}},
        ),
        ("ambiguous", "none", {"resolution": {"ambiguous_count": 2}}),
        (
            "requires_lookup",
            "entity_lookup",
            {"lookup": {"type": "artist", "musicbrainz_id": MBID}},
        ),
        (
            "requires_lookup",
            "recording_resolution",
            {
                "lookup": {
                    "type": "canonical_manifest",
                    "recording_count": 2,
                    "recordings": [
                        {"musicbrainz_recording_id": MBID},
                        {"isrcs": ["KRABC2600002"]},
                    ],
                }
            },
        ),
        ("unavailable", "none", {}),
        ("unplayable", "none", {}),
    ],
)
def test_playback_contract_accepts_supported_status_mode_pairs(status, mode, extra):
    assert validate_playback_plan(_plan(status, mode, **extra)) == []


@pytest.mark.parametrize(
    ("status", "mode", "extra"),
    [
        ("ready", "none", {}),
        ("partial", "none", {}),
        ("requires_lookup", "direct_resource", {"resource": "demo:x"}),
        ("unavailable", "direct_resource", {"resource": "demo:x"}),
        ("unplayable", "track_list", {"resources": ["demo:x"]}),
        (
            "ready",
            "entity_lookup",
            {"lookup": {"type": "artist", "musicbrainz_id": MBID}},
        ),
    ],
)
def test_playback_contract_rejects_impossible_status_mode_pairs(status, mode, extra):
    assert validate_playback_plan(_plan(status, mode, **extra))


@pytest.mark.parametrize(
    "plan",
    [
        _plan(
            "ready",
            "direct_resource",
            resource="demo:x",
            resources=["demo:y"],
        ),
        _plan(
            "ready",
            "track_list",
            resources=["demo:x"],
            resource="demo:y",
        ),
        _plan(
            "requires_lookup",
            "entity_lookup",
            lookup={"type": "artist", "musicbrainz_id": MBID},
            resource="demo:x",
        ),
        _plan(
            "requires_lookup",
            "recording_resolution",
            lookup={"type": "canonical_manifest", "recording_count": 2},
            resolution={"coverage": 0.0},
        ),
        _plan(
            "unavailable",
            "none",
            lookup={"type": "canonical_manifest", "recording_count": 2},
        ),
    ],
)
def test_playback_contract_rejects_payload_from_another_mode(plan):
    assert validate_playback_plan(plan)


@pytest.mark.parametrize(
    "plan",
    [
        _plan(
            "requires_lookup",
            "entity_lookup",
            lookup={"type": "canonical_manifest", "recording_count": 2},
        ),
        _plan(
            "requires_lookup",
            "entity_lookup",
            lookup={"type": "artist"},
        ),
        _plan(
            "requires_lookup",
            "recording_resolution",
            lookup={"type": "artist", "musicbrainz_id": MBID},
        ),
        _plan(
            "requires_lookup",
            "recording_resolution",
            lookup={"type": "canonical_manifest"},
        ),
    ],
)
def test_playback_contract_rejects_lookup_payload_for_wrong_mode(plan):
    assert validate_playback_plan(plan)
