# Fiat / Alfa / Lancia ASCI-BUS and changer-family pre-hardware research

This note expands the Alfa 147 Type 937 anchor into a broader Fiat Group changer-family map. The useful pre-hardware finding is not that every Fiat, Alfa Romeo, and Lancia radio is interchangeable. It is that multiple documented factory radios across the group separate **vehicle-network integration** from a dedicated external-changer path, and several explicitly name that changer path **ASCI-BUS**.

The existing `ALFA-937.md` remains the concrete Alfa 147 reference. This file records reusable family evidence and exceptions without turning a commercial application list into physical-compatibility claims.

## Evidence classes

Fiat/Lancia/Alfa eLearn material mirrored by 4CarData is treated as service-documentation evidence. Dension documentation is used as commercial integration evidence: useful for confirming that one emulator ecosystem spans multiple marques, but not proof that every listed head unit speaks an identical protocol.

No ASCI bytes, timings, CAN identifiers, or universal electrical levels are asserted here because none have been captured on the project hardware.

## B-CAN and the changer link are separate integration surfaces

Fiat eLearn documentation for Grande Punto, Bravo, and Croma describes the factory radio as a low-speed B-CAN node. B-CAN carries functions such as anti-theft identity, ignition/on state, speed-dependent volume, illumination, steering-wheel commands, and radio-information repetition.

The same documentation separately says those radios can interface with an external Blaupunkt CD changer through an **ASCI-BUS** line.

That separation is important for PD Bridge. A future adapter does not need to assume that changer audio/control must be tunneled through vehicle CAN merely because the radio itself is a CAN node. The documented architecture provides two distinct research paths:

1. B-CAN for vehicle state, steering controls, and display-related observations where captures prove useful messages exist;
2. the dedicated changer interface for source selection, changer control/state, and analogue audio.

This is materially different from PSA RD4, where the documented changer itself sits on Comfort CAN, and from VAG Gamma-era radios with their own DATA/CLOCK-style changer interface.

## The ASCI family spans multiple Fiat models

The Grande Punto and Nuova Bravo eLearn radio descriptions both explicitly advertise an external Blaupunkt changer through ASCI-BUS while also documenting B-CAN integration.

The Fiat Croma documentation repeats the same architecture: factory radio on low-speed CAN, external Blaupunkt changer through ASCI-BUS, and a separate changer audio input.

Fiat Idea service information goes further and exposes the changer harness roles. Radio-side pins 13-20 are documented as CDC data in/out, permanent and switched/enable supply, CDC data ground, CDC audio ground, and left/right audio. At the changer-side connector, the two data directions are named `ASCI bus CDC - radio` and `ASCI bus radio - CDC`.

This establishes a reusable architectural class rather than just a product-name coincidence: **bidirectional dedicated changer data plus separate analogue stereo audio and power**.

## Panda provides electrical evidence, but only for that target family

Fiat Panda eLearn documents the changer connector in unusual detail:

- CDC RXD and TXD are shown as 5 V / 0 V signals;
- permanent changer supply is shown as 14 V, with a separate switched supply;
- changer audio has its own reference plus left/right analogue channels;
- the radio selects the changer as an audio source and steering-wheel scan keys can move tracks.

This is valuable bench-planning evidence, but it must not be generalized into a universal Fiat Group electrical specification. A future adapter should measure the exact target radio before attaching logic-level hardware.

Dension's own harness list reinforces the need for that caution: it groups Alfa Romeo/Fiat/Lancia under `CABL-AF8` but lists a separate `CABL-FP1` specifically for Fiat Panda. Connector or harness reuse is therefore broad, not absolute.

## Lancia Ypsilon and Musa sit in the same architectural neighborhood

Lancia Ypsilon eLearn publishes a connector map that is strikingly similar to the Fiat examples:

- A1/A3 are the two CAN lines;
- E13/E14 are CDC data in/out;
- E15/E16 are changer supply and enable;
- E17 is CDC data ground;
- E18-E20 are changer audio ground, left, and right.

The radio UI also exposes CD-changer functions.

Lancia Musa documentation independently describes the factory radio as a CAN node and the external changer as an available source. Its Connect Nav+ material explicitly names ASCI-BUS for the external changer and documents steering-wheel control of changer functions.

These sources support treating Fiat and Lancia radios of this era as one **research family**, while still requiring exact head-unit identity before implementation.

## Alfa 159 shares the same changer pin-role pattern

Alfa 159 eLearn documents the factory radio with:

- B-CAN on A1/A3;
- CDC data in/out on E13/E14;
- CDC permanent/enable supply on E15/E16;
- CDC data ground on E17;
- CDC audio ground and left/right audio on E18-E20.

It also documents an external Blaupunkt ten-disc changer as an optional source.

That E13-E20 role pattern matches the documented Fiat Idea/Lancia Ypsilon layout closely enough to justify a shared bench-research hypothesis. It does **not** prove identical protocol bytes, timing, changer-disc-count semantics, or firmware behavior.

The Alfa 147/GT generation should likewise remain a specific subfamily until the exact ALFA-937/related changer signaling is captured. Commercial Mini-ISO adapters make shared ancestry plausible, not proven.

## Changer capacity is a protocol-compatibility dimension

Dension's troubleshooting documentation contains an unusually useful warning for the Alfa/Fiat/Lancia/Maserati group: a Gateway that emulates a six-disc changer may not work, or may work only partly, with head units designed around a five-disc changer.

That warning is commercial product evidence rather than a protocol specification, but it demonstrates that "supports an external changer" is not a sufficient compatibility key. Future PDv1 profiles should record at least:

- exact radio/navigation model and firmware where obtainable;
- expected factory changer type and nominal disc count;
- connector/harness variant;
- whether changer presence needs vehicle configuration or a full power cycle;
- whether steering/display behavior comes from B-CAN, the changer link, or both.

