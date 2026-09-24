# Honda / Acura factory changer pre-hardware family research

This note maps the practical Honda/Acura changer-era families visible in commercial integration data. The useful result is a conservative generation split, not a claim that one undocumented Honda protocol can be implemented from desk research alone.

## Evidence classes

Dension and Yatour compatibility material is used to establish reusable connector/head-unit families and exclusions. Public technical documentation for the later Honda-specific changer protocol is sparse enough that low-level protocol details are intentionally deferred to bench captures rather than reconstructed from scattered forum claims.

## Older Honda/Acura systems overlap Alpine M-Bus

Yatour's application guide defines an older Honda/Acura family using an Alpine M-Bus-compatible connection. Its listed applications include late-1990s/early-2000s Accord, Civic, CR-V, Odyssey, Prelude, S2000 and related Acura models.

The same guide separately lists ordinary Alpine M-Bus head units and some Honda OEM Alpine units under its M-Bus product family.

That is a useful architectural result: a meaningful subset of older Honda/Acura factory audio can be approached as an existing aftermarket-head-unit bus rather than as an entirely Honda-specific protocol.

## Later Honda/Acura uses a distinct Honda-specific connector family

Yatour separately defines a later Honda white-connector family across 2000s Accord, Civic, CR-V, Element, Odyssey, Pilot, Fit, S2000 and Acura CSX/MDX/RDX/TSX applications.

The guide documents optional Y-cable arrangements where navigation, XM or AUX already occupies the relevant resource and offers a switch arrangement that can retain an existing changer on supported configurations.

Dension independently groups Honda and Acura behind a dedicated CABL-HB1 cable family.

The safe conclusion is therefore a hard generation boundary: **older Alpine/M-Bus-derived Honda integration and later Honda-specific changer integration must not be assumed protocol-compatible.**

## Built-in changer and navigation variants are important exclusions

The Yatour guide explicitly excludes some older Honda/Acura applications with a built-in changer from its older plug-and-play path and distinguishes navigation/XM-equipped later systems.

That matters for PDv1 because "supports CDs" does not imply "has a usable external changer interface." A future compatibility profile should record:

- exact head-unit part/model;
- navigation/non-navigation;
- built-in versus external changer topology;
- connector family;
- whether another factory module already occupies the changer/accessory connection.

## Family map

| Family | Established pre-hardware architecture | PD Bridge implication | Still hardware/source gated |
| --- | --- | --- | --- |
| older OEM Alpine / M-Bus Honda-Acura | overlaps a known Alpine M-Bus changer ecosystem | can share aftermarket M-Bus research/adapter concepts | exact OEM deviations, electrical levels, text/control behavior |
| later Honda white-connector changer family | broad reusable Honda/Acura external-device family | Honda-specific adapter lane | actual protocol framing, handshake, text semantics, controls |
| built-in-changer/navigation/XM variants | source/resource topology differs | profile exact equipment; do not infer external-CDC availability | coexistence and switching behavior |
| later integrated/touchscreen systems | outside this changer-era lane | separate future generation only if needed | architecture-specific research |

## Why low-level reverse engineering stops here

Unlike Ford ACP or Toyota AVC-LAN, the current public-source set does not provide a sufficiently strong, well-scoped technical reference to promote later Honda changer bytes, bus timing or electrical levels into project documentation.

More desk research would mostly collect forum constants of uncertain provenance. The next useful evidence for that layer is a representative head unit plus logic capture.

This lane is therefore considered sufficiently mapped for pre-hardware breadth, while implementation remains intentionally hardware-gated.

## Smallest useful later hardware set

1. one older Honda/Acura OEM Alpine/M-Bus head unit;
2. one common later Honda white-connector head unit;
3. only add a navigation/XM example if coexistence becomes a project requirement.

## Questions deliberately left for hardware

- exact later-Honda changer protocol, signaling levels and initialization;
- whether OEM steering controls are carried through the changer interface or a separate vehicle bus;
- CD-TEXT/text-display support by head-unit revision;
- coexistence with XM/navigation/AUX and factory changer modules;
- whether physical-disc TOC/timing leaves the in-dash drive;
- whether the Draft 0.2 audio beacon survives real Honda/Acura optical/audio paths.

## Sources

All links checked on 2026-09-24.

- **Dension Gateway Lite hardware/cable documentation.** Dedicated CABL-HB1 Honda/Acura family and separation between European- and Asian-spec Gateway hardware. https://techsupport.dension.com/638013-W-Gateway-hardware-versions-car-side-cables
- **Yatour YT-M06 application guide, mirror by Manualzz.** Older Honda/Acura Alpine M-Bus family, later Honda white-connector family, navigation/XM/AUX coexistence notes, built-in changer exclusions and broad model/head-unit applications. https://manualzz.com/doc/23313500/yatour-yt-m06-digital-music-changer-user-manual
