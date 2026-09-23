# Public catalog model

The public catalog is a registry of **meanings**, not a pile of streaming URLs.

## Categories are facets, not ID ranges

The same entry can be a community-maintained, living, canonical, K-pop collection. These properties are stored independently. Numeric IDs do not encode category, provider, genre, ownership, or curation authority.

## Examples

### Artist catalog

A disc can mean "play this artist's catalog". Provider plugins are free to materialize or directly play the catalog while preserving the declared playback behavior.

### Canonical community collection

A community collection such as "K-Pop Girl Group Singles" should ideally identify service-neutral recordings in a manifest, using stable music metadata identifiers where available. Spotify, Apple Music, local-library, and future-provider bindings become resolvers for the same collection.

### Federated editorial concept

A concept such as "Current Global Pop Hits" may intentionally map to each service's own editorial equivalent. Its portability must be declared `federated` so users are not told those track lists are identical.

### Provider-native record

A public disc may deliberately identify one provider's editorial or user-owned playlist. Its portability is `provider_native`; unsupported providers remain unsupported rather than pretending to be equivalent.

## Living and snapshot collections

A `snapshot` entry has membership intended to stabilize apart from corrections. A `living` entry can gain newly qualifying music without changing its semantic meaning—for example an artist's complete catalog or an ongoing genre collection.
