from pathlib import Path

import pytest

from playlistdisc.ble_transport import (
    BLE_ADAPTER_TO_HOST_UUID,
    BLE_HOST_TO_ADAPTER_UUID,
    BLE_SERVICE_UUID,
    MAX_FRAME_BYTES,
    BridgeFrameDecoder,
    BridgeFrameError,
    ble_profile,
    encode_bridge_frame,
    fragment_frame,
)
from playlistdisc.bridge import read_bridge_jsonl

ROOT = Path(__file__).parents[1]
MESSAGE = read_bridge_jsonl(ROOT / "tests/vectors/bridge-session.jsonl")[0]
SECOND = read_bridge_jsonl(ROOT / "tests/vectors/bridge-session.jsonl")[2]


def test_profile_has_stable_distinct_draft_uuids_and_reliable_properties():
    profile = ble_profile()
    assert profile["service_uuid"] == BLE_SERVICE_UUID
    assert len({BLE_SERVICE_UUID, BLE_ADAPTER_TO_HOST_UUID, BLE_HOST_TO_ADAPTER_UUID}) == 3
    assert profile["adapter_to_host"]["properties"] == ["indicate"]
    assert profile["host_to_adapter"]["write_type"] == "with_response"
    assert profile["framing"]["max_payload_bytes"] == MAX_FRAME_BYTES


def test_frame_encoding_is_deterministic():
    reordered = dict(reversed(list(MESSAGE.items())))
    assert encode_bridge_frame(MESSAGE) == encode_bridge_frame(reordered)


def test_decoder_handles_every_two_chunk_split():
    frame = encode_bridge_frame(MESSAGE)
    for split in range(1, len(frame)):
        decoder = BridgeFrameDecoder()
        assert decoder.feed(frame[:split]) == ()
        assert decoder.feed(frame[split:]) == (MESSAGE,)
        assert decoder.buffered_bytes == 0


def test_decoder_handles_one_byte_chunks():
    frame = encode_bridge_frame(MESSAGE)
    decoder = BridgeFrameDecoder()
    emitted = []
    for byte in frame:
        emitted.extend(decoder.feed(bytes([byte])))
    assert emitted == [MESSAGE]


def test_decoder_handles_multiple_frames_in_one_chunk():
    first = encode_bridge_frame(MESSAGE)
    second = encode_bridge_frame(SECOND)
    decoder = BridgeFrameDecoder()
    assert decoder.feed(first + second) == (MESSAGE, SECOND)


def test_fragment_frame_is_lossless_for_small_gatt_payloads():
    frame = encode_bridge_frame(MESSAGE)
    chunks = fragment_frame(frame, 20)
    assert chunks
    assert all(1 <= len(chunk) <= 20 for chunk in chunks)
    assert b"".join(chunks) == frame

    decoder = BridgeFrameDecoder()
    messages = []
    for chunk in chunks:
        messages.extend(decoder.feed(chunk))
    assert messages == [MESSAGE]


def test_zero_and_oversized_lengths_fail_and_require_reset():
    decoder = BridgeFrameDecoder()
    with pytest.raises(BridgeFrameError, match="empty payload"):
        decoder.feed(b"\x00\x00\x00\x00")
    assert decoder.failed
    with pytest.raises(BridgeFrameError, match="failed state"):
        decoder.feed(encode_bridge_frame(MESSAGE))

    decoder.reset()
    oversized = (MAX_FRAME_BYTES + 1).to_bytes(4, "big")
    with pytest.raises(BridgeFrameError, match="maximum"):
        decoder.feed(oversized)
    assert decoder.failed

    decoder.reset()
    assert decoder.feed(encode_bridge_frame(MESSAGE)) == (MESSAGE,)


def test_invalid_utf8_json_and_bridge_schema_fail_closed():
    bad_utf8 = (1).to_bytes(4, "big") + b"\xff"
    decoder = BridgeFrameDecoder()
    with pytest.raises(BridgeFrameError, match="UTF-8"):
        decoder.feed(bad_utf8)

    decoder.reset()
    payload = b"{not-json}"
    with pytest.raises(BridgeFrameError, match="valid JSON"):
        decoder.feed(len(payload).to_bytes(4, "big") + payload)

    decoder.reset()
    payload = b'{"not":"a bridge message"}'
    with pytest.raises(BridgeFrameError, match="invalid bridge message"):
        decoder.feed(len(payload).to_bytes(4, "big") + payload)


def test_encoder_rejects_invalid_bridge_message():
    with pytest.raises(BridgeFrameError, match="invalid bridge message"):
        encode_bridge_frame({"hello": "world"})


def test_custom_max_payload_is_enforced_on_both_sides():
    frame = encode_bridge_frame(MESSAGE)
    payload_length = int.from_bytes(frame[:4], "big")
    assert payload_length > 10
    with pytest.raises(BridgeFrameError, match="maximum"):
        encode_bridge_frame(MESSAGE, max_frame_bytes=10)

    decoder = BridgeFrameDecoder(max_frame_bytes=10)
    with pytest.raises(BridgeFrameError, match="maximum"):
        decoder.feed(frame[:4])


def test_documented_profile_vector_matches_reference_constants():
    import yaml

    documented = yaml.safe_load(
        (ROOT / "tests/vectors/ble-profile.yaml").read_text(encoding="utf-8")
    )
    assert documented == ble_profile()
