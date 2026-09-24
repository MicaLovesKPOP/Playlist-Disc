# Ford Europe ACP / Quadlock pre-hardware family research

This note maps the high-value Ford Europe changer-era families that matter for Playlist Disc before hardware exists. It deliberately separates the older Ford Audio Communication Protocol (ACP) changer ecosystem from later Quadlock/CAN-era radios.

The goal is family coverage, not a claim that one adapter will work in every Ford carrying a 5000/6000 badge.

## Evidence classes

The strongest protocol evidence available pre-hardware is independent reverse engineering of Ford ACP and working changer-emulator projects. Yatour and Connects2 compatibility material is used to establish practical radio/connector family boundaries. Exact Ford electrical specifications, commands, timings, and target-vehicle behavior remain capture-gated.

## The older Ford changer family uses ACP

Anson Liu's documented Ford ACP AUX/changer-emulator project describes a 12-position changer connection used by a broad 1990s/2000s Ford radio family. The project replaces a factory changer, receives head-unit playback controls, and routes analogue audio into the factory radio.

Its compatibility list includes 4050RDS, 4500, 4600RDS, 5000RDS, 5000RDS EON, 6000CD RDS, 6000 MP3, and 7000RDS families.

Independent Ford 6000CD changer-emulator work likewise describes the Ford Audio Communication Protocol as the bus between head unit and changer. Community implementations report an RS-485-like physical layer and 9-bit serial framing, but those electrical/timing values remain reverse-engineered evidence rather than a PDv1 specification.

For Playlist Disc the useful conclusion is architectural: **older Ford changer-capable radios expose a reusable dedicated changer-control bus plus separate audio, with OEM transport controls available through the head unit/steering controls.**

## Commercial compatibility data corroborates the 12-pin family

The Yatour YT-M06 application guide defines a `FRD1` Ford 12-pin family for Ford Europe roughly 1994-2004 and lists the same 4050/4500/4600/5000/6000/7000-era head units.

That agreement between a working open-source emulator and a commercial changer-replacement product is strong family-boundary evidence, even though neither makes every listed vehicle a measured PDv1 target.

## Later 5000C/6000CD/6006CD units cross into a different generation

Yatour separately defines `FRD2` for newer Ford Europe radios, using a 40-way flat/Quadlock-related harness for 5000C, 6000CD, and 6006CDC units from the mid/late-2000s. It explicitly separates this generation from the older 12-pin family and excludes OEM Sony head units from that application.

Connects2 aftermarket-control products independently describe 5000C/6000CD/6006CD applications using a CAN-bus Quadlock adapter.

The safe conclusion is therefore a hard compatibility boundary:

- an older radio called "6000CD" may belong to the direct ACP changer family;
- a later 6000CD/6006CD may live in a Quadlock/CAN vehicle integration generation;
- OEM Sony systems are another branch again.

Radio faceplate/model name alone is not enough.

## PD Bridge implications

The older ACP lane is attractive because a future adapter may combine:

1. changer-presence/source emulation;
2. OEM next/previous/seek controls;
3. analogue audio injection;
4. optional display/status semantics exposed by the head unit.

The later Quadlock/CAN lane should be treated differently:

- steering/vehicle controls may be CAN-mediated;
- changer or AUX activation may be head-unit-generation specific;
- exact source behavior must not be inherited from ACP merely because the radio is branded 6000CD.

The host-side PD Bridge protocol does not need to know which Ford generation produced the normalized events.

## Smallest useful later hardware set

A compact Ford validation set should prefer boundaries rather than model count:

1. one older 12-pin ACP radio such as a changer-capable 5000/6000-series unit;
2. one later Quadlock/CAN 5000C/6000CD/6006CD unit;
3. one OEM Sony system only if Ford/Sony compatibility becomes important after those two families are understood.

## Questions deliberately left for hardware

- exact ACP voltage levels, framing, timing, addresses, keepalive and source-selection sequence on target units;
- whether all listed ACP-era radios implement exactly the same changer dialect;
- exact steering-wheel-control path on each vehicle;
- whether the in-dash CD player's TOC/timing/CD-TEXT appears anywhere outside the radio;
- exact CAN messages and bitrate on later Quadlock vehicles;
- whether a later Quadlock 6000CD exposes an external changer source, AUX source, or another integration mechanism;
- coexistence with navigation, factory phone, Sony, amplifier or existing changer equipment;
- whether the Draft 0.2 audio beacon survives each real optical/audio path.

## Sources

All links checked on 2026-09-24.

- **Anson Liu, Ford ACP CD-changer AUX project.** Working open-source changer emulation, 12-position changer connector, head-unit playback controls, compatibility list, and Ford ACP reverse-engineering references. https://ansonliu.com/2017/09/ford-acp-cd-changer-emulator-aux-audio/
- **Dovydas / electronic.lt, Ford 6000CD RDS EON Bluetooth changer emulator.** Independent working Ford ACP changer emulator and community-derived physical/framing details; retained as reverse-engineering evidence only. https://www.electronic.lt/2014/03/08/priedelis-originaliam-automobilio-ford-grotuvui-ford-6000cd-rds-eon-su-bluetooth-funkcijomis/
- **Yatour YT-M06 application guide, mirror by Manualzz.** Separates Ford `FRD1` 12-pin 1994-2004-era radios from `FRD2` newer 40-way/Quadlock 5000C/6000CD/6006CDC applications and excludes OEM Sony from the latter. https://manualzz.com/doc/23313500/yatour-yt-m06-digital-music-changer-user-manual
- **Connects2 CTSFO003.2 / related application data, retailer mirror.** Commercial evidence for CAN-bus Quadlock integration around later 5000C/6000CD/6006CD families. https://www.arukereso.hu/auto-hifi-kiegeszito-c3619/connects2/ford-kormanytavvezerlo-adapter-can-bus-quadlock-ctsfo003-2-ctsfo003-2-p294411221/
