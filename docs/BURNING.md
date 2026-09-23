# Burning draft discs

PDv1 draft discs require **Disc-At-Once** recording because their identity lives in the exact TOC. Track-At-Once software that inserts automatic two-second gaps will produce a different disc.

The reference backend is `cdrdao`.

```bash
pdv1 build 999901 --output build/PD1-999901
cd build/PD1-999901
cdrdao show-toc disc.toc
cdrdao write disc.toc
```

Or, when the CLI can find cdrdao:

```bash
pdv1 burn build/PD1-999901/disc.toc
```

Use test IDs only while the format is experimental. A Sharpie label is sufficient; avoid adhesive disc labels in slot-loading automotive mechanisms.
