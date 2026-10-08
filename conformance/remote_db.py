"""Codec and client for the rekordbox remote-database protocol."""

from __future__ import annotations

import socket
import struct
from dataclasses import dataclass


MAGIC = 0x872349AE
PORT_QUERY = 12523
PORT_QUERY_REQUEST = b"\x00\x00\x00\x0fRemoteDBServer\0"
GREETING = b"\x11\x00\x00\x00\x01"
SETUP_TXID = 0xFFFFFFFE
SETUP_MAGIC = 0x14

SETUP = 0x0000
RENDER = 0x3000
MENU_HEADER = 0x4000
ERROR = 0x4003
MENU_ITEM = 0x4101
MENU_FOOTER = 0x4201

MAX_PENDING_BYTES = 16 * 1024 * 1024
MAX_TAG_SLOTS = 32
HEADER_LENGTH = 20


class IncompleteMessage(ValueError):
    pass


@dataclass(frozen=True)
class Argument:
    type: str
    value: int | str | bytes

    @classmethod
    def number(cls, value: int) -> Argument:
        return cls("number", value & 0xFFFFFFFF)

    @classmethod
    def string(cls, value: str) -> Argument:
        return cls("string", value)

    @classmethod
    def blob(cls, value: bytes) -> Argument:
        return cls("blob", value)

    @property
    def argument_tag(self) -> int:
        return {"string": 0x02, "blob": 0x03, "number": 0x06}[self.type]

    def encode(self) -> bytes:
        if self.type == "number":
            return b"\x11" + struct.pack(">I", int(self.value))

        if self.type == "blob":
            value = bytes(self.value)
            return b"\x14" + struct.pack(">I", len(value)) + value

        value = str(self.value).encode("utf-16-be", "surrogatepass")
        units = len(value) // 2 + 1
        return b"\x26" + struct.pack(">I", units) + value + b"\0\0"

    def as_json(self) -> dict[str, object]:
        if self.type == "blob":
            return {"type": "blob", "hex": bytes(self.value).hex()}

        return {"type": self.type, "value": self.value}


