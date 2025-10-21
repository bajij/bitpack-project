from __future__ import annotations
from dataclasses import dataclass
import struct
from typing import List

# Header binaire: 13 champs uint32 little-endian => 52 octets
# version, kind, endianness, word_bits, n, k, cap, k_prime, p, k_over, main_bits, over_bits, words_count
_HDR_FMT = "<13I"
_HDR_SIZE = struct.calcsize(_HDR_FMT)

KIND_CROSSING = 0
KIND_ALIGNED = 1
KIND_OVERFLOW = 2

ENDIAN_LITTLE = 0
ENDIAN_BIG = 1  # réservé, on n'utilise que L.E. mais on le note dans l'en-tête

@dataclass
class PackedData:
    words: List[int]
    n: int
    kind: int
    # params Crossing/Aligned
    k: int = 0
    cap: int = 0
    # params Overflow
    k_prime: int = 0
    p: int = 0
    k_over: int = 0
    main_bits: int = 0
    over_bits: int = 0
    # format
    endianness: int = ENDIAN_LITTLE
    word_bits: int = 32
    version: int = 1

    def to_bytes(self) -> bytes:
        words_count = len(self.words)
        header = struct.pack(
            _HDR_FMT,
            self.version,
            self.kind,
            self.endianness,
            self.word_bits,
            self.n,
            self.k,
            self.cap,
            self.k_prime,
            self.p,
            self.k_over,
            self.main_bits,
            self.over_bits,
            words_count,
        )
        # sérialise chaque mot en u32 little-endian
        body = b"".join((w & 0xFFFFFFFF).to_bytes(4, "little") for w in self.words)
        return header + body

    @staticmethod
    def from_bytes(data: bytes) -> "PackedData":
        if len(data) < _HDR_SIZE:
            raise ValueError("buffer too small for header")
        fields = struct.unpack(_HDR_FMT, data[:_HDR_SIZE])
        (
            version,
            kind,
            endianness,
            word_bits,
            n,
            k,
            cap,
            k_prime,
            p,
            k_over,
            main_bits,
            over_bits,
            words_count,
        ) = fields
        if endianness != ENDIAN_LITTLE:
            raise ValueError("only little-endian payloads are supported")
        body = data[_HDR_SIZE:]
        if len(body) != words_count * 4:
            raise ValueError("payload size does not match words_count")
        words = [int.from_bytes(body[i:i+4], "little") for i in range(0, len(body), 4)]
        return PackedData(
            words=words,
            n=n,
            kind=kind,
            k=k,
            cap=cap,
            k_prime=k_prime,
            p=p,
            k_over=k_over,
            main_bits=main_bits,
            over_bits=over_bits,
            endianness=endianness,
            word_bits=word_bits,
            version=version,
        )
