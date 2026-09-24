# Compatibility coverage research plan

Playlist Disc should aim for broad old-car compatibility without pretending that every vehicle variant can be solved before hardware exists.

The scalable unit of pre-hardware research is the **head-unit / integration family**, not the car badge. A single radio, changer interface, display bus, or optical-network family may span many models and sometimes multiple marques. Conversely, one car model may have several fundamentally different radio/navigation options.

This document defines which remaining families are worth researching, how far that research should go before hardware, and when the compatibility-research phase is broad enough to stop expanding.

## What "widest compatibility within reason" means

PDv1 has two distinct compatibility layers:

1. **Physical token compatibility** - can an ordinary finalized CD-DA disc load and play well enough for TOC, CD-TEXT, or the audio beacon to be useful?
2. **Vehicle integration compatibility** - can an adapter observe useful disc state, normalize OEM controls, switch/reroute audio, or use the factory display?

The first layer is intentionally generic. The second is where family-specific research matters.

Commercial changer-emulator ecosystems are useful discovery evidence because they show that broad reuse exists, but they are **not PDv1 compatibility proof**. Dension explicitly describes the head unit, rather than vehicle model alone, as the key compatibility boundary for changer-emulation products.

## Admission rule for a research family

A family belongs in the near-term plan when it satisfies at least two of these conditions:

- factory CD or CD-changer integration was common during the target old-car era;
- the same head-unit/interface family spans many models or multiple marques;
- manufacturer/service documentation or a mature third-party integration ecosystem exists;
- OEM steering controls or a factory display offer useful PD Bridge surfaces;
- representative hardware appears realistically obtainable for later testing.

A family can be deferred when documentation is too weak, the installed base is unusually narrow, the system is effectively inseparable from proprietary hardware, or researching it would duplicate an already understood integration class without adding meaningful coverage.

Do not create a vehicle compatibility profile merely because a brand appears in an adapter catalog. Profiles remain concrete head-unit/vehicle targets intended for eventual physical reports.

## Existing reference anchors

The three current reference vehicles remain valuable because they anchor three materially different architectures:

- **Alfa Romeo 147 / ALFA-937 SW3.17** - legacy copper changer integration plus B-CAN participation.
- **MINI R55 Boost CD / RAD2** - K-CAN plus MOST optical infotainment gateway/changer architecture.
- **Citroen C3 II / RD4 family** - Comfort CAN radio/display/changer architecture with a separate multifunction display.

These are anchor points, not the intended limit of compatibility research.

## Remaining high-value research matrix

