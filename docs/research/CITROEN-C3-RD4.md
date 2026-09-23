# Citroen C3 II / RD4-family pre-hardware integration research

This note records source-backed information that can shape a future PD Bridge adapter for the non-navigation Citroen C3 II / RD4-family setup used as the project's third reference vehicle.

The target car is already observed to have steering-stalk media controls and a separate orange multifunction display that can show track/title information. Those are **target-car observations**, not proof of any particular CAN frame or RD4 hardware level.

The sources below deliberately separate three evidence classes:

1. C3 owner's documentation describing the factory user interface;
2. Citroen RD4-family service documentation describing architecture;
3. reverse-engineered AEE2004-era PSA traffic from related vehicles.

Only later captures can prove which low-level details apply unchanged to the target C3.

## Evidence established by the C3 owner's guide

### Factory audio controls and a separate multifunction screen are part of the platform

The 2009 C3 owner's guide identifies audio-equipment steering controls, a multifunction screen, and either MyWay or the Audio system in the dashboard.

For Monochrome Screen C it explicitly lists audio sources including radio, CD, USB and jack input, and says audio-related menus are operated from the Audio system control panel.

The same guide describes USB/portable-audio files as manageable through the steering controls or audio control panel and displayable on the multifunction screen.

For PDv1 this confirms the **user-facing architecture** we care about: an OEM control surface and a physically separate OEM display already participate in media interaction. It does not tell us which CAN frames implement them.

## Evidence established by RD4-family service documentation

### CD-TEXT and MP3 depend on RD4 level

Citroen's RD4 audio presentation describes three RD4 levels:

- Level 1: no CD-TEXT;
- Level 2: CD-TEXT;
- Level 2+: CD-TEXT plus MP3 CD playback.

The document explains that RD4 can read CD-TEXT song/artist/title information from a disc and display it on the multifunction screen.

That is important because it establishes a **factory optical-disc-metadata → separate-display path** within the RD4 family. It still does not prove which RD4 level or firmware is installed in the target C3, so PDv1 must not mark CD-TEXT capability as measured yet.

### Control/display communication is multiplexed; changer audio is separate

The RD4 service presentation's connection table describes COMFORT CAN communication for:

- radio status and requests involving the multifunction display;
- radio control including tuner/source/volume/audio/CD functions;
- CD-changer display information;
- CD-changer status/control.

The same table describes changer audio to the radio separately as an analogue connection.

That split is architecturally useful. A future C3 adapter may be able to use vehicle-network information for selection/control/display while leaving streamed audio on an analogue or existing audio-interface path.

The source document is for the C6, so it should be treated as **RD4-family architecture**, not proof of exact C3 wiring or message identifiers.

## Existing AEE2004/2007 reverse engineering

### RD4, remote stalk and display are known to be tightly coupled on PSA CAN

The open-source PSAVanCanBridge project states that AEE2004 and AEE2007 are mostly compatible, supports RD4/RD43/RD45 and radio remote-stalk functionality, and notes that the radio and display exchange a large number of messages during operation.

This is valuable implementation groundwork, but the project's own compatibility statements are broader than its directly tested vehicles. We should therefore use it to choose what to capture, not to declare the target C3 solved.

### Related PSA cars expose almost the perfect PDv1 information set

The AutoWP PSA CAN reverse-engineering reference is explicitly based on vehicles including a Peugeot 407 and Citroen C4 variants, not the target C3. On those related systems it documents:

- **0x0A4** — current CD track text/author from radio to display;
- **0x165** — radio status/source, including tuner, CD, changer, AUX, USB and Bluetooth states;
- **0x325** — CD tray insert/eject/present/ready state;
- **0x365** — CD disc information including number of tracks and total minutes/seconds;
- **0x3A5** — current playing CD track and timing;
- **0x131** — radio CD-changer command;
- additional Yatour-observed changer status/current-disc traffic.

For Playlist Disc, 0x365 is particularly interesting: **track count + total disc duration alone can already identify a deliberately designed PDv1 token candidate**, while the full TOC remains the stronger canonical identity.

But we must not put those numeric IDs into a C3 implementation until the target car confirms them. They are excellent sniffing hypotheses, not specifications.

## Architectural implications for PD Bridge

The evidence supports a promising layered design for the C3/RD4 reference platform:

1. **Disc recognition:** first investigate whether the RD4 publishes tray/disc/track information on its Comfort CAN traffic. If target captures resemble the related-platform 0x325/0x365 class, PDv1 may identify discs before the audio beacon is ever heard.
2. **Controls:** normalize steering-stalk and head-unit media actions into PD Bridge events only after target capture confirms their transport.
3. **Streaming audio:** a changer/AUX/Bluetooth interface can remain an audio transport independent of disc identity.
4. **Display metadata:** because the factory radio already sends audio information to a separate display, future now-playing injection is plausible as a research target, but exact formatting, segmentation, frame IDs and arbitration behavior are capture-gated.
5. **Fallback:** if the bus exposes insufficient optical-disc identity, the universal repeated audio beacon remains available.

Among the three reference cars, this remains a particularly attractive reverse-engineering target because the documented RD4 family and related PSA CAN captures expose the same categories of state PDv1 wants.

## Questions deliberately left for hardware

Do not answer these from the related-platform references alone:

- exact RD4 manufacturer/part number/software level in the target C3;
- whether it is Level 2 or Level 2+ and whether its CD-TEXT behavior matches the service presentation;
- target vehicle's exact AEE architecture/revision;
- whether related-platform frame IDs 0x0A4, 0x165, 0x325, 0x365, 0x3A5 and 0x131 appear unchanged;
- bus bitrate, wiring/tap point and termination details for the target installation;
- whether full or only coarse TOC information is externally visible;
- exact steering-stalk frame(s);
- whether arbitrary metadata can be injected without upsetting the radio/display state machine;
- whether source switching can be automated safely;
- whether the Draft 0.2 audio beacon survives the real optical/audio path.

Until measured, the repository should not promote any of those values into normative vehicle-adapter code.

## Sources

All links were checked on 2026-09-24.

- **Citroen C3 2009 Owner's Guide, mirror by CarManualsOnline.** Audio steering controls, separate multifunction screen, audio-system layout, Monochrome Screen C audio-source display, and USB/audio control/display behavior. https://www.carmanualsonline.info/citroen-c3-2009-owners-manual
- **Citroen service documentation, C6 - D4EABAP0 - Presentation : Audio system, mirror by Scribd.** RD4 levels, CD-TEXT/MP3 support, multifunction-display integration, Comfort CAN control/display paths and changer control/audio architecture. https://www.scribd.com/document/821708464/C6-Audio-System-Presentation
- **morcibacsi, PSAVanCanBridge v3.** AEE2004/AEE2007 compatibility statement, RD4/RD43/RD45 support, radio remote stalk and radio/display coupling. https://github.com/morcibacsi/PSAVanCanBridge/blob/v3/readme.md
- **AutoWP PSA CAN reverse-engineering reference.** Related-platform CAN-INFO traffic for CD text, radio source, tray/disc/track state and changer commands; explicitly based on Peugeot 407 / Citroen C4-family and other reference sources rather than the target C3. https://autowp.github.io/
