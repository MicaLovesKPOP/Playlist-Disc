# MINI R55 / Boost CD (RAD2) pre-hardware integration research

This note records source-backed facts that can shape a future PD Bridge adapter for the pre-LCI MINI Clubman R55 with **Radio MINI Boost CD / RAD2**. It deliberately separates documented architecture from anything that still requires a real vehicle, optical media, or bus capture.

The target car already has steering-wheel media controls and an existing diagnostic setup through the OBD port. Those facts make the platform unusually attractive for an OEM+ implementation, but they do not turn OBD diagnostics into arbitrary MOST/K-CAN monitoring.

## Evidence established by documentation

### Option 6FC identifies the Boost CD / RAD2 family

MINI Technical Service bulletin SI M09 01 09 explicitly lists R55, R56, and R57 models with option **6FC (Radio MINI boost CD, RAD2)**. That is enough to use RAD2 documentation as the architectural family for an R55 fitted with Boost CD, while still leaving exact part number/software identification for later diagnostics.

### Boost CD is a MOST radio and a MOST ↔ K-CAN gateway

MINI service-technique documentation describes the BMW Professional / MINI Boost CD radio as a **MOST-network radio**. Its gateway translates between MOST and K-CAN and acts as system, power, and network master for MOST.

A separate MOST service description likewise says the RAD2 head-unit gateway is connected to both MOST and K-CAN and that the head unit forms the interface between the two buses.

For PDv1 this is the most important architectural fact: **Choco does not have one simple radio bus**. A future adapter can plausibly have different responsibilities on different networks:

- K-CAN may expose useful vehicle/control state;
- MOST is the documented infotainment ring and likely digital-audio/control path for optional multimedia modules;
- RAD2 bridges the two.

Nothing in those documents proves that the in-dash CD player's TOC, CD-TEXT, track timing, or button events appear on K-CAN. Those remain capture questions.

### The Boost CD drive understands audio CD and MP3/WMA

The service-technique document states that the Boost CD drive plays ordinary audio CDs as well as compressed MP3/WMA media.

That is encouraging for optical-disc experimentation, but PDv1 should **not** change its compatibility baseline because of it. Ordinary CD-DA remains the conservative universal format across Shadow, Choco, Misty, and future cars. MP3 capability only tells us that RAD2 has a richer optical parser internally; it does not establish what information leaves the head unit.

### The optional R55 CD changer is on the optical infotainment side

MINI's R55 CD-changer removal instructions explicitly tell the technician to follow optical-fibre handling procedures before disconnecting the changer.

That matters because it kills a tempting oversimplification: the MINI changer path is not analogous to the Alfa's analogue Mini-ISO changer connector. A future Choco playback integration that behaves like a factory changer has to respect the **MOST architecture** or use an existing MOST interface rather than pretending the changer is a few analogue pins.

### Steering-wheel track controls are documented on the 2008 Clubman

The official 2008 MINI / MINI Clubman owner's manual documents steering-wheel controls for changing radio station and selecting music track. The same manual identifies the car's radio display and center-stack audio controls.

That makes steering input and the OEM display valid PD Bridge targets. Documentation does not tell us the internal messages used for those controls or how much arbitrary metadata RAD2 can render.

### OBD diagnostics and direct MOST access are not the same thing

BMW/MINI ISTA/P documentation for R55/R56 distinguishes normal vehicle-interface access over the OBD socket from MOST multichannel programming via ICOM B / a MOST direct-access port. It also notes that RAD2-equipped cars do not always have that direct-access port.

So Choco's existing OBD diagnostic setup is useful for:

- identifying the exact RAD2 module/software;
- reading fault memory and module topology;
- inspecting coding/vehicle-order state using the appropriate tools;
- establishing whether changer-related options/modules are configured.

But it should **not** be described as an unrestricted MOST sniffer. Direct observation of infotainment traffic may require another interface or another tap point.

## Architectural implications for PD Bridge

The current evidence supports a split design:

