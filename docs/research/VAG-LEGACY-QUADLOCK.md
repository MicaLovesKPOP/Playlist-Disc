# VAG legacy and Quadlock CDC pre-hardware family research

This note maps reusable Volkswagen Group head-unit / changer architectures that are worth treating as PD Bridge compatibility families. It is intentionally **not** a claim that every Volkswagen, Audi, SEAT, or Skoda with a similar-looking connector behaves identically.

The purpose is to keep later adapter work from collapsing several different generations into one misleading "VAG Quadlock" bucket.

## Evidence classes

The strongest architecture evidence below comes from Volkswagen/Audi service documentation mirrored by Workshop Manuals. Dension material is used as commercial integration evidence: it is valuable for identifying real head-unit family boundaries, but it does not prove PDv1 behavior or undocumented protocol details.

No CAN identifiers, changer bytes, clock rates, electrical levels, or source-selection timing are promoted here. Those remain capture or bench-test questions.

## Legacy Volkswagen changer wiring

Volkswagen Golf Mk3 Gamma service information documents a dedicated 10-pin red connector with CD-changer DATA IN, CLOCK IN, DATA OUT, switched supply, grounds, and left/right LINE IN.

Later Golf Cabriolet Gamma documentation uses the blue part of a 20-pin multipart connector instead, but exposes the same classes of signals: changer DATA IN, DATA OUT, CLOCK, supply, control, audio earth, and left/right audio.

This establishes two bounded facts:

- the physical connector changed across generations;
- the changer architecture remained visibly separate from ordinary speaker/radio wiring and used dedicated digital control plus analogue stereo audio.

It does not establish that the byte protocol or timings are identical between those generations.

For PD Bridge, this is the classic direct-CDC integration class: a future adapter could potentially emulate a changer for source/audio/control purposes while using an independent PDv1 recognition path.

## Mk5 RCD 300: CAN radio plus separate changer interface

Volkswagen Golf Mk5 RCD 300 service documentation is especially useful because it shows both integration layers on one head unit.

The connector overview identifies a power connector carrying CAN high/low and a separate 12-pin connector dedicated to CD-changer control and CD audio. The detailed changer connector exposes changer DATA OUT, DATA IN, CLOCK, control, supply, audio ground, and left/right analogue audio.

Volkswagen also documents an optional external six-disc changer for the RCD 300 and states that the integrated drive accepts ordinary CD-R and CD-RW audio discs.

This gives PDv1 an important architecture result: **a CAN-connected radio is not necessarily a CAN-controlled changer**. Vehicle/UI state and changer emulation can belong to different buses on the same head unit.

A future RCD 300 adapter should therefore keep at least three questions separate:

1. physical Playlist Disc recognition from the in-dash drive;
2. changer/source/audio emulation on the dedicated changer path;
3. steering/display/vehicle state on CAN where useful.

## RCD 310 / RCD 510: same signal classes, newer integration choices

Volkswagen service information for RCD 310 and RCD 510 still documents a 12-pin connector with CD-changer DATA OUT, DATA IN, CLOCK, control, supply, and analogue left/right audio, while the radio itself also has CAN connections.

For RCD 310, Volkswagen separately documents that the centre-console location can contain either a CD changer or a multimedia control unit, but not both.

This matters because later integration products may use the multimedia-device path rather than pretending to be the old changer even though changer pins still exist on the radio.

Do not infer from shared signal names that RCD 300, RCD 310, and RCD 510 accept identical changer framing.

## Quadlock is a connector family, not a protocol family

Dension's product documentation separates multiple car-side harnesses and software families inside the Volkswagen/Audi ecosystem:

- Volkswagen mini-ISO;
- Volkswagen Quadlock;
- Audi mini-ISO;
- Audi Quadlock;
- Volkswagen BAP Quadlock;
- Volkswagen "single CAN" Quadlock.

Dension explicitly warns that a cable/hardware family does not mean every vehicle in a marque is supported, and its general compatibility guidance identifies the installed head unit as the key compatibility boundary.

The Gateway Pro BT manual goes further for CAN-BAP systems such as RCD 310, RCD 510, and RNS 510: that product emulates factory MDI/telephone functions rather than merely presenting itself as a classic CD changer, and later vehicles may require coding for Media Player 3 and Telephone.

This is a critical boundary for Playlist Disc. The project should never choose an adapter implementation from "it has Quadlock" alone. Connector shape, radio generation, enabled options, and control protocol all matter.

## Audi copper systems are a separate subfamily

Dension documents separate Audi mini-ISO and Audi Quadlock harnesses, and its Audi Dual-CAN Gateway Pro material uses CD-changer mode while putting its own menu/ID3 information on the instrument-cluster display rather than the radio display.

