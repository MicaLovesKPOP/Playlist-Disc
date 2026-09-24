# PSA RD3 / RD4 / RD43 / RD45 pre-hardware family research

This note extends the project's Citroen C3 II / RD4 reference research into a broader PSA head-unit family map. It separates the older VAN-based RD3/RB3 generation from the CAN-based RD4 family and records why later RD43/RD45 names cannot be treated as one universal protocol revision.

The existing C3 RD4 note remains the concrete reference-vehicle anchor. This document is a family map, not a claim that every Peugeot/Citroen application is physically compatible with one adapter.

## Evidence classes

The strongest RD3 wiring evidence is a VDO electrical product specification for RB3/RD3. The RD4 architecture is already sourced in docs/research/CITROEN-C3-RD4.md from Citroen service documentation. Open-source PSA bridge projects are used as reverse-engineering evidence for architecture generations and display/radio coupling, not as target-car truth.

Commercial changer-interface activation guides are retained only as lower-authority evidence that changer presence may require telecoding.

No VAN/CAN frame identifiers from related vehicles are promoted into a normative adapter here.

## RD3/RB3 is a Comfort VAN head-unit family

The VDO RB3/RD3 electrical product specification labels the radio's main data connections as VAN Data and VAN DataB.

The same specification dedicates the blue Mini-ISO changer section to:

- CD-changer VAN Data;
- CD-changer VAN DataB;
- changer bus ground and supply;
- Comfort VAN supply;
- analogue changer audio ground, left input, and right input.

This establishes a clear RD3 architecture: **changer control/state is on the Comfort VAN network while audio is a separate analogue path**.

It is not the VAG-style dedicated DATA/CLOCK serial changer bus and it is not the later PSA Comfort CAN architecture.

## RD3 already exposes factory changer control through the normal OEM UI

Peugeot 206 owner documentation for Audio RD3 describes factory CD-changer selection, disc selection, next/previous track control, and steering-stalk source/track/disc actions.

That makes OEM controls a legitimate PD Bridge target for the RD3/VAN family.

The owner's documentation does not reveal the VAN messages used for those actions, so exact control frames remain hardware/reverse-engineering questions.

## RD3 changer presence may require vehicle configuration

Commercial PSA changer-interface documentation distinguishes VAN vehicles with RD3 from CAN vehicles with RD4 and reports that the CD-changer function must be enabled through PSA diagnostic/telecoding menus when it is not already configured.

This is not manufacturer protocol documentation, so the exact menu procedure should not become normative PDv1 behavior.

It does establish a practical compatibility dimension worth recording in future profiles: a physically compatible changer port may still be unavailable until the vehicle configuration advertises a changer.

## RD4 is a different architecture, not a connector refresh

The existing C3/RD4 research documents Citroen RD4-family service information describing Comfort CAN communication among radio, multifunction display, controls, and CD changer, while changer audio remains separate.

That change from VAN to CAN is a hard family boundary.

A PD Bridge adapter should therefore not attempt to reuse RD3 VAN signaling merely because both generations offer an external changer and a separate display.

## AEE2001, AEE2004/2007, and AEE2010 are meaningful protocol generations

The PSAVanCanBridge project explicitly models conversions among:

- AEE2001 to AEE2004;
- AEE2001 to AEE2010;
- AEE2004 to AEE2010.

It describes AEE2004 and AEE2007 as mostly compatible for its purposes and supports newer RD4/RD43/RD45 head units on the CAN side of its VAN-to-CAN bridge.

This is useful family-boundary evidence: PSA infotainment generations are not interchangeable merely because connectors can be adapted.

The project also states that radio and display are tightly coupled and exchange many messages during operation, which reinforces the need to treat head unit + display generation as one compatibility tuple.

## RD43/RD45 names do not uniquely identify one electrical generation

PSAVanCanBridge material demonstrates RD4/RD43/RD45 support in AEE2004/2007 conversion work, while its broader bridge also handles AEE2010.

Project discussion additionally documents an RD45 variant intended for the later six-pin display generation and distinguishes it by product number.

For Playlist Disc, the safe conclusion is not "all RD45 are AEE2010" or "all RD45 are AEE2004." The safe conclusion is that **model name alone is insufficient**. A future profile must record exact part number, display generation, and vehicle architecture.

This is the same reason concrete compatibility profiles should remain head-unit/vehicle targets rather than brand-level entries.

## Family map

