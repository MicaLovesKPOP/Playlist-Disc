# Packs and wallets

A pack is an **ordered view of existing catalog IDs** for browsing, sharing, or arranging a physical CD wallet. A pack never allocates an ID and never changes what a disc means.

Draft 0.2 source packs live at:

```text
catalog/packs/<slug>.yaml
```

and validate against `catalog/schema/pack.schema.json`.

## Source model

A pack declares:

- a stable human-readable `slug`;
- title, status, provenance, and tags;
- a practical wallet `capacity` of 12, 24, 48, or 96;
- an ordered, duplicate-free list of existing six-digit catalog IDs.

The list order is the wallet order. Generated library snapshots resolve it to explicit 1-based slots with each disc's machine ID and display metadata.

A pack may contain fewer discs than its capacity. This supports partially filled wallets without inventing placeholder identities.

## Identity boundary

Pack membership is curation, not physical identity. Updating or retiring a pack does not alter any referenced Playlist Disc. Conversely, changing the meaning of a disc cannot be justified by saying that a pack changed.

`pdv1 validate-catalog` rejects missing disc references, duplicate slots, wrong pack paths, and lists larger than their declared capacity.

During Draft 0.2, permanent public music IDs are still closed. The repository therefore contains only a small development/test-vector pack. Physical wallet artwork and print-layout conventions remain outside the format until they can be informed by real use.

See `docs/LIBRARY.md` for pack/search commands and generated static-library JSON.