@dataclass(frozen=True)
class Message:
    transaction: int
    kind: int
    arguments: tuple[Argument, ...]

    def encode(self, tag_slots: int | None = None) -> bytes:
        count = min(len(self.arguments), MAX_TAG_SLOTS)
        slots = count if tag_slots is None else tag_slots
        if slots < count or slots > MAX_TAG_SLOTS:
            raise ValueError(
                f"fixed tag slots must be between argument count {count} and 32"
            )

        header = b"".join(
            (
                b"\x11",
                struct.pack(">I", MAGIC),
                b"\x11",
                struct.pack(">I", self.transaction),
                b"\x10",
                struct.pack(">H", self.kind),
                b"\x0f",
                bytes((count,)),
                b"\x14",
                struct.pack(">I", slots),
            )
        )
        tags = bytes(argument.argument_tag for argument in self.arguments[:count])
        tags += bytes(slots - count)
        fields = b"".join(
            argument.encode()
            for argument in self.arguments[:count]
            if not (argument.type == "blob" and argument.value == b"")
        )
        return header + tags + fields

    @classmethod
    def decode(cls, data: bytes) -> tuple[Message, int]:
        if len(data) < HEADER_LENGTH:
            raise IncompleteMessage

        magic = struct.unpack_from(">I", data, 1)[0]
        if (
            data[0] != 0x11
            or magic != MAGIC
            or data[5] != 0x11
            or data[10] != 0x10
            or data[13] != 0x0F
            or data[15] != 0x14
        ):
            raise ValueError(f"not a database message: magic was {magic:#010x}")

        transaction = struct.unpack_from(">I", data, 6)[0]
        kind = struct.unpack_from(">H", data, 11)[0]
        count = data[14]
        slots = struct.unpack_from(">I", data, 16)[0]
        if count > MAX_TAG_SLOTS:
            raise ValueError(f"message declares {count} arguments")
        if slots < count or slots > MAX_TAG_SLOTS:
            raise ValueError(f"invalid argument tag list length {slots}")
        if len(data) < HEADER_LENGTH + slots:
            raise IncompleteMessage

        declared = data[HEADER_LENGTH : HEADER_LENGTH + count]
        offset = HEADER_LENGTH + slots
        arguments: list[Argument] = []
        for declared_tag in declared:
            if declared_tag == 0x03 and (
                not arguments
                or (
                    arguments[-1].type == "number"
                    and arguments[-1].value == 0
                )
            ):
                arguments.append(Argument.blob(b""))
                continue

            if offset >= len(data):
                raise IncompleteMessage
            field_tag = data[offset]
            offset += 1

            if field_tag in (0x0F, 0x10, 0x11):
                width = {0x0F: 1, 0x10: 2, 0x11: 4}[field_tag]
                if offset + width > len(data):
                    raise IncompleteMessage
                value = int.from_bytes(data[offset : offset + width], "big")
                offset += width
                arguments.append(Argument.number(value))
                continue

            if field_tag == 0x14:
                if offset + 4 > len(data):
                    raise IncompleteMessage
                length = struct.unpack_from(">I", data, offset)[0]
                offset += 4
                if offset + length > len(data):
                    raise IncompleteMessage
                arguments.append(Argument.blob(data[offset : offset + length]))
                offset += length
                continue

            if field_tag == 0x26:
                if offset + 4 > len(data):
                    raise IncompleteMessage
                units = struct.unpack_from(">I", data, offset)[0]
                offset += 4
                length = units * 2
                if offset + length > len(data):
                    raise IncompleteMessage
                raw = data[offset : offset + length]
                offset += length
                terminator = next(
                    (index for index in range(0, len(raw), 2) if raw[index : index + 2] == b"\0\0"),
                    len(raw),
                )
                text = raw[:terminator].decode("utf-16-be", "replace")
                arguments.append(Argument.string(text))
                continue

            raise ValueError(f"unknown argument field tag {field_tag:#04x}")

        return cls(transaction, kind, tuple(arguments)), offset

    @classmethod
    def decode_all(cls, data: bytes) -> tuple[list[Message], int]:
        messages: list[Message] = []
        offset = 0
        while offset < len(data):
            try:
                message, used = cls.decode(data[offset:])
            except (IncompleteMessage, ValueError):
                break
            messages.append(message)
            offset += used
        return messages, offset

    def as_json(self, *, transaction: bool = False) -> dict[str, object]:
        value: dict[str, object] = {
            "kind": self.kind,
            "arguments": [argument.as_json() for argument in self.arguments],
        }
        if transaction:
            value = {"transaction": self.transaction, **value}
        return value


def database_port(host: str, query_port: int) -> int:
    with socket.create_connection((host, query_port), timeout=3) as connection:
        connection.settimeout(3)
        connection.sendall(PORT_QUERY_REQUEST)
        answer = receive_exact(connection, 2)
    return int.from_bytes(answer, "big")


def receive_exact(connection: socket.socket, length: int) -> bytes:
    output = bytearray()
    while len(output) < length:
        chunk = connection.recv(length - len(output))
        if not chunk:
            raise EOFError("dbserver closed the connection")
        output.extend(chunk)
    return bytes(output)


def is_setup_reply(mode: str, message: Message) -> bool:
    if message.transaction != SETUP_TXID:
        return False
    if mode == "extended":
        return message.kind == SETUP
    if mode == "legacy":
        return (
            message.kind == MENU_HEADER
            and len(message.arguments) >= 2
            and message.arguments[0] == Argument.number(0)
            and message.arguments[1].type == "number"
        )
    return False


def is_usable_setup_reply(message: Message) -> bool:
    return message.transaction == SETUP_TXID and message.kind in (SETUP, MENU_HEADER)


