# Catalog evolution and public-ID immutability

Playlist Disc is designed around physical objects that may remain in use for decades. Once a permanent public ID is active, changing what that ID means would silently repurpose already-burned discs.

Draft 0.2 therefore implements the evolution guard **before** the permanent namespace is opened.

## Current Draft 0.2 state

Permanent public activation is closed. Records in `000001-899999` may be modeled as `draft` proposals, but repository validation rejects public `active` and `retired` records until PDv1.0 freezes the physical format.

Development/test IDs in `999900-999999` are unaffected by this future-public lock.

## Command

```bash
pdv1 check-catalog-evolution /path/to/baseline/catalog catalog
```

The baseline should be the target branch state before the proposed change. CI creates a detached worktree at the PR base commit (or previous main commit after a push) and runs this comparison automatically.

## When protection starts

A permanent public record is not protected while its baseline status is `draft`. It can still be corrected, redesigned, renumbered, or removed before publication.

Once its baseline status is `active`, its semantic core is considered to have physical copies in the world. Retirement does not remove that protection.

## Locked after activation

The following entry fields are immutable:

- canonical `title`;
- `short_title` used for compact/OEM display labeling;
- `definition` (artist/release IDs, canonical manifest path and membership policy, federated concept, provider-native provider, etc.);
- `lifecycle` (`snapshot` vs `living`);
- `portability`;
- default `playback` behavior.

An active entry may remain `active` or transition once to `retired`. A retired entry stays retired and cannot be deleted or reactivated.

## Canonical manifests

For an active `snapshot` canonical manifest, service-neutral recording membership is immutable.

The comparison intentionally ignores:

- `title_hint` / `artist_hint` corrections;
- provider-specific exact-track overrides.

Those fields help resolution/review but do not define canonical membership.

For shuffle collections, manifest row order is ignored. For ordered playback, row order is part of meaning and is protected.

For a `living` canonical manifest, membership is allowed to evolve. Its definition and `membership_policy` remain locked, so changing the rule itself requires a new ID. Human review is still required because software cannot prove that a new recording actually satisfies a natural-language policy.

## Provider-native resources

For provider-native entries, the native provider's direct `resource` and optional market are additionally protected. Changing from one native playlist/resource to another would otherwise silently repurpose the physical disc.

Canonical and federated provider bindings are realization details and may change as services move URLs, catalogs, or APIs.

## Intentionally mutable metadata

Subject to normal catalog validation, these can evolve without changing physical identity:

- tags;
- maintainers and provenance administration;
- notes;
- non-native provider bindings;
- provider resolution overrides/hints;
- pack/wallet membership and ordering;
- a retired entry's successor reference.

## Snapshot corrections

If an already-active snapshot genuinely contains the wrong canonical recording identity, the conservative default is to issue a new public ID and retire the old one. This keeps CI mechanically trustworthy rather than creating an easy 'correction' bypass capable of changing physical meaning.

## Why CI compares history

Ordinary schema validation can tell whether today's file is internally valid; it cannot tell whether an old piece of plastic has just been redefined. Evolution validation therefore needs both the baseline and current catalog.

The repository CI performs this historical comparison on pull requests and on pushes to `main`.