1. **Physical Playlist Disc recognition** still begins with the in-dash optical drive. We should test whether full/rounded TOC information, track state, or CD metadata becomes visible outside RAD2 before inventing a separate sensor.
2. **Vehicle controls/state** may be normalized from K-CAN or another documented interface if captures show stable useful messages.
3. **Streaming audio / rich OEM integration** belongs on the MOST side or in a proven MOST-compatible aftermarket interface rather than a homemade analogue changer hack.
4. **Diagnostics/coding** remain a setup/research tool, not the runtime bridge transport by default.

This division fits PD Bridge Draft 0.1: a Choco-specific adapter can hide MOST/K-CAN complexity and publish only normalized events such as `DISC_SELECTED`, `NEXT`, `PREVIOUS`, `SOURCE_STATE`, and display capability.

## Questions deliberately left for hardware

These should not be answered from documentation alone:

- exact RAD2 hardware/software identifiers in the target car;
- whether the physical test disc's TOC or CD-TEXT is observable over K-CAN, MOST, diagnostics, or nowhere outside the drive;
- whether steering-wheel media actions can be observed conveniently on K-CAN and their exact message encoding;
- whether RAD2 can be commanded to switch source by an external adapter without undesirable side effects;
- whether a factory-changer configuration is already present or needs coding;
- exact MOST ring membership in the target car;
- presence/location of any MOST direct-access port;
- whether an existing MOST Bluetooth interface can expose reliable bidirectional metadata on this exact pre-LCI Boost CD revision;
- whether factory display text can be injected generically or only through specific source/module semantics;
- whether the Draft 0.2 audio beacon survives the real optical/audio path.

Until those are measured, the repository should not invent K-CAN IDs, MOST function blocks, coding values, or RAD2 command frames.

## Sources

All links were checked on 2026-09-24.

- **MINI Technical Service, SI M09 01 09, mirrored by Operation CHARM.** R55/R56/R57 option 6FC identification as Radio MINI Boost CD / RAD2 and RAD2 MOST-gateway programming behavior. https://charm.li/Mini/2009/Cooper%20JCW%20%28R56%29%20L4-1.6L%20Turbo%20%28N14%29/Repair%20and%20Diagnosis/Technical%20Service%20Bulletins/Customer%20Interest/Audio%20System%20-%20RAD2%28R%29%20Locks%20Up%20When%20Programming/
- **MINI service information, Communication Systems - Service Techniques, mirrored by DiagnostData.** Boost CD as a MOST radio; MOST/K-CAN gateway functions; audio master/connection master; standard audio CD plus MP3/WMA support. https://diagnostdata.com/mini/cooper/ii-2006-2010/remont/communication-devices/communication-systems-service-techniques-cooper-cooper-s-r56/other/
- **MINI repair information, 65 11 072 Removing/installing CD changer - R55, mirrored by DiagnostData.** Optical-fibre handling requirement for the R55 changer. https://diagnostdata.com/mini/cooper/ii-2006-2010/remont/airbag-audio-navigation-and-anti-theft-repair-s-clubman-r55/65-11-072-removing-and-installingreplacing-cd-changer/65-11-072-removing-and-installingreplacing-cd-changer/
- **BMW AG / MINI USA, 2008 MINI / MINI Clubman Owner's Manual.** Steering-wheel station/track controls, radio display, center-stack audio/CD controls. https://www.miniusa.com/content/dam/mini/PDF/archiveownermanuals/MY08/01410014701_basis_r5556_1207_ue_1107__2008.pdf
- **MINI service information, MOST Functions, mirrored by Workshop Service Manuals.** RAD2 gateway connection to MOST and K-CAN; head unit as interface between both buses. https://workshop-manuals.com/mini/cooper_s_%28r56%29/l4-1.6l_turbo_%28n14%29/powertrain_management/computers_and_control_systems/information_bus/component_information/description_and_operation/most_functions_%28without_rad_radio%29/
- **BMW AG, ISTA/P User Documentation, mirrored by ManualShelf.** R55/R56 diagnostic/programming interface matrix and RAD2/MOST direct-access-port conditions. https://www.manualshelf.com/manual/bmw/ag-icom/user-guide-english.html