| Priority | Family / lane | Reach to establish | Current state | Pre-hardware deliverable |
| --- | --- | --- | --- | --- |
| P1 | VAG legacy + Quadlock CDC | Volkswagen, Audi, SEAT, Skoda; split mini-ISO/legacy CDC from later Quadlock/CAN where necessary | sourced family note | Legacy Gamma direct CDC, RCD 300 CAN + separate CDC, later RCD/BAP/MDI boundaries, Audi copper separation, Skoda pinout caveat, and Audi MMI optical exclusion mapped in docs/research/VAG-LEGACY-QUADLOCK.md. |
| P1 | BMW/MINI legacy CDC | Older BMW/MINI 17-pin/40-pin and changer-era systems outside the R55 RAD2/MOST anchor | sourced family note | BMW NG I/K-Bus + separate changer audio, remote BM24/BM54 radio-module boundary, R50/R53 K-Bus changer wiring, connector generations, and the MOST transition mapped in docs/research/BMW-MINI-LEGACY-CDC.md. |
| P1 | PSA legacy + later RD4 derivatives | Peugeot/Citroen RD3/VAN plus RD4/RD43/RD45 generation boundaries | sourced family note | RD3 Comfort-VAN changer control + separate audio, the RD4 CAN boundary, AEE2001/2004-2007/2010 generations, and RD43/RD45 identity caveats mapped in docs/research/PSA-RD3-RD4-FAMILY.md. |
| P1 | Fiat/Alfa/Lancia legacy CDC | Broader Fiat Group changer ecosystem around the Alfa 937 anchor | sourced family note | B-CAN versus dedicated ASCI-BUS surfaces, E13-E20 CDC role reuse, Panda electrical/harness exception, Alfa 159/Lancia family overlap, and changer-capacity dialect caveat mapped in docs/research/FIAT-ALFA-LANCIA-CDC.md. |
| P1 | Renault changer/CAN families | Tuner List, Update List and later CAN-era factory radios | sourced family note | Tuner List/Update List display topologies, dedicated CDC/S-PDIF path, documented CAN display/control coupling, and later Radio+/Continental Quadlock boundary mapped in docs/research/RENAULT-TUNER-UPDATE-LIST.md. |
| P1 | Ford Europe factory audio | 5000/6000/Sony/TravelPilot-era CD and changer integrations, split by connector/network generation | sourced family note | Older 12-pin Ford ACP changer systems separated from later 5000C/6000CD/6006CD Quadlock/CAN and OEM Sony branches in docs/research/FORD-ACP-QUADLOCK.md. |
| P1 | Opel/Vauxhall CAN audio | Quadlock/CAN CD/changer-era systems such as CD30/CD70/CDC40-class families | sourced family note | CD30 TID/GID, CDC40 integrated-changer, CD70 GID/CID and dedicated Opel Quadlock/CAN integration boundaries mapped in docs/research/OPEL-CD30-CDC40-CD70.md. |
| P1 | Toyota/Lexus factory CDC | High-volume Japanese OEM changer-port families | sourced family note | AVC-LAN/IEBus multimedia architecture, working changer-emulator/decoder evidence, coexistence constraints, and later-generation exclusions mapped in docs/research/TOYOTA-LEXUS-AVCLAN.md. |
| P1 | Honda/Acura factory CDC | Honda/Acura changer-era factory radios | sourced family-boundary note | Older OEM Alpine/M-Bus systems separated from the later Honda-specific white-connector family, with built-in changer/navigation/XM caveats and low-level protocol work explicitly deferred to bench captures in docs/research/HONDA-ACURA-CDC.md. |
| P1 | Mazda factory CDC/CAN | Legacy changer ports plus later CAN-integrated radios | sourced family-boundary note | Legacy external-CDC systems, Mazda 6/RX-8 revision caveats, and the later CAN-bus generation mapped in docs/research/MAZDA-CDC-CAN.md; protocol constants remain bench-gated. |
| P1 | Aftermarket head-unit buses | Alpine, Becker, Blaupunkt, Clarion, Pioneer, Sony, JVC and other widely fitted legacy units | sourced family note | Alpine M-Bus/Ai-NET, Pioneer IP-Bus, Sony UniLink, Clarion CeNET, Blaupunkt DMS/CDC and lower-priority vendor buses mapped as protocol-plugin families in docs/research/AFTERMARKET-HEAD-UNIT-BUSES.md. |
| P2 | Audi MMI 2G / VAG optical | Optical VAG infotainment outside ordinary copper/Quadlock radio families | planned | Characterize optical changer semantics separately from copper/Quadlock VAG radios; avoid assuming R55 MOST behavior transfers. |
| P2 | Mercedes/Porsche/Saab optical | D2B/MOST changer-era systems with mature optical gateway products | planned | Establish generation boundaries, coding requirements, display/control capability, and whether one adapter architecture can sensibly serve multiple marques. |
| P2 | Volvo legacy + optical | HU/MELBUS-era and later optical infotainment families | planned | Determine whether legacy and optical generations offer distinct high-leverage integration paths. |
| P2 | Nissan/Infiniti factory CDC | Changer-capable OEM families | planned | Identify reusable head-unit generations and whether documentation/ecosystem quality justifies promotion to P1. |
| P2 | Hyundai/Kia/Suzuki/Subaru | Additional high-volume changer-era families visible in commercial adapter catalogs | planned | Group only where a real shared interface family is demonstrated; otherwise keep brand families separate or defer. |
| P2 | Chrysler/Jeep and other regional families | Useful mainly for non-European expansion | planned | Research after P1 lanes unless readily available hardware or unusually strong documentation makes the work cheap. |

P1 means the family should receive a sourced pre-hardware note before declaring compatibility research broadly complete. P2 means worthwhile expansion, but not at the cost of indefinitely delaying physical validation.

