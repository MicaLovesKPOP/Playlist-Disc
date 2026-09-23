# Alfa 147 / ALFA-937 pre-hardware integration research

This note records documentation that can shape a future PD Bridge adapter for the Alfa Romeo 147 Type 937 without pretending that any vehicle-bus or changer behavior has already been measured. The repository reference profile is the Blaupunkt `ALFA-937 CD` with software `3.17`.

The distinction matters: documentation can identify plausible interfaces and documented signal roles, but only later vehicle captures and physical tests can establish the exact messages, timing, firmware behavior, or PDv1 recognition path of the target unit.

## Evidence established by documentation

### The radio participates in the body CAN network

Alfa Romeo eLearn's 147 radio description identifies the radio as a node on the vehicle CAN network. It says the radio exchanges information with the Body Computer and receives ignition state and vehicle-speed information through that network. The wider eLearn CAN description places the radio on B-CAN rather than the drivetrain C-CAN.

For PDv1 this makes B-CAN observation a legitimate research path, but it does **not** establish that CD TOC, track number, CD-TEXT, or button events are exposed there. Those remain capture questions.

### Documented radio connector roles include CAN and optional steering controls

The eLearn functional description assigns connector A pins 1 and 3 to the radio CAN connection, pin 7 to direct battery supply, and connector C pins 10 and 11 to steering-wheel controls when that option is fitted.

These facts are useful for identifying which documented interfaces belong to which subsystem. They are not a wiring instruction: connector population and exact head-unit variant still need physical confirmation before any adapter is attached.

### The platform supports an external CD changer

The same eLearn radio description says the 147 radio is prepared to control an optional ten-disc CD changer. That is significant for bridge architecture because it provides a documented OEM path separate from the in-dash optical drive.

### Commercial adapters corroborate the changer path

Connects2 lists the Alfa Romeo 147 Type 937 (2000-2007) for its CTAARBT001 A2DP interface with a Mini-ISO connection. The manufacturer describes the product as plugging into the original CD-changer port, and states that the OEM radio fast-forward button can be used to answer/end calls. That does not reveal the changer protocol, but it demonstrates that a commercial integration can use the port for both audio and at least one control action.

A mirrored Yatour YT-M06 application guide independently lists Alfa Romeo 147 installations with Blaupunkt 376/378/379/937/947 radios. Yatour describes the product family as a CD-changer replacement controlled from the vehicle head unit. Two independent commercial products therefore support changer emulation as a credible adapter direction, without proving compatibility with every ALFA-937 firmware revision.

### Software 3.17 is a reason not to depend on the passive-AUX trick

A long-running community Alfa 147 AUX guide reports that the front-panel CHANGER/AUX forcing method is applicable to software versions **earlier than 3.17** and advises using an interface where the passive AUX method cannot be enabled. This is community evidence rather than manufacturer documentation, so it is deliberately stored as such in the compatibility profile.

For the `3.17` reference profile, PDv1 integration design should therefore not rely on the SRC/ON passive-AUX trick. A real changer-emulating interface is the more defensible research direction until hardware testing says otherwise.

## Architectural implications for PD Bridge

The evidence supports keeping three responsibilities separate:

1. **Disc recognition** remains the PDv1 optical path: TOC first, with CD-TEXT/audio beacon as redundant channels where available.
2. **Vehicle-state observation** may eventually use B-CAN if captures show useful, stable signals. The current documentation only proves that the radio is a B-CAN participant; it does not define a PDv1 transport.
3. **Playback/control integration** may use the documented CD-changer path. A changer emulator could potentially carry audio and translate OEM controls while the physical Playlist Disc remains the user's tangible selector.

This separation fits the transport-neutral bridge protocol already in the repository: the vehicle adapter can normalize whatever the Alfa exposes without baking Alfa-specific electrical details into the logical protocol.

## Questions deliberately left for hardware

No software/documentation pass can responsibly answer these yet:

- whether the exact ALFA-937 CD SW3.17 unit exposes and enables the Mini-ISO changer interface in the target car;
- the changer protocol's electrical levels, framing, commands, timing, and source-selection handshake;
- which head-unit button events, if any, can be observed on B-CAN versus only inside the radio/changer interface;
- whether the in-dash CD player's track number, TOC timing, CD-TEXT, or load state appears on B-CAN;
- whether the instrument-cluster display receives useful disc/track metadata from the radio;
- whether a changer emulator and an inserted physical audio CD can coexist in the source-selection behavior needed by PDv1;
- whether the Draft 0.2 audio beacon survives the real analogue path.

Until those are measured, the repository should not invent CAN identifiers, changer frames, bus speeds, or control mappings.

## Sources

All links were checked on 2026-09-23.

- **Alfa Romeo eLearn, E3510 RADIO - Description (5 door), mirrored by 4CarData.** Radio architecture, CAN-node behavior, ignition/speed information, optional ten-disc changer. https://4cardata.info/elearn/190/2/2002030/2000206/2001822/3023379
- **Alfa Romeo eLearn, E3510 RADIO - Functional description (5 door), mirrored by 4CarData.** Connector A CAN/supply roles and connector C steering-control roles. https://4cardata.info/elearn/190/2/2002032/2000206/2001823/3026183
- **Alfa Romeo eLearn, E1050 CAN CONNECTION LINES - Description, mirrored by 4CarData.** Network topology placing the radio on B-CAN. https://4cardata.info/elearn/190/2/2002018/2000209/2001823/3023171
- **Connects2, CTAARBT001 Alfa Romeo A2DP Interface.** Type 937 application, Mini-ISO/CD-changer-port integration and OEM fast-forward-button call control. https://www.connects2.com/Product/ProductItem/CTAARBT001
- **Yatour, YT-M06 application guide, mirrored by Manuals+.** Alfa 147 / Blaupunkt 376, 378, 379, 937, 947 application and CD-changer-replacement model. https://manuals.plus/m/9921c86f4ad53408abf45b538a8fd98b7e499750560fd2c89f7f8f36daab09d8
- **WileCoyote.it, Requisiti Alfa 147.** Community report on the pre-3.17 passive CHANGER/AUX activation boundary; retained as lower-authority evidence only. https://www.wilecoyote.it/web/requisiti.htm
