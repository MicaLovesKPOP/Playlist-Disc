# Renault Tuner List / Update List / later CAN pre-hardware family research

This note maps Renault's common changer-era VDO Tuner List and Update List radios, plus the later Radio+/Continental CAN generation, as distinct compatibility families for future PD Bridge adapters.

The goal is not to claim that one Renault harness or protocol covers every vehicle. Commercial integration data is strongest at establishing head-unit/generation boundaries, while community reverse engineering provides useful implementation hypotheses that remain below manufacturer/service-documentation authority.

No changer bytes, CAN identifiers, bus rates, or electrical levels are normative here. Those remain target-hardware questions.

## Evidence classes

Connects2 and InCarTec application data are used as commercial integration evidence because they explicitly distinguish Tuner List, Update List, display topology, connector style, and later CAN/Quadlock systems across many Renault models.

Dension's harness list provides independent evidence that Renault formed a reusable commercial integration family (`CABL-RE8`), while also warning that a shared cable family never means every radio in a marque is compatible.

Open-source changer/display projects and community pinout references are used only as reverse-engineering evidence. They are useful for defining bench hypotheses, not for promoting protocol constants into PDv1 before captures.

## Tuner List is a broad pre-2005-era family, not merely a model label

Connects2 `CTSRN012.2` groups VDO Tuner List radios with a dash display across Clio II, Kangoo, Megane I/II, Scenic, Modus, Trafic, and Laguna II, mainly around the 2000-2005 period. The product is explicitly an updated interface with a separate display connector.

InCarTec independently describes a Renault pre-2005 Tuner List interface for cars with a separate display. Another InCarTec interface covers Tuner/Update List vehicles where the display is instead built into the radio.

That distinction matters for PD Bridge: even inside one radio family, display topology changes the steering/display integration path and must be part of the future compatibility profile.

## Update List is a later reusable generation with overlapping vehicles

Connects2 `CTSRN005.2` groups VDO Update List units across Clio III, Megane II, Scenic, Laguna, Modus, Twingo II, Trafic II, Kangoo II, Master III, and Nissan Primastar, generally from the mid-2000s onward. Its application table describes an 8-way ISO connection.

Connects2's Twingo application history makes the generation boundary particularly clear: VDO Tuner List appears on earlier cars, VDO Update List on 2007-2009 cars, and later Update List / Radio+ integrations move into a different interface generation after 2009.

The safe compatibility key is therefore not simply "Renault mini-ISO." Tuner List and Update List must be identified explicitly, along with display arrangement and exact vehicle/head-unit generation.

## Update List steering/display integration is CAN-mediated on documented applications

InCarTec's Update List CAN-bus steering interface states that the steering-control CAN signal runs through the separate display or original navigation unit; removing that display/navigation unit prevents the interface from working.

This establishes a real architectural constraint for the affected Update List applications: radio, steering controls, and display cannot be treated as unrelated modules when designing an adapter.

Open-source reverse engineering corroborates that architecture without becoming target truth. `MeganeBT` emulates an Update List CD changer, uses standard radio and steering controls, and connects to the CAN link between radio and AFFA display so it can render title/artist metadata. A separate Update List display project reports a CAN-connected display on a tested Clio II phase 3.

For PD Bridge, CAN observation/display injection is therefore a defensible Update List research lane, but exact CAN IDs, bitrate, timing, and message ownership still require target captures.

## The changer path remains distinct from the display/control network

Community pinout references for VDO Tuner List / Update List identify a dedicated C3 changer block with head-unit-to-changer transmit, changer-to-head-unit receive, power/enable, and digital audio input; they also distinguish a central-communication/display block from the changer block.

Open-source changer emulators independently implement the same architectural idea: `MeganeBT` emulates the standard Renault CDC and sends audio over S/PDIF, while `ESP32TLCDCEmu` targets Tuner List / Update List changer emulation with S/PDIF output.

This is useful pre-hardware evidence for separating three future adapter responsibilities:

1. dedicated CDC presence/control signalling;
2. audio delivery over the radio's expected changer audio path;
3. optional display/steering integration over the vehicle/display network.

The repository should not yet assume that Tuner List and Update List use identical CDC bytes just because both can be emulated by related projects.

## AUX support is not a substitute for changer integration

Community pinout references distinguish Update List by an AUX-capable connector that is absent on Tuner List. Commercial Bluetooth AUX products likewise advertise Update List compatibility while explicitly excluding Tuner List.

That makes passive AUX a useful convenience path for some later radios, but it does not replace the changer-emulation lane when Playlist Disc needs source activation, OEM controls, or disc-like behavior.

## The later Radio+ / Continental Quadlock generation is a hard boundary

Connects2 `CTSRN006.2` covers later Renault applications such as Fluence and Scenic III with Radio+ / Continental head units and Quadlock/Fakra, and marks the interface as CAN-bus based with ignition, illumination, speed, park-brake, and reverse outputs.

The same product family also covers some later VDO Update List applications on Quadlock, demonstrating that the radio name alone is insufficient: connector/network generation must be recorded too.

This later family should not inherit Tuner List/Update List CDC assumptions without separate evidence. It is a CAN/Quadlock integration lane first, with any external changer behavior to be proven per head unit.

## Navigation and premium units remain separate families

Cabasse, Carminat, TomTom, and other navigation/premium units appear alongside basic Tuner List/Update List radios in Renault applications but should not be collapsed into the same protocol family.

Commercial AUX products explicitly exclude several Carminat/Cabasse variants even while supporting ordinary Update List radios. That is enough reason to keep navigation/premium systems outside this P1 family note until they receive their own evidence.

## Family map