## Required output from each family pass

A useful family research note should establish, with sources:

- exact radio/navigation families and the model/era boundary they actually cover;
- connector and network architecture at a level safe to state without captures;
- factory CD/CD-changer, CD-TEXT, steering-control, and display capabilities where documented;
- whether changer emulators replace, coexist with, or require coding for the factory changer;
- which integration class applies: direct copper CDC, vehicle-network-mediated, optical MOST/D2B, proprietary serial bus, or aftermarket head-unit bus;
- which claims come from manufacturer/service documentation versus commercial compatibility data or community reverse engineering;
- the smallest practical representative hardware set for later physical testing;
- explicit hardware-gated questions: frame IDs, timings, electrical levels, source-selection handshakes, display injection, and target-unit behavior.

Related-platform reverse engineering may define a capture hypothesis, but never becomes target-unit truth without a target capture/report.

## Research status

The P1 family sweep is complete for the pre-hardware phase. Each lane now has a sourced architecture/family note or an explicit boundary where low-level work is intentionally deferred to representative bench captures.

P2 optical/premium and regional families remain worthwhile future expansion, but they are **not** a prerequisite for first hardware validation. MINI R55/RAD2 already anchors an optical MOST architecture, while the P1 set covers direct changer buses, vehicle-network-mediated systems, proprietary multimedia buses, and aftermarket head-unit buses.

From this point, prefer physical evidence or a genuinely new architecture over adding more model names to existing families.

## Stop rule for pre-hardware breadth

Compatibility research is broad enough for the pre-hardware phase when all of the following are true:

- every P1 lane has either a sourced family note or an explicit evidence-based reason to defer/drop it;
- the repository has characterized at least one reusable family in each major integration class: direct copper CDC, CAN/vehicle-network-mediated, optical MOST/D2B, and aftermarket head-unit bus;
- the three reference anchors have documented family boundaries so their findings are not accidentally generalized to unrelated radios;
- the generic audio-beacon fallback remains available for cars where useful vehicle-side state cannot be accessed;
- additional desk research would mostly add more model names rather than a new integration architecture or materially new design constraint.

These conditions are now met for the planned P1 breadth. Physical testing should take priority after the remaining format/software readiness gates are closed. New P2 families can still be added opportunistically when hardware, contributors, or materially new architecture justify them.

## Discovery sources and what they prove

These sources justify the **research map**, not PDv1 compatibility claims:

- **Dension, Compatibility.** States that changer-emulator compatibility is primarily determined by the installed head unit and that unsupported head units should not be assumed compatible. https://techsupport.dension.com/061228--Compatibility
- **Dension, Gateway Lite / Lite BT hardware and car-side cables.** Shows separate reusable harness families for Alfa/Fiat/Lancia, Audi mini-ISO and Quadlock, BMW 17-pin and 40-pin, Honda/Acura, Mazda, Renault, Skoda, Suzuki, Toyota/Lexus, and Volkswagen mini-ISO/Quadlock. https://techsupport.dension.com/638013-W-Gateway-hardware-versions-car-side-cables
- **Dension, Gateway Pro BT hardware and car-side cables.** Shows CAN/Quadlock-era groupings for Audi, BMW, Peugeot/Citroen, Opel, and Volkswagen. https://techsupport.dension.com/899846-Y-Gateway-hardware-versions-car-side-cables
- **Dension, Gateway 500 install guide.** Documents changer-emulation use on optical MOST-era Audi, BMW/MINI, Mercedes, Porsche, and Saab systems, including coding requirements on some platforms. https://www.dension.com/files/products/gateway_500/gateway-500-install-guide.pdf
- **Yatour Digital Music Changer application guide.** Provides broad discovery coverage across European, Japanese, and Korean OEMs and legacy aftermarket head-unit brands. https://manuals.plus/m/bdc75a321375bccd54f0a8c7e4654be92b9bba30e475b35fb375c0a047cd4f2a

All links checked on 2026-09-24. Commercial compatibility catalogs are discovery evidence only; each promoted family still needs its own sourced technical note before implementation assumptions are made.
