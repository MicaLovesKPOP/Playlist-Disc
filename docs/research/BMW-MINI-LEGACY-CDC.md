# BMW / MINI legacy CD-changer pre-hardware family research

This note maps the pre-MOST BMW/MINI changer architecture that is relevant to PD Bridge, while keeping it separate from the project's existing MINI R55 RAD2/MOST anchor and from later BMW MOST/iDrive systems.

The reusable boundary is not simply a 17-pin versus 40-pin radio connector. The stronger architectural pattern is **vehicle-bus changer control plus a separate audio path**, with different radio locations and connector generations across BMW and first-generation MINI.

## Evidence classes

BMW Service Training and BMW technical bulletins provide the main BMW architecture evidence. The original MINI R50/R53 CD-changer retrofit instructions provide direct MINI wiring and coding evidence. Dension documentation is used only to confirm commercially relevant connector/system boundaries and the transition to MOST.

No I-Bus/K-Bus message identifiers, bus timing, changer command bytes, analogue levels, or source-selection handshake are claimed here.

## BMW New Generation radios use the body/instrument bus for audio-system control

BMW's New Generation Radio service-training material covers C52/C53/CD53/MD53/CD54/BM53/BM54 installations across E39, E46, E52, and E53.

The training material states that system components are connected through the body/instrument bus and that button/volume operations are conveyed over that bus. It also documents that the radio communicates with other modules over K-Bus or I-Bus depending on model, including multifunction steering-wheel audio-control state.

The system diagrams include the CD changer alongside the radio, display/control units, multifunction steering wheel, and other I/K-Bus participants.

For PD Bridge this establishes that OEM controls and changer/source operation live in a networked audio system, but it does not prove which individual changer events or disc metadata are published as bus messages.

## BMW changer control and audio are physically separable

BMW service bulletins for E46 changer installation explicitly describe a three-pin CD-changer power/I-Bus connection. The pins are ground, battery power, and I-Bus.

A separate BMW bulletin for the E46 C53 New Generation radio describes revised changer/telephone audio connector pin assignments and identifies left, right, and common CD-changer audio connections.

Taken together, these documents support a clean architectural split:

- power and I-Bus are carried on the changer's three-pin connection;
- changer audio reaches the radio through a separate audio/data harness;
- the radio remains the source-management point.

That is materially different from VAG's documented dedicated DATA IN/DATA OUT/CLOCK changer bus even though both ultimately feed analogue audio to a radio.

## New Generation radios changed connector details without eliminating the changer architecture

BMW SIB 65 04 01 says the C53 Business New Generation radio entered E46 production in March 2001 and introduced a new Siemens connector for CD changer/telephone with revised pin assignments.

The bulletin required modifying the audio-data cable for the new radio, while the power/I-Bus cable remained part of the changer installation.

This is a useful warning for future hardware selection: connector generation changed, but that does not imply a wholly new changer-control concept.

A compatibility implementation should therefore be keyed to the actual radio/module generation, not merely "E46" or "BMW 17-pin/40-pin."

## Navigation cars move the radio module away from the dashboard

Dension's BMW 16:9 navigation installation documentation states that the changer connection is not on the visible navigation display. It is at the BM24/BM54 radio tuner module in the boot.

The same documentation distinguishes:

- BM24 with the older 17-round-pin connector;
- BM54 with the later 40-flat-pin connector.

This is commercial integration evidence rather than BMW protocol documentation, but it establishes an important installation boundary: a dashboard screen/control panel is not necessarily the radio endpoint that a PD Bridge changer-side adapter would connect to.

It also explains why later physical testing needs to record the exact radio module, not just the visible head unit.

## First-generation MINI R50/R53 uses K-Bus plus separate changer connections

The original MINI R50/R53 CD-changer retrofit instructions identify:

- radio plug X18126;
- a CD-changer wiring harness;
- K-Bus joint connector X10116;
- chassis-earth joint X494;
- separate black 3-pin and 6-pin changer socket housings.

The instructions explicitly route the changer harness to the K-Bus joint connector and distinguish older versus New Generation radio connector variants.

The circuit diagrams identify the changer on K-Bus and show separate left/right audio connections.

This makes R50/R53 a strong legacy MINI family in its own right. It should not inherit the R55 RAD2 architecture merely because both are MINI.

## R50/R53 changer retrofit is not coding relevant

The MINI retrofit instructions state that retrofitting the CD changer is not coding relevant and cannot be diagnosed.

For a future PD Bridge adapter this is encouraging because factory-style changer presence may not require a coding workflow on this documented configuration.

It is still not proof that every R50/R53 radio revision will recognize an emulator automatically, nor does it establish exact K-Bus frames.

## BMW/MINI legacy and MOST are different families

Dension's copper Gateway documentation provides separate BMW harnesses for the older 17-round-pin and later 40-flat-pin connector families.

Its Gateway 500 documentation, by contrast, treats later BMW platforms such as E60/E61, E63/E64, E70, E87, and E90-series cars as MOST optical systems and installs at the optical changer position/ring.

That is the correct architecture boundary for Playlist Disc:

- legacy BMW/MINI changer systems belong in this I/K-Bus + separate-audio lane;
- later BMW MOST systems belong in the optical lane;
- the MINI R55 RAD2 work already in the repository is an optical/K-CAN anchor, not a continuation of R50/R53 K-Bus wiring.

## Family map

