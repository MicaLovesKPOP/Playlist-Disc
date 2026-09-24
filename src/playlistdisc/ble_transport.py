"""Draft BLE transport framing for logical PD Bridge messages.

This module is deliberately independent of any Bluetooth library. It defines the
wire bytes that a BLE GATT implementation carries and can therefore be tested on a
normal computer before a phone or vehicle adapter exists.
"""

from __future__ import annotations

import json
from typing import Any

from .bridge import validate_bridge_message

BLE_PROFILE_VERSION = "0.1"
BLE_SERVICE_UUID = "5c1d3a30-1f5b-4f6a-9d3e-3b8c77e2d001"
BLE_ADAPTER_TO_HOST_UUID = "5c1d3a30-1f5b-4f6a-9d3e-3b8c77e2d002"
BLE_HOST_TO_ADAPTER_UUID = "5c1d3a30-1f5b-4f6a-9d3e-3b8c77e2d003"

FRAME_HEADER_BYTES = 4
MAX_FRAME_BYTES = 16_384


class BridgeFrameError(ValueError):
    """The framed byte stream is invalid and must be reset/reconnected."""


def ble_profile() -> dict[str, Any]:
    """Return the Draft 0.1 GATT contract as inspectable data."""
    return {
        "profile": "PD Bridge BLE",
        "version": BLE_PROFILE_VERSION,
        "service_uuid": BLE_SERVICE_UUID,
        "adapter_to_host": {
            "uuid": BLE_ADAPTER_TO_HOST_UUID,
            "properties": ["indicate"],
        },
        "host_to_adapter": {
            "uuid": BLE_HOST_TO_ADAPTER_UUID,
            "properties": ["write"],
            "write_type": "with_response",
        },
        "framing": {
            "length_prefix": "uint32-big-endian",
            "encoding": "utf-8-json",
            "max_payload_bytes": MAX_FRAME_BYTES,
        },
    }


def _canonical_bridge_json(message: dict[str, Any]) -> bytes:
    errors = validate_bridge_message(message)
    if errors:
        raise BridgeFrameError("invalid bridge message: " + "; ".join(errors))
    return json.dumps(
        message,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def encode_bridge_frame(
    message: dict[str, Any],
    *,
    max_frame_bytes: int = MAX_FRAME_BYTES,
) -> bytes:
    """Encode one validated PD Bridge message as length-prefixed UTF-8 JSON."""
    if max_frame_bytes <= 0:
        raise ValueError("max_frame_bytes must be positive")
    payload = _canonical_bridge_json(message)
    if not payload:
        raise BridgeFrameError("bridge frame payload must not be empty")
    if len(payload) > max_frame_bytes:
        raise BridgeFrameError(
            f"bridge frame payload is {len(payload)} bytes; "
            f"maximum is {max_frame_bytes}"
        )
    return len(payload).to_bytes(FRAME_HEADER_BYTES, "big") + payload


def fragment_frame(frame: bytes, max_chunk_bytes: int) -> tuple[bytes, ...]:
    """Split an encoded frame into arbitrary GATT-sized transport chunks."""
    if max_chunk_bytes <= 0:
        raise ValueError("max_chunk_bytes must be positive")
    value = bytes(frame)
    if not value:
        return ()
    return tuple(
        value[offset : offset + max_chunk_bytes]
        for offset in range(0, len(value), max_chunk_bytes)
    )


class BridgeFrameDecoder:
    """Incrementally decode arbitrary chunks of a framed PD Bridge byte stream.

    A framing/JSON/schema error enters a failed state. The caller must reset the
    decoder (normally on BLE reconnect) before accepting any more bytes. This avoids
    attempting unsafe byte-level resynchronization after a corrupted length prefix.
    """

    def __init__(self, *, max_frame_bytes: int = MAX_FRAME_BYTES) -> None:
        if max_frame_bytes <= 0:
            raise ValueError("max_frame_bytes must be positive")
        self.max_frame_bytes = max_frame_bytes
        self._buffer = bytearray()
        self._failed = False

    @property
    def failed(self) -> bool:
        return self._failed

    @property
    def buffered_bytes(self) -> int:
        return len(self._buffer)

    def reset(self) -> None:
        self._buffer.clear()
        self._failed = False

    def _fail(self, message: str) -> None:
        self._buffer.clear()
        self._failed = True
        raise BridgeFrameError(message)

    def feed(self, chunk: bytes | bytearray | memoryview) -> tuple[dict[str, Any], ...]:
        """Feed arbitrary transport bytes and return all complete validated messages."""
        if self._failed:
            raise BridgeFrameError(
                "bridge frame decoder is in failed state; reset/reconnect required"
            )
        try:
            self._buffer.extend(bytes(chunk))
        except (TypeError, ValueError) as exc:
            self._fail(f"bridge frame chunk is not bytes-like: {exc}")

        messages: list[dict[str, Any]] = []
        while True:
            if len(self._buffer) < FRAME_HEADER_BYTES:
                break

            payload_length = int.from_bytes(
                self._buffer[:FRAME_HEADER_BYTES],
                "big",
            )
            if payload_length == 0:
                self._fail("bridge frame declares an empty payload")
            if payload_length > self.max_frame_bytes:
                self._fail(
                    f"bridge frame declares {payload_length} bytes; "
                    f"maximum is {self.max_frame_bytes}"
                )

            total_length = FRAME_HEADER_BYTES + payload_length
            if len(self._buffer) < total_length:
                break

            payload = bytes(self._buffer[FRAME_HEADER_BYTES:total_length])
            del self._buffer[:total_length]

            try:
                text = payload.decode("utf-8")
            except UnicodeDecodeError as exc:
                self._fail(f"bridge frame payload is not valid UTF-8: {exc}")

            try:
                value = json.loads(text)
            except json.JSONDecodeError as exc:
                self._fail(f"bridge frame payload is not valid JSON: {exc.msg}")

            if not isinstance(value, dict):
                self._fail("bridge frame JSON must be an object")

            errors = validate_bridge_message(value)
            if errors:
                self._fail("invalid bridge message: " + "; ".join(errors))
            messages.append(value)

        return tuple(messages)
