# Provider-neutral playback plans

PDv1 separates **what a physical disc means** from **how a particular provider plays it**. Draft 0.2 now compiles catalog/private records into a normalized machine-readable playback plan before any provider SDK, OAuth flow, BLE transport, or vehicle implementation is involved.

## Command

```bash
pdv1 plan-playback 042381 --provider spotify --provider-index build/spotify-index.json
```

Private/local IDs use the same contract:

```bash
pdv1 plan-playback 900000 --provider local --local-library ~/.playlistdisc
```

`--output plan.json` writes deterministic JSON. `--require-ready` returns exit code 3 when the plan still needs lookup, is partial/ambiguous, or is unavailable.

## Plan states

| Status | Meaning |
| --- | --- |
| `ready` | The plan has everything required to hand to a provider/player. |
| `partial` | Some canonical recordings resolved and some are missing. |
| `ambiguous` | At least one canonical recording has multiple/conflicting exact candidates. |
| `requires_lookup` | The semantic identity is known but the selected provider still needs an entity/recording lookup. |
| `unavailable` | The selected provider has no playable realization. |
| `unplayable` | The ID is intentionally non-musical, e.g. a diagnostic test vector. |

## Plan modes

`direct_resource` identifies one provider/local resource. `track_list` supplies resolved resources for an explicit canonical recording collection. `entity_lookup` carries a MusicBrainz artist or release-group identity. `recording_resolution` carries the canonical recording identities that a provider still needs to resolve into an exact-ID provider index. `none` means there is no playable provider action.

## Contract invariants

Status and mode are not independent labels. The packaged JSON Schema rejects combinations that could otherwise make different consumers interpret the same plan differently:

| Mode | Allowed status | Required mode payload |
| --- | --- | --- |
| `direct_resource` | `ready` | `resource` |
| `track_list` | `ready`, `partial`, `ambiguous` | `resources` |
| `entity_lookup` | `requires_lookup` | `lookup.type` = `artist` or `release_group`, plus `musicbrainz_id` |
| `recording_resolution` | `requires_lookup` | `lookup.type` = `canonical_manifest`, `recording_count`, and ordered `recordings` containing exact MBID/ISRC identity |
| `none` | `ambiguous`, `unavailable`, `unplayable` | no executable resource/lookup payload |

Mode-specific payloads are mutually exclusive. For example a `direct_resource` plan cannot also carry `resources`, `lookup`, or a resolution report, and a `track_list` cannot simultaneously claim a single `resource` or unresolved `lookup`. This makes the playback plan a discriminated contract rather than a bag of optional fields, which is important because host orchestration and materialization-cache logic accept plans generated outside the compiler as well as compiler-produced plans.

A canonical resolution report may accompany resolved `track_list` plans and non-executable `none` plans so incomplete/ambiguous coverage remains inspectable without turning that report itself into a playback action.

## Canonical manifests

When a provider/local index is supplied, the compiler calls the existing exact MBID/ISRC resolver. It preserves manifest order in the resulting resource list; `shuffle` remains a playback policy for the host rather than randomizing the plan at compile time.

Coverage is honest: missing recordings stay missing, conflicting exact identifiers stay ambiguous, and title/artist hints are never used as fuzzy substitutes. The full resolution report is embedded in the plan for diagnostics while the `resources` list contains only successfully resolved items.

If no provider index is supplied, the plan remains **self-contained**: it returns `requires_lookup` / `recording_resolution` with the canonical recording count plus an ordered `recordings` array. Each row contains the MusicBrainz Recording MBID and/or ISRC values from the canonical manifest, normalized for exact matching. If that manifest row has an exact override for the selected provider, only that provider's override is included as `provider_override`.

Human title/artist hints are deliberately not copied into this resolver payload. A future live provider plugin therefore has everything required for exact identity resolution without being tempted to fuzzy-match display text, and it does not need direct access to the catalog/manifests as a hidden side channel.

Playback-plan validation also requires `recording_count == len(recordings)` and rejects duplicate MBIDs/ISRCs across rows.

## Artist and album records

If a catalog record already has a concrete selected-provider resource, the compiler emits `direct_resource`. Otherwise artist catalogs emit a MusicBrainz Artist lookup and albums emit a MusicBrainz Release Group lookup. This keeps the canonical entity service-neutral while leaving provider search/materialization to the plugin.

## Federated and provider-native records

Federated records select the declared equivalent/best-available resource for the chosen provider. Provider-native records work only on their declared native provider. An explicit `unsupported` provider binding wins over fallback behavior.

## Private/local records

Private entries use their local `bindings` table but compile into the exact same playback-plan schema. This avoids a separate phone/bridge code path just because the disc ID is private.

## Boundary

The playback planner does not log into services, create playlists, stream audio, select Bluetooth transports, or control a car. It is the deterministic semantic handoff between the catalog/resolver layer and future provider/host implementations.