| Family | Established architecture | PD Bridge implication | Still hardware/source gated |
| --- | --- | --- | --- |
| BMW pre-NG / early changer era | changer integrated with vehicle audio network; connector generations vary | candidate legacy bus + analogue-audio adapter | exact older-radio boundaries and frames |
| BMW C53/CD53/CD54 NG radio era | I/K-Bus system control; separate changer power/I-Bus and audio path | normalize controls from vehicle bus while changer/audio path remains separate | exact changer commands, disc-state visibility, radio-specific behavior |
| BMW BM53/BM54 navigation era | radio tuner module remote in luggage compartment; changer-side integration occurs there | adapter endpoint may be remote from visible display/head unit | exact module revision, 17/40-pin compatibility, display traffic |
| MINI R50/R53 | K-Bus changer integration, separate 3-pin/6-pin changer connections, no coding required by retrofit instructions | strong legacy MINI adapter candidate | exact K-Bus changer frames, radio revision behavior |
| BMW/MINI MOST generation | optical ring/CD-changer emulation | separate optical adapter architecture | MOST function blocks, coding, target-module behavior |
| MINI R55 RAD2 | MOST radio/gateway plus K-CAN, already researched separately | existing optical reference anchor | target-car captures remain required |

## Representative future hardware set

A small but informative later hardware set would be:

1. one E46-style C53/CD53 New Generation radio with changer preparation;
2. one BM54 navigation/radio-module installation or bench set;
3. one R50/R53 MINI radio + factory changer harness;
4. later BMW MOST hardware only as part of the separate optical research lane.

Testing several cars that share the same radio/module would add less architectural information than one example from each family.

## Questions deliberately left for hardware

Do not infer these from the wiring diagrams or commercial adapter ecosystem:

- exact I-Bus or K-Bus changer messages, addresses, timing, wake-up behavior, or checksums;
- whether full TOC, track count, elapsed time, CD-TEXT, or disc-load state is observable on I/K-Bus;
- whether steering-wheel commands can be consumed safely without interfering with the factory radio state machine;
- analogue signal levels and grounding behavior for a replacement/emulated audio path;
- whether one BMW changer protocol is identical across C53/CD53/CD54/BM53/BM54;
- exact differences between BMW I-Bus and MINI R50/R53 K-Bus changer semantics;
- emulator coexistence with a real factory changer;
- radio/module behavior after ignition cycles and bus sleep/wake;
- display-text injection capability on MID/BMBT/cluster or MINI display;
- whether the Draft 0.2 audio beacon survives the real in-dash optical/audio chain;
- any assumption that a later MOST BMW or R55 MINI can reuse the legacy copper adapter.

## Design consequences for PD Bridge

The legacy BMW/MINI family reinforces the same separation seen from another direction in VAG research: **control-network semantics, changer emulation, audio transport, and display behavior should remain independent adapter capabilities**.

For a future BMW/MINI adapter:

- disc recognition may come from observable changer/radio state or the universal audio beacon;
- OEM media controls can be normalized from I/K-Bus only after captures prove them;
- source activation may be a changer-emulation concern rather than a generic vehicle-bus command;
- audio can use the documented separate changer audio path;
- display metadata should be advertised only when the exact MID/BMBT/cluster/radio path is proven.

The host should continue to see only PD Bridge capabilities, not BMW-specific bus assumptions.

## Sources

All links checked on 2026-09-24.

- **BMW AG Service Training, New Generation (NG) Radio, June 2000, mirrored by ge39.com.** NG radio families, body/instrument-bus control, I/K-Bus communication, CD-changer system placement, source management and connector information. https://www.ge39.com/files/ngradios.pdf
- **BMW Service Information Bulletin 65 04 01, mirrored by BMW Repair Guide.** E46 C53 New Generation radio introduction, revised Siemens changer/telephone connector, separate changer audio assignments, and continued power/I-Bus harness. https://bmwrepairguide.com/sib/650401.pdf
- **BMW Service Information, CD Changer Installation Precautions, mirrored by Operation CHARM.** E46/X5 three-pin changer X18180 wiring: ground, power, and I-Bus. https://charm.li/BMW/2000/328i%20%28E46%29%20L6-2793cc%202.8L%20DOHC%20%28M52%20TU%29/Repair%20and%20Diagnosis/Technical%20Service%20Bulletins/All%20Technical%20Service%20Bulletins/CD%20Changer%20-%20Installation%20Precautions/
- **MINI Parts and Accessories, CD changer retrofit kit for R50/R53, installation instruction 01 29 0 139 548, mirror by Manualzz.** K-Bus joint connector, separate 3-pin/6-pin changer connectors, old/New Generation radio variants, circuit diagrams, and no-coding statement. https://manualzz.com/doc/24695563/mini-cd-changer-car-audio-installation-instructions
- **MINI CD changer retrofit instruction mirror by Mini Mania.** Secondary copy of the R50/R53 factory installation instructions and K-Bus wiring diagram. https://www.minimania.com/images/instructions/OEM%20CD%20Changer.pdf
- **Dension, BMW 16:9 navigation requirements and installation.** BM24/BM54 radio module location in the boot and 17-round-pin versus 40-flat-pin connector generations. https://techsupport.dension.com/663302-U-BMW-169-navigation-requirements-and-installation
- **Dension, Gateway Lite / Lite BT hardware and car-side cables.** Separate BMW 17-round-pin and 40-flat-pin copper harness families. https://techsupport.dension.com/638013-W-Gateway-hardware-versions-car-side-cables
- **Dension Gateway 500 MOST installation guide.** Later BMW/MINI optical changer-emulation family, coding conditions, and representative MOST-era BMW platforms. https://www.dension.com/files/products/gateway_500/gateway-500-install-guide.pdf