| Family | Established architecture | PD Bridge implication | Still hardware/source gated |
| --- | --- | --- | --- |
| RB3/RD3, AEE2001-era | Comfort VAN on radio and changer; separate analogue changer audio | VAN adapter lane with OEM source/control potential | VAN message IDs, timing, exact radio variants, display traffic |
| RD4, AEE2004-era | Comfort CAN radio/display/changer architecture; separate changer audio | CAN adapter lane; existing C3 reference anchor | exact target frames, bitrate/tap, CD/TOC visibility |
| AEE2007-era derivatives | close enough to AEE2004 for the cited bridge project, but still a named generation | reuse hypotheses permitted, not universal frame claims | per-vehicle/head-unit confirmation |
| RD43/RD45 | appears across later PSA conversion ecosystems; exact generation depends on hardware | require part-number/display-generation identity in profiles | precise AEE mapping by part number, coding, protocol |
| AEE2010-era infotainment | breaking protocol generation relative to AEE2004/2007 | separate CAN-generation adapter work | exact target buses/messages and display coupling |
| RT/SMEG/NAC/RCC navigation families | outside the basic radio scope of this P1 lane | separate future lane only if PDv1 needs them | architecture-specific research |

## Relationship to the existing C3 RD4 reference

The C3 II / RD4 note already establishes the strongest current PSA reference facts:

- a separate multifunction display participates in media UI;
- RD4 levels differ in CD-TEXT/MP3 capability;
- Comfort CAN carries radio/display/changer control/status classes;
- changer audio is separate;
- related AEE2004 reverse engineering exposes promising disc/source/timing categories but target IDs remain capture-gated.

This family note adds the generations around that anchor rather than duplicating it.

## Representative future hardware set

A compact later PSA validation set should prefer generation boundaries:

1. one RD3/RB3 VAN-era head unit with changer preparation and its native display/stalk;
2. the existing C3 II RD4 reference vehicle;
3. one clearly identified RD43/RD45 AEE2004/2007 example;
4. one later RD45/AEE2010 example only if part-number research confirms it as a distinct protocol-generation test.

Testing multiple cars with the same radio/display generation is less valuable than crossing the VAN/CAN and AEE-generation boundaries.

## Questions deliberately left for hardware

Do not infer these from product pinouts or related-platform reverse engineering:

- exact RD3 VAN changer commands, addresses, timing, wake/sleep behavior, or checksums;
- exact RD4/RD43/RD45 target-vehicle CAN identifiers or payloads;
- bus bitrates and safe physical tap points for any concrete vehicle;
- whether the in-dash drive exposes full TOC, only total duration/track count, CD-TEXT, or no useful identity externally;
- exact steering-stalk frames for each architecture;
- exact display-text injection semantics and segmentation;
- whether changer activation/coding is required on a specific vehicle that did not ship with a changer;
- whether an emulator can coexist with factory USB/Bluetooth/changer equipment;
- which RD43/RD45 part numbers belong to AEE2004/2007 versus AEE2010;
- whether the Draft 0.2 audio beacon survives each real radio path.

## Design consequences for PD Bridge

PSA gives the project another strong example of why normalized capabilities are preferable to one universal "car bus" abstraction.

A PSA adapter may obtain:

- selection/control state from VAN on RD3;
- similar logical state from CAN on RD4 and later generations;
- audio through a separate analogue changer path;
- display capability only through the matching radio/display generation.

The PD Bridge host does not need to know whether the vehicle adapter translated VAN, AEE2004 CAN, or AEE2010 CAN. It only needs the capabilities and normalized events that the adapter can prove on that exact target.

## Sources

All links checked on 2026-09-24.

- **VDO Car Communication, Electrical Product Specifications RB3/RD3, mirror by PeugeotTurkey.** RD3/RB3 VAN power/data connector and blue Mini-ISO changer pins carrying VAN Data/DataB plus separate analogue changer audio. https://www.peugeotturkey.com/dosyalar/PDF/rd3.pdf
- **Peugeot 206 owner documentation, mirror by Scribd.** RD3 factory CD-changer operation and steering-stalk source/track/disc controls. https://www.scribd.com/document/344976644/2006-peugeot-206-64834-pdf
- **PSA changer activation guide, mirror by Manualzz.** Commercial integration evidence distinguishing VAN/RD3 from CAN/RD4 and documenting changer telecoding as a practical installation requirement. https://manualzz.com/doc/5222272/xcarlink--gateway-changeur-cd-guide-d-utilisation
- **morcibacsi, PSAVanCanBridge v3.** AEE2001/AEE2004/AEE2010 conversion boundaries, AEE2004/2007 relationship, RD4/RD43/RD45 support, remote-stalk support, and radio/display coupling. https://github.com/morcibacsi/PSAVanCanBridge/blob/v3/readme.md
- **morcibacsi, PSAVanCanBridge discussion #11.** Lower-authority implementation discussion documenting an RD45 product-number variant for the later six-pin display generation. https://github.com/morcibacsi/PSAVanCanBridge/discussions/11
- **morcibacsi, PSACANBridge.** AEE2004/2007 to AEE2010 as a breaking CAN-generation conversion problem. https://github.com/morcibacsi/PSACANBridge
- **Citroen RD4-family source set.** See docs/research/CITROEN-C3-RD4.md for the manufacturer/service and reverse-engineering evidence already pinned to the project's concrete RD4 reference architecture.
