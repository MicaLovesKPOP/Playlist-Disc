"""Build an offline provider-index from tagged local audio files."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Callable, Iterable

from .resolver import validate_provider_index

SUPPORTED_EXTENSIONS = frozenset(
    {
        ".aac",
        ".aif",
        ".aiff",
        ".ape",
        ".asf",
        ".flac",
        ".m4a",
        ".mp3",
        ".mp4",
        ".oga",
        ".ogg",
        ".opus",
        ".tta",
        ".wav",
        ".wma",
        ".wv",
    }
)

_UUID_RE = re.compile(
    r"(?i)([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
)
_ISRC_RE = re.compile(r"(?i)([A-Z]{2}[A-Z0-9]{3}[0-9]{7})")


@dataclass(frozen=True, slots=True)
class LocalScanReport:
    index: dict[str, Any]
    scanned_files: int
    indexed_files: int
    unidentified_files: int
    unreadable_files: int
    unreadable: tuple[str, ...]


def _normalized_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).casefold())


def _coerce_values(value: object) -> list[str]:
    if value is None:
        return []
    text_attr = getattr(value, "text", None)
    if isinstance(text_attr, (list, tuple)):
        return [str(item) for item in text_attr if str(item).strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    text = str(value)
    return [text] if text.strip() else []


def _tag_items(tags: object) -> Iterable[tuple[str, list[str]]]:
    if tags is None:
        return ()
    items = getattr(tags, "items", None)
    if not callable(items):
        return ()
    return (
        (_normalized_key(key), _coerce_values(value))
        for key, value in items()
    )


def _values_for(
    tags: object,
    *,
    exact: set[str] | None = None,
    contains: tuple[str, ...] = (),
) -> list[str]:
    exact = exact or set()
    result: list[str] = []
    for key, values in _tag_items(tags):
        if key in exact or any(fragment in key for fragment in contains):
            result.extend(values)
    return result


def _extract_mbids(values: Iterable[str]) -> tuple[str, ...]:
    found = {
        match.group(1).lower()
        for value in values
        for match in _UUID_RE.finditer(value)
    }
    return tuple(sorted(found))


def _extract_isrcs(values: Iterable[str]) -> tuple[str, ...]:
    found: set[str] = set()
    for value in values:
        normalized = value.upper().replace("-", "").replace(" ", "")
        found.update(match.group(1).upper() for match in _ISRC_RE.finditer(normalized))
    return tuple(sorted(found))


def extract_tag_identity(tags: object) -> dict[str, Any] | None:
    """Extract service-neutral identity from common easy/raw audio tags.

    MusicBrainz Picard's historical MusicBrainz Track Id tag contains the
    MusicBrainz Recording MBID and is therefore accepted alongside explicit
    MusicBrainz Recording Id spellings.
    """
    mbid_values = _values_for(
        tags,
        exact={"musicbrainztrackid", "musicbrainzrecordingid"},
        contains=("musicbrainzrecordingid", "musicbrainztrackid"),
    )
    mbids = _extract_mbids(mbid_values)
    if len(mbids) > 1:
        raise ValueError(
            "file contains multiple distinct MusicBrainz recording IDs: "
            + ", ".join(mbids)
        )

    isrc_values = _values_for(
        tags,
        exact={"isrc", "tsrc"},
        contains=("isrc",),
    )
    isrcs = _extract_isrcs(isrc_values)

    if not mbids and not isrcs:
        return None

    title_values = _values_for(
        tags,
        exact={"title", "tit2"},
    )
    artist_values = _values_for(
        tags,
        exact={"artist", "tpe1"},
    )

    result: dict[str, Any] = {}
    if mbids:
        result["musicbrainz_recording_id"] = mbids[0]
    if isrcs:
        result["isrcs"] = list(isrcs)
    if title_values:
        result["title_hint"] = title_values[0].strip()
    if artist_values:
        result["artist_hint"] = artist_values[0].strip()
    return result


def _default_loader(path: Path) -> object:
    try:
        import mutagen  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "local-library scanning requires the optional local-library extra "
            "(pip install 'playlist-disc[local-library]')"
        ) from exc
    return mutagen.File(path, easy=True)


def _candidate_files(root: Path, recursive: bool) -> list[Path]:
    iterator = root.rglob("*") if recursive else root.glob("*")
    files = [
        path
        for path in iterator
        if path.is_file() and path.suffix.casefold() in SUPPORTED_EXTENSIONS
    ]
    return sorted(
        files,
        key=lambda path: path.relative_to(root).as_posix().casefold(),
    )


def scan_local_library(
    root: str | Path,
    *,
    recursive: bool = True,
    loader: Callable[[Path], object] | None = None,
) -> LocalScanReport:
    """Scan tagged audio and build a validated provider=local index.

    Files without a MusicBrainz Recording MBID or ISRC are deliberately omitted.
    No title/artist fuzzy matching is performed.
    """
    root_path = Path(root).expanduser().resolve()
    if not root_path.is_dir():
        raise ValueError(f"local library root is not a directory: {root_path}")

    loader = loader or _default_loader
    tracks: list[dict[str, Any]] = []
    unidentified = 0
    unreadable: list[str] = []
    candidates = _candidate_files(root_path, recursive)

    for path in candidates:
        relative = path.relative_to(root_path).as_posix()
        try:
            audio = loader(path)
            if audio is None:
                raise ValueError("unsupported or unrecognized audio container")
            identity = extract_tag_identity(getattr(audio, "tags", None))
        except Exception as exc:
            unreadable.append(f"{relative}: {exc}")
            continue

        if identity is None:
            unidentified += 1
            continue

        item = {
            "resource": path.resolve().as_uri(),
            **identity,
        }
        tracks.append(item)

    tracks.sort(key=lambda item: item["resource"])
    index: dict[str, Any] = {
        "schema_version": 1,
        "provider": "local",
        "tracks": tracks,
        "notes": (
            "Generated from local audio tags. Files without an exact MusicBrainz "
            "Recording MBID or ISRC were intentionally omitted."
        ),
    }

    errors = validate_provider_index(index)
    if errors:
        raise ValueError("generated provider index is invalid: " + "; ".join(errors))

    return LocalScanReport(
        index=index,
        scanned_files=len(candidates),
        indexed_files=len(tracks),
        unidentified_files=unidentified,
        unreadable_files=len(unreadable),
        unreadable=tuple(unreadable),
    )


def write_local_provider_index(
    report: LocalScanReport, output: str | Path
) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.index, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