A PD Bridge changer emulator should not hard-code one virtual magazine size across this family before bench testing.

## Navigation units are not automatically the same radio family

Fiat Croma, Panda, Lancia Musa, and other platforms also offered Connect/Connect Nav+ units. Service documentation shows external changer support on several of them, sometimes with ASCI-BUS named explicitly.

That does not make every Connect unit interchangeable with the simpler single-DIN factory radio. Navigation hardware, display ownership, telematics, and software generation can change the integration boundary even when an external Blaupunkt changer is still present.

For compatibility planning, `radio + exact navigation variant + vehicle architecture` remains the safe identity tuple.

## PD Bridge implications

The family evidence suggests a practical future adapter decomposition:

- **direct changer interface:** emulate the documented CDC/ASCI side for source selection, audio injection, and changer-style controls;
- **optional B-CAN observer:** normalize steering controls or source/display state only after target captures establish stable messages;
- **analogue streaming audio:** use the documented changer L/R input path rather than inventing an audio transport on CAN;
- **head-unit-specific dialect profile:** keep magazine size, source handshake, initialization, and any text support outside the generic bridge protocol.

This fits the existing transport-neutral PD Bridge design: the host sees normalized `disc_selected`, `media_control`, `source_state`, and related events while a Fiat-family adapter owns the electrical/protocol details.

## Smallest useful later hardware set

Desk evidence is broad enough that a large model collection is unnecessary for the first bench phase. A useful representative set would be:

1. the existing Alfa 147 / ALFA-937 SW3.17 target;
2. one well-documented Fiat/Lancia ASCI-BUS radio with E13-E20 changer pins, preferably from Panda/Idea/Ypsilon/Grande Punto-era hardware;
3. one later Alfa 159/Bravo/Croma-era B-CAN radio to test whether the apparent pin-role reuse also means protocol reuse;
4. optionally one Connect/Nav unit only after the basic-radio path is understood.

If two representative radios prove protocol-equivalent, the implementation can then expand by verified head-unit identity instead of assuming brand-wide compatibility.

## Questions deliberately left for hardware

- exact ASCI electrical levels on each target radio and whether Panda's 5 V signalling generalizes;
- baud/framing, initialization, keepalive, changer-status, disc/track, and source-selection messages;
- whether five-, six-, and ten-disc OEM units use protocol variants or only different capabilities;
- whether a changer emulator can coexist electrically/logically with any factory changer wiring;
- which steering/source/display state is visible on B-CAN for each target and whether it is necessary at all;
- whether any family member can accept useful text/metadata over the changer path;
- power-cycle or body-computer state needed for newly attached changer detection;
- exact analogue levels, mute behavior, and noise performance of the streaming-audio path.

Until those are measured, this note should not become firmware constants.

## Sources

All links were checked on 2026-09-24.

- **Fiat eLearn, Grande Punto 5570 ACCESSORIES - CAR RADIO.** B-CAN radio functions and external Blaupunkt changer via ASCI-BUS. https://4cardata.info/elearn/199/2/199000000/199000004/199000003/199000619
- **Fiat eLearn, Nuova Bravo 5570T AUDIO SYSTEM.** B-CAN integration plus external Blaupunkt changer via ASCI-BUS. https://4cardata.info/elearn/198/2/198000000/198000002/198000000/198002772
- **Fiat eLearn, Croma INTRODUCTION - ACCESSORIES.** Factory radio as CAN node, steering/display functions, ASCI-BUS external changer and separate changer audio. https://4cardata.info/elearn/194/2/194000000/194000004/194000002/194001961
- **Fiat eLearn, Idea INTRODUCTION - ACCESSORIES.** CDC harness pin roles and explicit ASCI bus radio-to-changer/changer-to-radio signals. https://4cardata.info/elearn/135/2/2010001/2001005/2000744/2401106
- **Fiat eLearn, Panda 5570T CAR RADIO AND CAR TELEPHONE.** CDC RX/TX electrical values, changer power/audio pinout, source selection and steering-wheel changer controls. https://4cardata.info/elearn/169/2/2009000/2000900/2001390/2750971
- **Lancia eLearn, Ypsilon INTRODUCTION - ACCESSORIES.** CAN A1/A3 and E13-E20 CDC data/power/audio pin roles plus changer UI. https://4cardata.info/elearn/101/2/5000045/2000805/2000810/2429858
- **Lancia eLearn, Musa INTRODUCTION - ACCESSORIES (HI-FI).** Factory radio as CAN node and external changer source. https://4cardata.info/elearn/184/2/184000001/184000003/184000002/184000371
- **Lancia eLearn, Musa 5580P CONNECT PANEL.** Connect Nav+ external changer via ASCI-BUS and steering-wheel management. https://4cardata.info/elearn/184/2/184000001/184000003/184000002/184000377
- **Alfa Romeo eLearn, 159 5570 ACCESSORIES.** B-CAN A1/A3, E13-E20 CDC connector roles and optional external Blaupunkt changer. https://4cardata.info/elearn/939/2/939000001/939000000/939000004/939003541
- **Dension, Gateway Lite/Lite BT hardware versions and car-side cables.** `CABL-AF8` Alfa/Fiat/Lancia grouping, separate `CABL-FP1` Fiat Panda harness, and explicit warning that harness families do not imply universal compatibility. https://techsupport.dension.com/638013-W-Gateway-hardware-versions-car-side-cables
- **Dension, Gateway Lite BT troubleshooting.** Alfa/Fiat/Lancia/Maserati recognition/power-cycle guidance and five-disc versus six-disc changer compatibility caveat. https://techsupport.dension.com/775794-N-Gateway-cannot-be-selected-or-any-various-problems
