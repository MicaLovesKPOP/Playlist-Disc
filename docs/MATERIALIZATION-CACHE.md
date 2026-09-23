# Materialization cache

Some providers will require Playlist Disc to create or maintain a provider-side playlist before playback can be started efficiently. Recreating that playlist every time a physical disc is inserted would be slow, noisy, and wasteful.

Draft 0.2 therefore defines a **local cache record** for deterministic `track_list` playback plans.

## Cache a materialized provider resource

Given a validated playback plan:

```bash
pdv1 materialization-put plan.json \
  --cache ~/.playlistdisc/materializations \
  --scope default \
  --resource spotify:playlist:generated
```

Then later:

```bash
pdv1 materialization-check plan.json \
  --cache ~/.playlistdisc/materializations \
  --scope default
```

A hit returns the previously materialized provider resource. A missing or stale record returns exit code 3.

## What invalidates the cache

The **complete normalized playback plan** is SHA-256 fingerprinted. Therefore any change to meaningful provider-facing input invalidates the record automatically, including:

- canonical track membership/order as represented in the plan;
- exact provider resolution/resource choices;
- ready vs partial coverage;
- playback order/start/repeat policy;
- provider;
- disc identity.

The cache also records the source-resource count as an independently readable sanity check.

This means a living canonical collection naturally gets a new cache key state when its compiled track list changes.

## Account/profile scope

A provider-created playlist normally belongs to one provider account/profile. Callers supply a local `scope` string. Only its SHA-256 is stored and used in the path:

```text
<cache>/<provider>/<scope-sha256>/<disc-id>.json
```

This avoids putting an e-mail/account label directly into filenames. It is **not encryption or anonymization against guessing**; the cache is private local state and should not be published.

OAuth access/refresh tokens, cookies, passwords, and provider credentials never belong in a materialization record.

## Deliberately narrow scope

The generic cache currently accepts only playback plans with:

- mode `track_list`; and
- status `ready` or `partial`.

That boundary is intentional.

A `direct_resource` plan already has a stable selected resource and does not need a generated playlist.

An `entity_lookup` such as an artist catalog can change remotely even when its MusicBrainz artist identity does not. Caching such a lookup requires provider-specific refresh/version/TTL semantics and is therefore left to the future plugin.

A `recording_resolution` plan has not yet resolved its canonical tracks and cannot be safely materialized.

## Partial plans

A host may choose to materialize a partial plan, but the record pins the exact partial plan and status. If later resolution improves, the new plan fingerprint invalidates that materialization.

Whether partial playback is acceptable remains host/user policy.

## Provider revisions

Plugins may attach an opaque `provider_revision` to a record for diagnostics. The generic cache does not interpret it. Provider-specific freshness beyond exact plan equivalence remains plugin responsibility.

## Privacy

Materialization caches may contain private provider playlist/resource identifiers and should remain local. They are not part of the public catalog and are excluded from physical disc identity.
