# Local/private discs

PDv1 reserves `900000-989999` for permanently local/private use. These identities never need a central registry, account, or telemetry.

Draft 0.2 tooling can manage these mappings entirely on disk. This is useful for validating the workflow now, but the physical-format warning still applies: **while PDv1 is a draft, only the development/test range should be burned to real media.** Private IDs can be virtually built and verified before PDv1.0.

## Local library layout

A local library uses the same deterministic sharding idea as the public catalog:

```text
~/.playlistdisc/
  discs/
    900/
      900000.yaml
      900001.yaml
```

The local file contains human titles, playback behavior, and one or more local provider/resource bindings. Provider resources are intentionally local configuration; they are not uploaded to the public catalog and are not part of the physical identity.

Do not store passwords, OAuth tokens, cookies, or API secrets in these files. A binding should contain only the provider's non-secret playlist/library locator needed by a future resolver.

## Create a mapping

```bash
pdv1 local-create ~/.playlistdisc \
  --title "Personal favourites" \
  --short-title "FAVOURITES" \
  --binding spotify=spotify:playlist:example \
  --binding local=library:playlist:favourites \
  --order shuffle \
  --start random \
  --tag personal
```

Without `--id`, the tool allocates the lowest unused private ID. To preserve an existing personal numbering plan, pass a specific unused ID:

```bash
pdv1 local-create ~/.playlistdisc \
  --id 901234 \
  --title "Road trip" \
  --short-title "ROAD TRIP" \
  --binding local=library:playlist:road-trip
```

Allocation is local only. If the same person keeps multiple unsynchronized local libraries, those libraries can independently allocate the same number. Use one authoritative library and back it up or synchronize it between devices.

## Validate and inspect

```bash
pdv1 local-validate ~/.playlistdisc
pdv1 local-list ~/.playlistdisc
pdv1 local-list ~/.playlistdisc --json
```

Validation checks the private namespace, file sharding, schema, playback values, and binding shape. Creation uses exclusive file creation so an existing mapping is never silently overwritten.

There is deliberately no CLI command to delete or repurpose a private ID. A user can edit their own files, but once a physical disc exists, reusing its number for unrelated music creates the same semantic-confusion problem as recycling a public ID.

## Virtual build

A local record can provide title metadata when generating a mastering bundle:

```bash
pdv1 build 900000 \
  --local-library ~/.playlistdisc \
  --output build/PD1-900000

pdv1 verify-build build/PD1-900000
```

This exercises allocation, metadata lookup, TOC generation, CD-TEXT generation, beacon generation, and cross-channel verification without consuming optical media.

## Why bindings are local

Public IDs are designed around durable, provider-neutral meaning. A private disc has a different trust boundary: its mapping belongs to the user and can include direct personal-library locators. Keeping those bindings outside the public repository avoids leaking personal playlist identifiers and allows the same private physical ID to have different service bindings on the user's own devices.
