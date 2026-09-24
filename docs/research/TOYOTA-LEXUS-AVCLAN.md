# Toyota / Lexus AVC-LAN pre-hardware family research

This note maps the high-value Toyota/Lexus changer-era family centered on AVC-LAN, Toyota's multimedia use of NEC/Renesas IEBus.

The family is unusually useful pre-hardware because independent tooling exists to decode real head-unit/CD-changer traffic and an open-source project has implemented a functional changer-emulation board.

## Evidence classes

Sigrok decoder work is used as protocol-analysis evidence because it includes actual head-unit and CD-changer captures. The AVCLAN Mockingboard project is used as working reverse-engineering evidence. Yatour/Dension material is used to establish broad commercial application and harness families.

No captured address, command, timing or electrical value becomes normative PDv1 behavior without target hardware.

## AVC-LAN is the Toyota multimedia bus used by changer-era systems

Sigrok development material explicitly identifies IEBus/AVC-LAN as the multimedia/navigation bus used by Toyota and describes decoder development against a testbench containing an audio head unit and CD changer.

The associated decoder/dump work demonstrates that changer traffic is observable and software-decodable before Playlist Disc needs to invent its own analyzer.

For PD Bridge, AVC-LAN is therefore a distinct proprietary multimedia-bus lane rather than generic vehicle CAN.

## A working open-source changer emulator proves the integration path is practical

The AVCLAN Mockingboard project connects to a stock Toyota head unit and emulates an external CD changer on AVC-LAN.

Its documented implementation can:

- communicate on AVC-LAN;
- enable the changer audio input;
- react to head-unit transport controls;
- switch between internal and external CD sources on supported setups.

The project also contains a Wireshark dissector and points to Sigrok changer captures.

Its own documentation is appropriately cautious about incomplete handshake behavior on some revisions. That is exactly the level PDv1 should preserve: reusable family evidence, not universal Toyota compatibility.

## Commercial adapter families show broad Toyota/Lexus reuse

Dension lists a dedicated Toyota/Lexus Gateway Lite cable family (CABL-TO1).

Yatour's YT-M06 guide defines a Toyota application family using Toyota-specific changer connectors across many OEM Panasonic/Matsushita head units and navigation systems. It also documents optional Y-cables where the changer port is occupied by navigation/AUX/XM and reports text display support on some compatible systems.

This establishes wide practical reuse, but the exact radio part number still belongs in every concrete compatibility profile.

## Family map

| Family | Established pre-hardware architecture | PD Bridge implication | Still hardware/source gated |
| --- | --- | --- | --- |
| Toyota/Lexus AVC-LAN external-changer systems | proprietary IEBus-derived multimedia network plus changer audio path | strong reusable changer-emulation/control lane | exact target addresses, handshake, electrical layer, text semantics |
| systems with navigation/XM/AUX sharing changer resources | same logical ecosystem with port/device coexistence constraints | adapter must model source ownership/coexistence | exact arbitration and device-presence behavior |
| later CAN-centric / integrated infotainment | not proven to be the same AVC-LAN changer family | separate generation if needed | architecture-specific research |

## Smallest useful later hardware set

A compact Toyota/Lexus validation set can stay small:

1. one common Toyota AVC-LAN head unit known to support an external changer;
2. one Lexus/navigation-equipped example where the multimedia bus has more than one peripheral;
3. only add a later non-AVC-LAN unit if physical testing shows the architecture boundary matters to PDv1.

## Questions deliberately left for hardware

- exact transceiver/electrical requirements for target Toyota/Lexus units;
- exact changer registration/handshake and keepalive sequence;
- whether the head unit exposes physical-disc TOC, CD-TEXT or only changer-style state;
- exact text-display limits and character encoding;
- coexistence with navigation, satellite radio, AUX and factory changer modules;
- whether steering controls are visible on AVC-LAN or elsewhere in each vehicle;
- whether a PD Bridge adapter can share the bus passively before asserting changer presence;
- whether the Draft 0.2 audio beacon survives the real radio path.

## Sources

All links checked on 2026-09-24.

- **sigrok-devel, IEBus/AVC-LAN decoder announcement.** Decoder tested with an audio head unit and CD changer; identifies AVC-LAN as Toyota multimedia/navigation IEBus. https://sourceforge.net/p/sigrok/mailman/message/37863005/
- **halleysfifthinc, AVCLAN Mockingboard.** Open-source Toyota CD-changer emulator, AVC-LAN implementation, head-unit controls, audio-input activation and protocol-analysis tooling. https://github.com/halleysfifthinc/Toyota-AVC-LAN
- **Dension Gateway Lite hardware/cable documentation.** Dedicated CABL-TO1 Toyota/Lexus cable family with an explicit warning that harness families are not universal vehicle compatibility. https://techsupport.dension.com/638013-W-Gateway-hardware-versions-car-side-cables
- **Yatour YT-M06 application guide, mirror by Manualzz.** Broad Toyota/Lexus changer-replacement family, Toyota-specific connectors, navigation coexistence/Y-cable notes and selected text-display support. https://manualzz.com/doc/23313500/yatour-yt-m06-digital-music-changer-user-manual
