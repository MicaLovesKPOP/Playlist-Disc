# Opel / Vauxhall CD30 / CDC40 / CD70 pre-hardware family research

This note maps the common mid-2000s Opel/Vauxhall infotainment family around CD30/CD30 MP3, CDC40 Opera, CD70 Navi and related Quadlock-era systems.

The useful pre-hardware result is not a universal Opel protocol claim. It is the boundary that these radios participate in a tightly integrated vehicle/display/control environment and should be treated as a head-unit + display + vehicle-network family.

## Evidence classes

Opel/Vauxhall infotainment manuals establish the user-facing radio/display/steering architecture. Dension integration documentation establishes a dedicated Opel Quadlock hardware/cable family for its CAN-era Gateway products. Commercial AUX/interface material is lower-authority evidence for practical connector/source availability.

No CAN identifiers, coding values, security-pairing procedures, or source-control frames are promoted into PDv1 here.

## CD30/CD30 MP3 depends on the vehicle information display

The Vauxhall/Opel CD30 infotainment documentation says the system is operated from both the central head-unit controls and steering-wheel controls, and that behavior varies with the installed information display.

The manual explicitly distinguishes Triple-Info-Display (TID) and Graphic-Info-Display (GID) variants.

For Playlist Disc, that is enough to treat the display generation as part of the compatibility tuple. A "CD30" profile without display type is incomplete.

## CD70 Navi exposes radio/CD state through GID/CID and steering controls

The CD70 Navi documentation states that Graphic Info Display or Colour Info Display shows radio, CD-player and navigation information.

It also documents steering-wheel controls that switch radio/CD mode and skip tracks.

That proves the factory system already has the two PD Bridge surfaces we care about:

- OEM media controls;
- a separate vehicle display carrying audio state.

It does not prove which internal CAN messages implement those functions.

## CDC40 Opera is a different source topology despite sharing the vehicle UI family

The CDC40 Opera manual documents:

- steering-wheel remote control;
- menu/display integration;
- a built-in multi-disc CD changer;
- direct disc selection through the factory UI.

That means CDC40 should not be treated as "CD30 plus external changer." Its changer is part of the head unit itself, so an external changer-emulation strategy may not apply at all.

For PDv1 the distinction matters because physical-token recognition may still work through the built-in drive while streamed-audio/source integration could require AUX, another factory source, or a separate vehicle-network strategy.

## Dension identifies a dedicated Opel Quadlock integration family

Dension's Gateway Pro BT hardware documentation lists a dedicated Opel hardware revision (GWPC13B) and an Opel Quadlock car-side cable (CABP-OC2).

The same document explicitly warns that cable/hardware families do not imply universal compatibility across a marque.

This is useful family evidence: the mid-2000s Opel lane is not merely generic ISO audio wiring. It warrants an Opel-specific Quadlock/CAN integration family, but concrete compatibility must still be recorded per head unit and vehicle/display combination.

## Family map

| Family | Established pre-hardware architecture | PD Bridge implication | Still hardware/source gated |
| --- | --- | --- | --- |
| CD30 / CD30 MP3 + TID | head unit plus separate basic information display and steering controls | normalized controls may be available; display capability may be limited | exact CAN path/messages; external source behavior; coding |
| CD30 / CD30 MP3 + GID | same radio family with richer graphic display | stronger metadata/display target | exact text injection and ownership |
| CDC40 Opera | integrated multi-disc changer, steering controls and GID-class display integration | physical-disc lane remains useful; streaming source likely differs from external-CDC emulation | external source options, CAN semantics, display injection |
| CD70 Navi / DVD90-class | navigation + separate GID/CID audio display and steering controls | rich OEM UI target, but navigation integration raises coupling | exact network/source behavior and module pairing |
| later Renault/Nissan-derived or touchscreen units | different generation | separate lane if later needed | architecture-specific research |

## Smallest useful later hardware set

A compact Opel validation set should prefer topology differences:

1. one CD30/CD30 MP3 car with TID or GID;
2. one CDC40 Opera if integrated-changer behavior is worth testing;
3. one CD70 Navi/GID or CID system only if display/metadata injection becomes a priority.

Testing several Astra H cars with the same radio/display tuple is less useful than crossing those topology boundaries.

## Questions deliberately left for hardware

- exact CAN buses, bitrates and frame identifiers carrying steering/audio/display state;
- whether CD track count, total time, full TOC or CD-TEXT leaves the head unit;
- source-selection and AUX activation behavior on exact part/software revisions;
- whether external changer emulation exists on CD30/CD70 variants and how it differs from CDC40;
- radio/display/module pairing and diagnostic coding requirements;
- whether arbitrary now-playing text can be injected without breaking display ownership;
- coexistence with navigation, phone and factory amplifier modules;
- whether the Draft 0.2 audio beacon survives each real head-unit path.

## Sources

All links checked on 2026-09-24.

- **Vauxhall/Opel CD30/CD30 MP3 infotainment manual.** Central controls plus steering-wheel controls and TID/GID display-dependent operation. https://business.citroen.be/content/dam/vauxhall/Home/owners/infotainment-manuals/astra/mg_astra_kta-2733_1-vx-en_eu_my13_ed0712_3_en_vx_online.pdf
- **Opel CD70 Navi infotainment documentation.** Graphic/Colour Info Display audio information plus steering-wheel radio/CD and track controls. https://opel-infos.de/media/kta/2587_0_D_GB.pdf
- **Opel CDC40 Opera manual, mirror by Manualzz.** Steering-wheel control, menu/display integration and integrated CD-changer operation. https://manualzz.com/doc/4487592/opel-cdc-40-opera-infotainment-system-bedienungsanleitung
- **Dension Gateway Pro BT hardware/cable documentation.** Dedicated Opel hardware revision and CABP-OC2 Opel Quadlock cable; explicitly warns that a cable family is not universal marque compatibility. https://techsupport.dension.com/899846-Y-Gateway-hardware-versions-car-side-cables
- **Opel Zafira infotainment product information, mirror by opel-infos.de.** CD30 MP3, CDC40 Opera and CD70 Navi display/steering-wheel equipment distinctions. https://www.opel-infos.de/media/files/opel-infos_2010-12-00_726.pdf