That commercial behavior is useful evidence that Audi changer/source integration can coexist with CAN-backed steering/cluster interaction, and that radio-display and cluster-display capabilities are not interchangeable.

Audi should therefore not be treated as merely a Volkswagen pinout with a different badge. Exact Concert/Symphony generations and target models still need their own sourced boundary pass before a concrete compatibility profile is created.

## Audi MMI optical systems are a separate architecture

Audi A4 MMI service documentation explicitly places the CD changer on the MOST bus and lists MOST as the infotainment interconnect.

That is enough to exclude MMI optical systems from the copper/Quadlock CDC family. They belong in the separate P2 optical lane alongside other MOST/D2B research.

A successful copper VAG adapter therefore says nothing about MMI changer emulation, MOST function blocks, ring management, or coding.

## Family map

| Family | Established architecture | PD Bridge implication | Still hardware/source gated |
| --- | --- | --- | --- |
| VW legacy Gamma, red T10 | dedicated DATA IN/OUT + CLOCK + analogue L/R | direct-CDC class | exact framing, electrical levels, activation |
| VW later Gamma, blue multipart/mini-ISO era | same documented signal classes on newer connector | reusable direct-CDC design pattern, not proven protocol identity | framing/timing and exact radio coverage |
| VW RCD 300 | radio on CAN plus separate serial-control/analogue CDC connector | split CAN vehicle/UI work from changer/audio work | button/display traffic, CDC protocol, source handshake |
| VW RCD 310 / RCD 510 | CAN radio plus dedicated CDC pins; multimedia-device alternatives exist | treat CDC and MDI/BAP paths as distinct integration choices | exact generation/coding behavior and best runtime path |
| VW BAP-era RCD/RNS integrations | commercial adapters use factory MDI/telephone semantics and may require coding | separate BAP/MDI subfamily, not generic Quadlock CDC | BAP messages, coding matrix, target-unit behavior |
| Audi mini-ISO / Quadlock copper systems | commercial changer-mode integration plus CAN/cluster surfaces | separate Audi copper subfamily | exact Concert/Symphony generation mapping and protocol |
| Audi MMI | MOST optical infotainment including CD changer | separate optical adapter architecture | MOST protocol/function blocks/coding |

## SEAT and Skoda boundary

Commercial adapter catalogs show that some SEAT and Skoda applications reuse broader VAG integration hardware. Dension also documents a dedicated older Skoda cable before Skoda adopted Volkswagen pinouts, and separately documents that some Skoda Stream/Dance units were produced with either Skoda-specific or Volkswagen-style changer pinouts.

That is strong enough to justify keeping SEAT/Skoda inside the VAG research lane, but **not** strong enough to declare their radios equivalent to the Volkswagen families above.

A later source pass should map concrete SEAT/Skoda head-unit names to these architecture families or explicitly leave them separate.

## Representative future hardware set

The smallest useful later hardware set should favor architectural diversity rather than model count:

1. one legacy VW Gamma-class direct-CDC unit;
2. one Mk5 RCD 300-class CAN + separate-CDC unit;
3. one later BAP-capable RCD/RNS unit where MDI/coding behavior can be observed;
4. one Audi copper Concert/Symphony-family unit;
5. Audi MMI only when the separate optical P2 lane reaches hardware.

One good example of each class is more informative than testing several cars with the same radio generation.

## Questions deliberately left for hardware

Do not infer these from connector pin names or commercial compatibility lists:

- exact serial changer bytes, baud/clock rate, voltage levels, timing, keep-alives, or source-selection handshake;
- whether one captured CDC protocol is reusable unchanged across Gamma, RCD 300, RCD 310, and RCD 510;
- which in-dash CD states, TOC data, CD-TEXT, track timing, or load/eject events are visible on vehicle CAN;
- exact steering-wheel and cluster-display traffic for any target vehicle;
- whether a changer emulator can coexist with a factory changer or multimedia interface on a specific installation;
- which coding options are required on a specific BAP-era vehicle;
- whether a target radio exposes enough information for PDv1 recognition without the audio beacon;
- whether the Draft 0.2 beacon survives each real optical/audio path;
- any Audi MMI MOST messages or function blocks.

## Design consequences for PD Bridge

The VAG family pass establishes a reusable rule: **vehicle-network integration and changer integration must be modeled independently**.

A VAG adapter should expose normalized PD Bridge capabilities rather than leaking its underlying implementation:

- disc detection should advertise only recognition channels actually proven on that target;
- media controls may come from CAN or another OEM control path;
- automatic source switching may be implemented through CDC, MDI/BAP, or not at all;
- metadata display may target a radio, cluster, or neither;
- analogue streaming audio can remain separate from the physical-disc identity path.

This keeps one host runtime usable even though the VAG radio families underneath it are materially different.

## Sources

All links checked on 2026-09-24.

