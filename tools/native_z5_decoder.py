#!/usr/bin/env python3
"""Experimental C56 0x40/Z5 model decoder. No original game payloads included.

The native table semantics are reconstructed; valid decode is not a guarantee
that the recovered model has complete UVs, materials or original appearance.
"""
from dataclasses import dataclass


class DecodeError(ValueError):
    pass


@dataclass
class BuiltTable:
    width: int
    entries: list[int]
    consumed: int
    symbols: int
    secondary_nodes: int
    bits_left: int


def build_table(data: bytes, offset: int, width: int) -> BuiltTable:
    if not 1 <= width <= 15:
        raise DecodeError("unsupported root width")
    field_size = 2 if width > 8 else 1
    if offset < 0 or offset + field_size > len(data):
        raise DecodeError("truncated table count")
    count = int.from_bytes(data[offset:offset + field_size], "little")
    span = count * 4 + 4
    if offset + span > len(data):
        raise DecodeError("truncated table description")
    entries = [0] * (2 << width)
    entries[1] = 2
    acc, bits, slot, secondary = 0, 0, 1, 0
    for byte in data[offset + field_size:offset + span]:
        acc = ((acc << 8) | byte) & 0xffffffff
        bits += 8
        while bits >= width and slot < (2 << width):
            shift = bits - width
            code = (acc >> shift) & ((1 << width) - 1)
            bits -= width
            acc &= (1 << bits) - 1 if bits else 0
            prior = entries[slot]
            if prior == 2:
                low = code & ((1 << (width - 2)) - 1 if width >= 2 else 0)
                child = slot + (low << 1) + 2 - (1 if slot & 1 else 0)
                if child < 0 or child + 1 >= len(entries):
                    raise DecodeError("secondary node out of range")
                entries[child] = 1 if (code << (16 - width)) & 0x8000 else 2
                entries[child + 1] = 1 if (code << (16 - width)) & 0x4000 else 2
                entries[slot] = low + 1
                secondary += 1
            else:
                entries[slot] = code | (0x8000 if prior != 0 else 0)
            slot += 1
    return BuiltTable(width, entries, span, slot - 1, secondary, bits)


class _WordBitReader:
    def __init__(self, data: bytes, offset: int):
        self.data, self.pos = data, offset
        self.word, self.remaining = 0, 0

    def bit(self) -> int:
        if not self.remaining:
            if self.pos + 4 > len(self.data):
                raise DecodeError("truncated compressed bitstream")
            self.word = int.from_bytes(self.data[self.pos:self.pos + 4], "little")
            self.pos += 4
            self.remaining = 32
        self.remaining -= 1
        return (self.word >> self.remaining) & 1

    def bits(self, count: int) -> int:
        value = 0
        for _ in range(count):
            value = (value << 1) | self.bit()
        return value


def _symbol(reader: _WordBitReader, table: BuiltTable) -> int:
    base = 2
    for _ in range(64):
        base_index = base + reader.bit()
        if base_index >= len(table.entries):
            raise DecodeError("lookup table out of range")
        entry = table.entries[base_index]
        if entry & 0x8000:
            return entry & 0x7fff
        base += entry * 2
        if base + 1 >= len(table.entries):
            raise DecodeError("continuation lookup exceeds table")
    raise DecodeError("excessive continuation depth")


def decode_stream(data: bytes, *, max_output: int = 16 * 1024 * 1024) -> bytes:
    if len(data) < 4 or data[0] != 0x40:
        raise DecodeError("expected native 0x40 stream")
    size = int.from_bytes(data[:4], "little") >> 8
    pos = 4
    if size == 0:
        if len(data) < 8:
            raise DecodeError("missing extended output size")
        size = int.from_bytes(data[4:8], "little")
        pos = 8
    if not 0 < size <= max_output:
        raise DecodeError("output size outside safety limit")
    primary = build_table(data, pos, 9)
    pos += primary.consumed
    secondary = build_table(data, pos, 5)
    pos += secondary.consumed
    reader = _WordBitReader(data, pos)
    output = bytearray()
    while len(output) < size:
        symbol = _symbol(reader, primary)
        if not (symbol & 0x100):
            output.append(symbol & 0xff)
            continue
        length = 3 + (symbol & 0xff)
        distance_class = _symbol(reader, secondary) & 0xff
        if distance_class == 0:
            distance_code = 0
        elif distance_class == 1:
            distance_code = 1
        else:
            distance_code = (1 << (distance_class - 1)) | reader.bits(distance_class - 1)
        distance = distance_code + 1
        if distance > len(output):
            raise DecodeError("back-reference before output start")
        for _ in range(min(length, size - len(output))):
            output.append(output[-distance])
    return bytes(output)


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--payload-offset", type=lambda x: int(x, 0), default=32)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    try:
        decoded = decode_stream(raw[args.payload_offset:])
    except DecodeError as error:
        parser.exit(1, f"DECODE FAILED (experimental): {error}\n")
    if args.output:
        args.output.write_bytes(decoded)
    print(f"Decoded {len(decoded)} bytes")