class Client:
    def __init__(
        self,
        connection: socket.socket,
        read_timeout_ms: int,
        setup_exchange: dict[str, object],
    ) -> None:
        self.connection = connection
        self.read_timeout = read_timeout_ms / 1000
        self.pending = bytearray()
        self.transaction = 0
        self.setup_exchange = setup_exchange

    @classmethod
    def connect(
        cls,
        host: str,
        query_port: int,
        device: int,
        setup: str,
        read_timeout_ms: int,
        strict_setup: bool,
    ) -> Client:
        port = database_port(host, query_port)
        if port == 0xFFFF:
            raise RuntimeError(
                "Link Export is disabled; select the LINK source in Export mode"
            )
        if port == 0:
            raise RuntimeError("port query returned invalid dbserver port 0")

        connection = socket.create_connection((host, port), timeout=3)
        connection.settimeout(read_timeout_ms / 1000)
        connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            connection.sendall(GREETING)
            if receive_exact(connection, len(GREETING)) != GREETING:
                raise RuntimeError("unexpected dbserver greeting")

            if setup == "legacy":
                arguments = (Argument.number(device),)
            elif setup == "extended":
                arguments = (Argument.number(device), Argument.number(SETUP_MAGIC))
            else:
                raise ValueError(f"unknown setup mode {setup!r}")

            request = Message(SETUP_TXID, SETUP, arguments)
            client = cls(connection, read_timeout_ms, {})
            client.send(request)
            response = client.receive()
            valid = any(
                is_setup_reply(setup, message)
                or (not strict_setup and is_usable_setup_reply(message))
                for message in response
            )
            if not valid:
                raise RuntimeError(f"setup returned no setup reply: {response!r}")
            client.setup_exchange = {
                "mode": setup,
                "request": request.as_json(transaction=True),
                "response": [
                    message.as_json(transaction=True) for message in response
                ],
            }
            return client
        except Exception:
            connection.close()
            raise

    def close(self) -> None:
        self.connection.close()

    def send(self, message: Message, *, tag_slots: int | None = None) -> None:
        self.connection.sendall(message.encode(tag_slots))

    def request(self, kind: int, arguments: list[Argument]) -> list[Message]:
        self.transaction = (self.transaction + 1) & 0xFFFFFFFF
        self.send(Message(self.transaction, kind, tuple(arguments)))
        return self.receive()

    def receive(self) -> list[Message]:
        while True:
            messages, used = Message.decode_all(bytes(self.pending))
            if messages:
                del self.pending[:used]
                return messages

            chunk = self.connection.recv(8192)
            if not chunk:
                raise EOFError("dbserver closed the connection")
            self.pending.extend(chunk)
            if len(self.pending) > MAX_PENDING_BYTES:
                raise RuntimeError("dbserver response exceeded pending-byte limit")

    def request_raw(
        self,
        kind: int,
        arguments: list[Argument],
        read_ms: int,
        tag_slots: int | None,
    ) -> dict[str, object]:
        self.transaction = (self.transaction + 1) & 0xFFFFFFFF
        message = Message(self.transaction, kind, tuple(arguments))
        return self.raw_probe(message.encode(tag_slots), read_ms)

    def raw_probe(self, payload: bytes, read_ms: int) -> dict[str, object]:
        try:
            self.connection.sendall(payload)
        except (BrokenPipeError, ConnectionError) as error:
            return raw_result("disconnect", error)

        self.connection.settimeout(read_ms / 1000)
        try:
            raw = self.connection.recv(8192)
            if not raw:
                return raw_result("disconnect")
            messages, used = Message.decode_all(raw)
            return {
                "outcome": "raw_reply",
                "error_kind": None,
                "raw_hex": raw.hex(),
                "decoded_bytes": used,
                "messages": [message.as_json() for message in messages],
            }
        except TimeoutError as error:
            return raw_result("timeout", error)
        except (BrokenPipeError, ConnectionError) as error:
            return raw_result("disconnect", error)
        finally:
            self.connection.settimeout(self.read_timeout)


def raw_result(outcome: str, error: BaseException | None = None) -> dict[str, object]:
    return {
        "outcome": outcome,
        "error_kind": error_kind(error) if error else None,
        "raw_hex": "",
        "messages": [],
    }


def transport_outcome(error: BaseException) -> tuple[str, str] | None:
    if isinstance(error, (TimeoutError, socket.timeout)):
        return "timeout", error_kind(error)
    if isinstance(error, (EOFError, BrokenPipeError, ConnectionError)):
        return "disconnect", error_kind(error)
    return None


def error_kind(error: BaseException) -> str:
    if isinstance(error, (TimeoutError, socket.timeout)):
        return "TimedOut"
    if isinstance(error, ConnectionResetError):
        return "ConnectionReset"
    if isinstance(error, BrokenPipeError):
        return "BrokenPipe"
    if isinstance(error, EOFError):
        return "UnexpectedEof"
    if isinstance(error, ConnectionAbortedError):
        return "ConnectionAborted"
    return type(error).__name__