| Family | Established pre-hardware architecture | PD Bridge implication | Still hardware/source gated |
| --- | --- | --- | --- |
| VDO Tuner List, separate display | widespread early-2000s Renault family; separate display integration; dedicated CDC path indicated by reverse engineering | direct CDC bench lane plus separate display/control lane | exact CDC framing/electrical levels; display protocol per unit; source handshake |
| VDO Tuner List, integrated display | same radio generation but different display/control topology | profile display topology explicitly; do not assume separate-display wiring | exact stalk/control path and CDC equivalence |
| VDO Update List, separate display | later family; commercial CAN steering/display integration; dedicated CDC/S/PDIF path in reverse-engineered implementations | CDC emulator plus optional CAN display/control adapter | target CAN messages/bitrate; exact CDC dialect; coding/enable behavior |
| VDO Update List, integrated display | Update List functionality without external display dependency | simpler vehicle-display boundary but still head-unit-specific | exact steering/control path and CDC dialect |
| Radio+ / Continental / later Quadlock | later CAN/Quadlock architecture | separate CAN-generation integration work | changer availability, exact CAN semantics, source/audio path |
| Cabasse / Carminat / TomTom navigation families | explicitly excluded by some basic-radio interfaces and AUX products | separate future lane only when justified | architecture-specific control/display/audio behavior |

## Smallest useful later hardware set

A representative Renault bench set can stay small:

1. one VDO Tuner List unit with separate display and stalk control;
2. one VDO Update List unit with its matching separate display;
3. optionally one integrated-display Tuner/Update List unit to test whether CDC behavior survives the display-topology change;
4. one later Radio+ / Continental Quadlock unit only after the direct CDC families are understood.

That set can answer whether the apparent cross-model reuse is truly protocol reuse before buying radios from many vehicles.

## Questions deliberately left for hardware

- exact Tuner List versus Update List CDC framing, baud, inversion, voltage levels, initialization, keepalive, and source-selection sequence;
- whether one changer emulator dialect works across both generations or requires per-head-unit variants;
- exact digital-audio electrical requirements, mute behavior, and whether any analogue-changer variants remain relevant;
- whether changer presence must be configured/coded on each target vehicle;
- exact stalk/display messages and whether PD Bridge needs CAN/display participation at all for basic playback;
- whether now-playing text can be injected reliably without disrupting factory display ownership;
- behavior when the separate display is absent, substituted, asleep, or on a different firmware generation;
- coexistence with factory navigation, phone, or changer modules;
- which later Quadlock units retain any CDC-compatible source versus requiring a completely different source architecture.

Until measured, related open-source frame constants and bitrates remain capture hypotheses only.

## Sources

All links were checked on 2026-09-24.

- **Connects2, CTSRN012.2.** VDO Tuner List applications across Clio/Kangoo/Megane/Scenic/Modus/Trafic/Laguna and explicit separate-display connector. https://connects2.com/Product/ProductItem/CTSRN012.2
- **Connects2, CTSRN005.2.** VDO Update List application family across Renault/Nissan models and 8-way ISO generation. https://connects2.com/Product/ProductItem/CTSRN005.2
- **Connects2, Renault Twingo application list.** Shows Tuner List, Update List, and later Radio+/Continental generations as separate interfaces over time. https://connects2.com/products/steering-wheel-control-interfaces/vehicle/Renault/Twingo
- **Connects2, CTSRN006.2.** Later CAN-bus/Quadlock Renault applications including Radio+/Continental and some later Update List units. https://connects2.com/Product/ProductItem/CTSRN006.2
- **InCarTec, Renault Update List ISO CAN-bus steering interface 29-UC-050-REN1.** Documents CAN steering-control dependency on the separate display/navigation unit. https://incartec.co.uk/product/Renault-ISO-CANbus-steering-wheel-audio-control-interface-29-UC-050-REN1
- **InCarTec, Renault Tuner List steering interface 29-652.** Pre-2005 Tuner List applications with separate display. https://incartec.co.uk/product/Renault-Tuner-List-Steering-wheel-control-interface-iso-cables-29-652
- **InCarTec, Renault Tuner/Update List integrated-display interface 29-608.** Establishes the separate integrated-display topology within the Tuner/Update List families. https://incartec.co.uk/product/Renault-Tuner-Update-list-Small-Display-on-radio-Steering-wheel-control-interface-29-608
- **Dension, Gateway hardware versions and car-side cables.** `CABL-RE8` Renault harness family plus explicit warning that harness families do not imply universal marque compatibility. https://techsupport.dension.com/638013-W-Gateway-hardware-versions-car-side-cables
- **PinoutGuide, Renault VDO Tunerlist / Updatelist.** Lower-authority pinout reference for separate CCU/display and CDC blocks, CDC Tx/Rx/power/S/PDIF, AUX distinction, and older analogue-audio caveat. https://pinouts.ru/Car-Stereo-Renault-Dacia/Renault_VDO_Tunerlist_VDO.shtml
- **Tomasz Mankowski, MeganeBT.** Reverse-engineered Update List CDC/S/PDIF emulator with radio/steering control and CAN-connected AFFA display metadata. https://github.com/Tomasz-Mankowski/MeganeBT
- **manu-t, autoradio-interface UpdateListDisplay.** Related-platform reverse engineering of an Update List CAN display on a Clio II phase 3; exact bitrate/IDs are not promoted into PDv1. https://github.com/manu-t/autoradio-interface/blob/master/UpdateListDisplay/UpdateListDisplay.ino
- **JohnyMielony, ESP32TLCDCEmu.** Open-source Tuner List / Update List changer-emulation implementation with S/PDIF output; used only as reverse-engineering evidence. https://github.com/JohnyMielony/ESP32TLCDCEmu
