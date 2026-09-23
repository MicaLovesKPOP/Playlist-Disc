# Local music-library scanner

PDv1 Draft 0.2 can build the same provider-index used by the canonical resolver directly from a tagged local music library.

This is an optional feature. The core toolkit does not require an audio-tagging dependency.

## Install scanner support

```bash
python -m pip install 'playlist-disc[local-library]'
```

From a repository checkout:

```bash
python -m pip install -e '.[local-library,dev]'
```

## Scan

```bash
pdv1 scan-local-library ~/Music --output build/local-provider-index.json
pdv1 validate-provider-index build/local-provider-index.json
```

Use `--no-recursive` to scan only the top-level directory.

The generated provider is `local`, and each resource is an absolute `file://` URI.

## Identity requirements

The scanner indexes a file only when its metadata contains at least one service-neutral recording identifier:

- MusicBrainz Recording MBID; or
- ISRC.

The historical MusicBrainz tag name `MusicBrainz Track Id` is accepted because it represents the MusicBrainz Recording entity.

Files with only artist/title tags are intentionally skipped. PDv1 does not fuzzy-match a similarly named local file to a canonical recording.

## Duplicates

The scanner does not arbitrarily choose between two local files representing the same recording. Both resources appear in the provider index, and the canonical resolver reports ambiguity unless the index is later curated to mark exactly one representation `preferred`.

That avoids silently preferring an MP3 over a FLAC, a clean version over an explicit version, or one master over another.

## Unreadable and unidentified files

Scanning continues if one file cannot be read. The CLI reports counts for files considered, indexed files, files lacking a canonical identifier, and unreadable files.

Use `--show-errors` to print unreadable-file details.

## Privacy

The output contains absolute local file URIs. Treat it as local configuration and do not commit it to the public Playlist Disc catalog.

No file contents, paths, or tags are uploaded anywhere by the scanner.

## Cross-service use

Once generated, the local index can be fed into the same exact-identifier resolver used by future streaming-service plugins. This is deliberate: a physical canonical disc should have the same meaning whether its audio comes from a local FLAC library or a streaming catalog.
