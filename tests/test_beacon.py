from pathlib import Path
import wave

from playlistdisc.beacon import SAMPLE_RATE, write_beacon_wav
from playlistdisc.identity import PDIdentity


def test_beacon_wav_is_exactly_four_seconds(tmp_path: Path):
    path = write_beacon_wav(PDIdentity(999902), tmp_path / "beacon.wav")
    with wave.open(str(path), "rb") as wav:
        assert wav.getnchannels() == 2
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == SAMPLE_RATE
        assert wav.getnframes() == SAMPLE_RATE * 4
