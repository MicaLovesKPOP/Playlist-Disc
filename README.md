# Playlist Disc

**Playlist Disc (PDv1)** is an experimental open physical format that turns an ordinary audio CD into a provider-neutral playlist token for older cars.

Insert one physical disc and a compatible vehicle/phone integration can interpret it as an intent such as:

- an artist's full catalog, shuffled;
- a year/genre collection;
- a community-curated playlist;
- a service-relative editorial collection;
- a private personal playlist.

The same disc is intended to work across different cars and playback services. The disc itself does not contain Spotify, Apple Music, vehicle, or phone-specific identifiers.

> [!WARNING]
> PDv1 is currently **Draft 0.1**. Only IDs `999900-999999` are for physical experiments. Do not mint permanent public music discs until PDv1.0 is frozen after real-world compatibility testing.

## Why CDs?

Many 2000s/early-2010s cars have excellent OEM CD mechanisms but awkward or nonexistent modern streaming integration. A Playlist Disc keeps the delightful physical ritual while letting the audio source remain modern and updateable.

A disc carries the same logical identity redundantly through:

1. a deterministic eight-track table of contents;
2. an optional CD-TEXT machine ID;
3. an experimental repeated audio beacon;
4. a human-readable printed ID.

If a car exposes its TOC or metadata, an adapter can identify the disc without playing the beacon. If it exposes nothing useful, an analogue fallback decoder can still identify the disc from track 1.

## Quick start

```bash
python -m pip install -e '.[dev]'

pdv1 inspect 999901
pdv1 build 999901 --output build/PD1-999901
pdv1 validate-catalog catalog
pytest
```

Example output from `pdv1 inspect 123456`:

```text
PD1-123456-3
namespace: public
check digit: 3
tracks: 0:09, 0:16, 0:20, 0:24, 0:28, 0:32, 0:36, 0:24
total: 3:09
```

The generated bundle contains a tiny `beacon.wav`, `disc.toc`, and `manifest.json`. `cdrdao` writes the mastering file in Disc-At-Once mode.

## Design principles

- **Cheap and cheerful:** ordinary CD-R is the default; finalized CD-RW is allowed for reusable/test discs.
- **Provider-neutral:** public IDs represent musical intent, not a provider URL, unless explicitly provider-native.
- **Car-neutral:** vehicle integrations translate their own electronics into a common disc-selection event.
- **Fail open:** an unrecognized or ambiguous disc behaves as a normal audio CD.
- **Immutable physical meaning:** once PDv1.0 allocates a public ID, it is never recycled or silently repurposed.
- **Private by default when desired:** a large local-only namespace requires no account, registration, or telemetry.

## Repository layout

- `spec/` — physical format, catalog model, future bridge protocol
- `catalog/` — public/test registry and schemas
- `compatibility/` — measured legacy-player/vehicle results
- `src/playlistdisc/` — reference library and CLI
- `tests/` — algorithm tests and golden vectors
- `docs/` — burning, testing, and roadmap documentation

## Planned namespace

| Range | Meaning |
| --- | --- |
| `000000` | invalid / never allocated |
| `000001-899999` | future public registry |
| `900000-989999` | private/local use |
| `990000-999899` | reserved |
| `999900-999999` | development/test |

The exact ranges remain draft until PDv1.0.

## Licensing

- software: Apache-2.0;
- specification/documentation: intended CC BY 4.0;
- catalog metadata: intended CC0 1.0.

See `LICENSE` and `LICENSES/README.md`.
