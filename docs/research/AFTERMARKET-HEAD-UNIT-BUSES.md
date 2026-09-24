# Aftermarket head-unit bus pre-hardware research

Playlist Disc can gain disproportionately broad compatibility by supporting reusable aftermarket head-unit buses rather than treating every installation as a vehicle-specific integration.

This note maps the useful pre-hardware families and deliberately stops before implementing undocumented electrical/protocol constants.

## Why this lane matters

Aftermarket radios break the direct relationship between vehicle make and audio protocol. A single changer/control bus can appear in cars from many manufacturers.

That makes aftermarket bus support one of the few ways a PD Bridge adapter can expand compatibility without adding another vehicle-specific CAN/MOST implementation.

## Alpine M-Bus and Ai-NET are separate generations

Yatour's application guide defines distinct products for:

- Alpine M-Bus head units;
- Alpine Ai-NET head units.

It also maps some older Honda/Acura OEM Alpine radios into the M-Bus family.

The safe conclusion is that Alpine support must be generation-specific. M-Bus and Ai-NET should not be collapsed into one "Alpine" adapter merely because both are external-changer buses.

## Pioneer IP-Bus is a reusable changer/accessory family

Yatour lists a dedicated Pioneer IP-BUS adapter across a broad range of DEH/KEH/MEH-era head units.

This establishes IP-Bus as a worthwhile standalone adapter target. Exact bus framing and electrical behavior should come from representative hardware or a proven implementation, not from model-name inference.

## Sony UniLink is a distinct networked accessory family

Sony changer documentation and community hardware work identify UniLink as the protocol used by compatible Sony head units and changers.

Community projects demonstrate the practical problem PDv1 would solve: the analogue auxiliary input on many Sony units remains unavailable until a valid UniLink device is present.

That makes UniLink a useful future source-emulation/control lane, but protocol implementation remains bench-gated.

## Clarion CeNET is another explicit accessory-bus generation

Yatour defines a dedicated Clarion CeNET-compatible product family and separates it from other changer protocols.

Community material independently refers to CeNET as Clarion's digital accessory interface.

This is enough to keep CeNET as a distinct adapter plugin without claiming protocol details.

## Blaupunkt DMS / CDC is widespread but dialect-sensitive

Blaupunkt changer reverse-engineering material shows a dedicated DMS/CDC protocol used across many OEM and aftermarket applications.

Arduino/forum work demonstrates 9-bit-serial-style CDC communication and real changer/head-unit interaction. The project's Alfa research already shows that even closely related Blaupunkt OEM radios can have firmware- and vehicle-specific source behavior.

Therefore Blaupunkt should be treated as a **family of related CDC dialects**, not one guaranteed universal emulator.

## JVC and other vendor-specific buses

Yatour exposes dedicated JVC and Sony product variants in addition to the named Alpine, Pioneer and Clarion families.

The current public evidence is enough to justify plugin boundaries but not enough to spend pre-hardware time reverse-engineering every vendor bus. JVC-specific details, Becker variants and less common systems can be added when representative hardware or a contributor exists.

## Adapter architecture consequence

PD Bridge should model aftermarket integrations as small protocol plugins behind the same normalized capabilities:

- changer/source present;
- next/previous/play-pause controls where available;
- source activation/deactivation where supported;
- now-playing/display capability only when proven;
- audio path treated separately from logical bridge events.

A future hardware design can therefore share the phone/BLE/host side while swapping only the head-unit bus front end.

## Priority after hardware begins

The highest-leverage representative aftermarket set would be:

1. Alpine M-Bus;
2. Pioneer IP-Bus;
3. Sony UniLink;
4. one Blaupunkt DMS/CDC implementation.

Ai-NET and CeNET become second-wave targets unless suitable hardware is already available.

That set spans multiple protocol styles without buying a museum of head units.

## Questions deliberately left for hardware

- exact voltage levels, transceivers, baud/framing and wake/handshake behavior of each bus;
- whether source activation requires periodic keepalive;
- how controls are encoded and whether long-press/seek semantics differ;
- display-text limits and character encoding;
- whether audio is analogue, digital or separately switched by generation;
- coexistence with a real changer or other accessory;
- whether one bus implementation survives multiple head-unit firmware generations.

## Sources

All links checked on 2026-09-24.

- **Yatour YT-M06 application guide, mirror by Manualzz.** Separate Alpine M-Bus, Alpine Ai-NET, Clarion CeNET, Pioneer IP-BUS, JVC and Sony product families plus tested head-unit examples. https://manualzz.com/doc/23313500/yatour-yt-m06-digital-music-changer-user-manual
- **Arduino Forum, Talking to a Sony CD changer.** Community evidence identifying Sony changer communication as UniLink; retained only as bus-family evidence. https://forum.arduino.cc/t/talking-to-a-sony-cd-changer/565235
- **Arduino Forum, controlling a Blaupunkt CDC.** Working Blaupunkt CDC control project and links to earlier DMS/CDC reverse engineering; retained as lower-authority protocol-family evidence. https://forum.arduino.cc/t/controlling-a-blaupunkt-cdc-from-an-arduino-nano-33-iot/1185951
- **Arduino Forum, Blaupunkt DMS/CDC reverse-engineering thread.** Community captures showing a distinct CDC protocol family; exact constants remain non-normative. https://forum.arduino.cc/t/serial-data-interfacing-where-to-start/39850
