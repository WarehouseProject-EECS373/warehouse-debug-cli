from typing import Tuple

from zlib import crc32
from enum import IntEnum


class Status(IntEnum):
    SUCCESS = 0
    UNDEFINED_ERROR = 1
    CRC_ERROR = 2


class EngineState(IntEnum):
    FUNCTIONAL = 0
    INACTIVE = 1
    ERROR = 2


class StcpEngine:
    HEADER = b"\x7A"
    FOOTER = b"\x7F\x7F"
    FOOTER_CHAR = b"\x7F"
    ESCAPE = b"\x7B"

    def __init__(self, send_fn) -> None:
        self._send = send_fn
        self._state = EngineState.FUNCTIONAL

    def _escape(self, data: bytes) -> bytes:
        data.replace(self.ESCAPE, self.ESCAPE + self.ESCAPE)
        data.replace(self.HEADER, self.ESCAPE + self.HEADER)
        data.replace(self.FOOTER_CHAR, self.ESCAPE + self.FOOTER_CHAR)
        return data

    def _unescape(self, data: bytes) -> bytes:
        data.replace(self.ESCAPE + self.ESCAPE, self.ESCAPE)
        data.replace(self.ESCAPE + self.HEADER, self.HEADER)
        data.replace(self.ESCAPE + self.FOOTER_CHAR, self.FOOTER_CHAR)
        return data

    def _wrap_data(self, payload: bytes) -> bytes:
        payload = self._escape(payload)
        crc = crc32(payload)
        message = (
            self.HEADER
            + payload
         #   + crc.to_bytes(length=4, byteorder="little")
            + self.FOOTER
        )
        return message

    def _unwrap_data(self, data: bytes) -> bytes:
        payload = data[1:-2]
        #crc = data[-6:-2]
        #if crc != crc32(payload).to_bytes(length=4, byteorder="little"):
#            return Status.CRC_ERROR

        payload = self._unescape(payload)

        return payload

    def write(self, data: bytes) -> Status:
        message = self._wrap_data(data)
        self._send(message)

    def handle_message(self, message) -> Tuple[Status, bytes]:
        payload = self._unwrap_data(message)
        return payload

    def is_connected(self) -> bool:
        return True

    def get_state(self) -> EngineState:
        return self._state

    def close(self) -> Status:
        return Status.SUCCESS
