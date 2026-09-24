# Mazda legacy CDC / later CAN pre-hardware family research

This note maps Mazda's practical changer-era split between the legacy external-CDC family and the later CAN-era integration family.

The goal is to establish where reuse is defensible and where exact head-unit revision matters enough that bench testing is the next useful step.

## Evidence classes

Dension and Yatour compatibility documentation establish reusable Mazda cable/application families and concrete head-unit caveats. The later Mazda generation is identified by Yatour as a CAN-bus family. Exact protocol framing, CAN identifiers and source-selection behavior remain hardware-gated.

## Legacy Mazda external-CDC family

Yatour defines a legacy Mazda application family covering many 2000s Mazda 2/3/5/6, MX-5, RX-8, Premacy, MPV and related factory head units.

Its application notes demonstrate why Mazda cannot be represented by model/year alone:

- some Mazda 6 radios require an internal jumper/modification before the external changer input is usable;
- RX-8 compatibility depends on radio firmware revision;
- navigation and Bose variants are excluded in parts of the legacy family;
- specific Panasonic/Matsushita-style head-unit part numbers are listed.

Dension independently lists a dedicated CABL-MA1 Mazda cable family.

For PDv1, this establishes a reusable **legacy direct changer-integration lane**, but with unusually important head-unit revision and equipment caveats.

## Later Mazda moves into a CAN-bus generation

Yatour separately defines a newer Mazda family for second-generation Mazda 3/5/6, MX-5, CX-7 and RX-8 applications and labels it as a CAN-bus family.

The guide also reports navigation compatibility and text-display capability for supported examples.

That is enough to define a hard family boundary: the later Mazda lane should not inherit the legacy CDC protocol simply because the source still behaves like a virtual changer to the driver.

## Family map

| Family | Established pre-hardware architecture | PD Bridge implication | Still hardware/source gated |
| --- | --- | --- | --- |
| legacy Mazda external-CDC family | broad dedicated changer-port ecosystem with head-unit/firmware caveats | direct CDC/source-emulation lane | exact serial protocol, electrical levels, controls, text behavior |
| Mazda 6 / RX-8 revision-sensitive legacy units | same broad era but activation/firmware matters | exact part/software must be in profile | jumper requirement, firmware-specific behavior |
| later Mazda CAN-bus family | vehicle-network-mediated accessory integration | CAN-aware adapter lane | exact CAN frames, source handshake, display ownership |
| Bose/navigation variants outside supported legacy sets | topology differs | separate target profiles | amplifier/nav coupling and source availability |

## Why pre-hardware research stops here

The family boundary and the key compatibility hazards are established. Public technical sources do not justify inventing a Mazda changer protocol or later CAN IDs.

Additional desk research would mainly produce more radio part numbers. A representative legacy head unit and a representative later CAN-era unit will answer the remaining architecture questions much more efficiently.

## Smallest useful later hardware set

1. one common legacy Mazda 3/6/RX-8-family head unit with an enabled external changer port;
2. one known revision-sensitive Mazda 6 or RX-8 only if the first unit suggests firmware/activation is material;
3. one later CAN-era Mazda unit.

## Questions deliberately left for hardware

- exact legacy CDC framing and signaling levels;
- exact activation/jumper behavior by radio part number;
- exact later CAN messages and bitrate;
- steering-control and display-text paths;
- whether physical-disc TOC/CD-TEXT leaves the in-dash drive;
- coexistence with Bose/navigation systems;
- whether the Draft 0.2 audio beacon survives the real Mazda audio path.

## Sources

All links checked on 2026-09-24.

- **Dension Gateway Lite hardware/cable documentation.** Dedicated CABL-MA1 Mazda integration family, with the general warning that cable-family support is not universal vehicle compatibility. https://techsupport.dension.com/638013-W-Gateway-hardware-versions-car-side-cables
- **Yatour YT-M06 application guide, mirror by Manualzz.** Legacy MAZ1 family, Mazda 6 internal-jumper caveat, RX-8 firmware caveat, head-unit/equipment exclusions, and separate MAZ2 later CAN-bus family with text/navigation support on compatible systems. https://manualzz.com/doc/23313500/yatour-yt-m06-digital-music-changer-user-manual
