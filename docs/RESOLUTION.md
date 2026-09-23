# Cross-service canonical resolution

PDv1 public identity is intentionally independent of Spotify, Apple Music, local files, or any future playback provider. Draft 0.2 now includes a deterministic resolution core that can be exercised without provider accounts or network access.

## Provider resolution index

The reference/testing interchange is a small JSON document:

```json
{
  "schema_version": 1,
  "provider": "example",
  "market": "NL",
  "tracks": [
    {
      "resource": "example:track:123",
      "musicbrainz_recording_id": "11111111-2222-3333-4444-555555555555",
      "isrcs": ["KRABC2600001"],
      "preferred": true
    }
  ]
}
```

Live provider plugins may build this structure in memory rather than write it to disk. A local-library implementation can use file/library URIs as resources.

## Resolution order

For each row of a canonical manifest:

1. an explicit provider override wins;
2. otherwise exact MusicBrainz Recording MBID and/or ISRC matches are considered;
3. when both identifier families match, their intersection is preferred;
4. contradictory MBID/ISRC candidate sets become **ambiguous**, never guessed;
5. multiple equivalent provider resources remain ambiguous unless exactly one is marked `preferred`;
6. no exact identifier match is **missing**.

Title and artist hints are never fuzzy identity. A similarly named remix, live version, rerecording, or unrelated track must not be silently substituted just to increase coverage.

## Partial coverage is valid

A canonical collection can contain tracks unavailable in a provider/market. Resolution therefore returns resolved, missing, and ambiguous counts plus coverage. Missing music should be reported to the user; the resolver does not rewrite canonical membership.

## Why this exists before live provider plugins

This layer lets us test the hardest semantic question independently of OAuth/API churn: what does it mean for one physical CD to represent the **same recording collection** on multiple services?

Spotify/Apple/etc. adapters can later focus on authentication, catalog lookup, playlist materialization, and playback control while conforming to this deterministic core.

## Scope

Draft 0.2 currently resolves explicit `canonical_manifest` collections. Artist-catalog and album definitions require provider entity resolvers and remain future plugin work.
