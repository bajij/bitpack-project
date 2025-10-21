from __future__ import annotations
from typing import List
from .core import WORD_BITS, ceil_div, bits_needed_unsigned, write_bits, read_bits
from .header import PackedData, KIND_CROSSING

class BitPackingCrossing:
    def __init__(self, word_bits: int = WORD_BITS):
        if word_bits != 32:
            raise ValueError("only 32-bit words supported")
        self.word_bits = word_bits

    def _k_from_data(self, arr: List[int]) -> int:
        maxv = max(arr) if arr else 0
        k = bits_needed_unsigned(maxv)
        return min(k, 32)

    def compress(self, arr: List[int]) -> PackedData:
        n = len(arr)
        k = self._k_from_data(arr)
        if k == 0:
            return PackedData(words=[], n=n, kind=KIND_CROSSING, k=0)
        total_bits = n * k
        words_count = ceil_div(total_bits, self.word_bits)
        words = [0] * (words_count if total_bits > 0 else 0)
        bit_off = 0
        limit = (1 << k)
        for x in arr:
            if x < 0 or x >= (1 << 32):
                raise ValueError("values must be 0 <= x < 2^32")
            if x >= limit:
                raise ValueError(f"value {x} exceeds {k} bits; use overflow variant")
            write_bits(words, bit_off, k, x)
            bit_off += k
        return PackedData(
            words=words,
            n=n,
            kind=KIND_CROSSING,
            k=k,
        )

    def get(self, i: int, data: PackedData) -> int:
        if i < 0 or i >= data.n:
            raise IndexError("index out of range")
        k = data.k
        if k == 0:
            return 0
        bit_off = i * k
        return read_bits(data.words, bit_off, k)

    def decompress(self, out: List[int], data: PackedData) -> None:
        if len(out) != data.n:
            raise ValueError("output buffer length must equal n")
        for i in range(data.n):
            out[i] = self.get(i, data)
