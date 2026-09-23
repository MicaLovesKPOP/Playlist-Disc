# Vehicle/phone bridge protocol — design sketch

This protocol is intentionally not frozen with the physical disc format.

Vehicle adapters should eventually expose service-neutral events such as:

```text
POWER_ON
POWER_OFF
DISC_PRESENT PD1-042381
DISC_REMOVED
NEXT
PREVIOUS
PLAY_PAUSE
```

Playback software may return metadata events such as:

```text
NOW_PLAYING
  title = Supernova
  artist = aespa
  album = Armageddon
```

The same phone/playback layer should therefore work with an Alfa adapter, MINI adapter, PSA adapter, or future vehicle integration even when their electrical interfaces differ completely.
