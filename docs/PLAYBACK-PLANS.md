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

`direct_resource` identifies one provider/local resource. `track_list` supplies resolved resources for an explicit canonical recording collection. `entity_lookup` carries a MusicBrainz artist or release-group identity. `recording_resolution` says a canonical manifest needs an exact-ID provider index. `none` means there is no playable provider action.

## Canonical manifests

When a provider/local index is supplied, the compiler calls the existing exact MBID/ISRC resolver. It preserves manifest order in the resulting resource list; `shuffle` remains a playback policy for the host rather than randomizing the plan at compile time.

Coverage is honest: missing recordings stay missing, conflicting exact identifiers stay ambiguous, and title/artist hints are never used as fuzzy substitutes. The full resolution report is embedded in the plan for diagnostics while the `resources` list contains only successfully resolved items.

If no provider index is supplied, the plan is still useful: it returns `requires_lookup` / `recording_resolution` with the canonical recording count. A future live provider plugin can satisfy that requirement.

## Artist and album records

If a catalog record already has a concrete selected-provider resource, the compiler emits `direct_resource`. Otherwise artist catalogs emit a MusicBrainz Artist lookup and albums emit a MusicBrainz Release Group lookup. This keeps the canonical entity service-neutral while leaving provider search/materialization to the plugin.

## Federated and provider-native records

Federated records select the declared equivalent/best-available resource for the chosen provider. Provider-native records work only on their declared native provider. An explicit `unsupported` provider binding wins over fallback behavior.

## Private/local records

Private entries use their local `bindings` table but compile into the exact same playback-plan schema. This avoids a separate phone/bridge code path just because the disc ID is private.

## Boundary

The playback planner does not log into services, create playlists, stream audio, select Bluetooth transports, or control a car. It is the deterministic semantic handoff between the catalog/resolver layer and future provider/host implementations.