- **Volkswagen service information, Golf Mk3 Gamma, mirrored by Workshop Manuals.** Legacy red T10 changer DATA IN/CLOCK/DATA OUT, power and analogue LINE IN assignments. https://workshop-manuals.com/volkswagen/golf-mk3/vehicle_electrics/electrical_system/infotainment/radio_systems/radio_system_quot%3Bgammaquot%3B/
- **Volkswagen service information, Golf Cabriolet Gamma, mirrored by Workshop Manuals.** Later blue multipart connector with changer DATA IN/OUT, CLOCK, control, supply and analogue audio. https://workshop-manuals.com/volkswagen/golf-mk3/vehicle_electrics/electrical_system/infotainment/radio_systems_for_golf_convertible_05.98_/radio_system_quot%3Bgammaquot%3B/
- **Volkswagen service information, Golf Mk5 RCD 300 connector overview, mirrored by Workshop Manuals.** Separate CAN/power connector and 12-pin CD-changer control/audio connector. https://workshop-manuals.com/volkswagen/golf-mk5/vehicle_electrics/communication/infotainment/radio_system_quot%3Brcd_300/overview_of_connectors_on_radio_unit_quot%3Brcd_300/
- **Volkswagen service information, RCD 300 changer connector, mirrored by Workshop Manuals.** Changer DATA IN/OUT, CLOCK, control, supply and analogue audio pin roles. https://workshop-manuals.com/volkswagen/golf-mk5/vehicle_electrics/communication/infotainment/radio_system_quot%3Brcd_300/overview_of_connectors_on_radio_unit_quot%3Brcd_300/multi-pin_connector_4_12-pin_cd_changer_control_and_cd_audio_input_signals/
- **Volkswagen service information, RCD 300 general description, mirrored by Workshop Manuals.** Optional external changer connection and CD-R/CD-RW support. https://workshop-manuals.com/volkswagen/golf-mk5/vehicle_electrics/communication/infotainment/radio_system_quot%3Brcd_300/general_description/
- **Volkswagen service information, RCD 310 changer connector and system overview, mirrored by Workshop Manuals.** Dedicated changer signals and CD-changer-versus-multimedia-control-unit installation choice. https://workshop-manuals.com/volkswagen/golf-mk5/vehicle_electrics/communication/infotainment/radio_system_rcd_310/overview_of_connectors_on_radio_quot%3Brcd_310/multi-pin_connector_4_12-pin_aux_audio_input_cd_changer_control_and_cd_audio_input_signals/
- **Volkswagen service information, RCD 510 connector overview, mirrored by Workshop Manuals.** CAN-connected radio with separate changer control/audio connector. https://workshop-manuals.com/volkswagen/golf-mk5/vehicle_electrics/communication/infotainment/radio_system_rcd_510/overview_of_connectors_on_radio_quot%3Brcd_510/
- **Dension, Compatibility.** Gateway devices emulate CDC or MDI functions and compatibility is primarily head-unit-specific. https://techsupport.dension.com/268165--Compatibility
- **Dension, Gateway Lite / Lite BT hardware and car-side cables.** Distinct Audi/VW mini-ISO and Quadlock harnesses plus older Skoda-specific versus later VW-pinout distinction. https://techsupport.dension.com/638013-W-Gateway-hardware-versions-car-side-cables
- **Dension, Gateway Pro BT hardware and car-side cables.** Distinct Audi Quadlock/mini-ISO, VW BAP Quadlock, and VW single-CAN Quadlock integration families. https://techsupport.dension.com/899846-Y-Gateway-hardware-versions-car-side-cables
- **Dension, Gateway Pro BT installation manual.** On CAN-BAP RCD310/RCD510/RNS510 systems the product emulates factory MDI/telephone functions and documents coding requirements on later cars. https://www.dension.com/files/products/gateway_pro_bt/gateway_pro_bt_v21_manual-75x105-v1.pdf
- **Dension, Gateway Pro BT Audi Dual CAN user manual.** CD-changer-mode integration with controls from radio/steering wheel and menu/ID3 presented on the cluster rather than radio screen. https://www.dension.com/files/news/gwp-9208-2_gateway_pro_bt_user_manual.pdf
- **Dension, Skoda changer-pinout support note.** Some Stream/Dance units exist in Skoda-specific and Volkswagen-pinout variants, reinforcing that marque/model name and connector shell are insufficient protocol boundaries. https://techsupport.dension.com/835305-V-Bad-sound-quality-in-case-of-Skoda
- **Audi service information, A4 Mk3 MMI layout, mirrored by Workshop Manuals.** MOST bus and CD changer as optical infotainment components. https://workshop-manuals.com/audi/a4_mk3/vehicle_electrics/communication/infotainment/mmi_infotainment_system/mmi_maximum_equipment_%28from_week_45/08_onwards%29_layout/
