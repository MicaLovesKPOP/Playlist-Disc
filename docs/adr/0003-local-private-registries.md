# ADR 0003: Private IDs use user-owned local registries

- **Status:** accepted for Draft 0.2
- **Date:** 2026-09-23

## Context

PDv1 reserves `900000-989999` for private/local use. Requiring those IDs to be registered with the project would defeat the privacy and offline-use goal. Encoding provider resources directly into the physical disc is impossible within the six-digit identity model and would make the disc provider-specific.

Private mappings can also contain personal playlist identifiers that do not belong in a public repository.

## Decision

Private IDs are resolved through a user-owned local registry stored outside the public catalog.

The reference layout is deterministically sharded by ID. Each record contains:

- the private six-digit ID;
- human title and conservative CD-TEXT short title;
- playback behavior;
- one or more non-secret provider/resource bindings;
- optional local tags and notes.

The reference allocator chooses the lowest unused private ID unless the user explicitly requests an unused private ID.

The project does not provide a central allocator for private IDs and does not claim global uniqueness. Users who use several devices should synchronize one authoritative local registry.

The reference CLI does not provide a destructive delete/recycle operation. Local files remain user-owned and editable, but repurposing an ID after a physical disc has been made is discouraged because old media would silently acquire new meaning.

## Consequences

- Private usage requires no account, network service, or telemetry.
- Personal provider/library locators stay out of the public catalog.
- One private disc can have bindings for several services in the user's own registry.
- Independent private registries can collide numerically; this is acceptable because the namespace is explicitly local.
- Backup and synchronization are the user's responsibility.
- Physical burning of private IDs remains deferred while the overall physical format is still Draft 0.2; the workflow can nevertheless be built and verified entirely in software.
