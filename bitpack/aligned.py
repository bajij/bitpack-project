from __future__ import annotations
from typing import List
from .core import WORD_BITS, bits_needed_unsigned, ceil_div
from .header import PackedData, KIND_ALIGNED

class BitPackingAligned:
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
            return PackedData(words=[], n=n, kind=KIND_ALIGNED, k=0, cap=0)
        cap = self.word_bits // k
        if cap <= 0:
            cap = 1  # k==32 => cap=1
        words_count = ceil_div(n, cap)
        words = [0] * words_count
        limit = (1 << k)
        for i, x in enumerate(arr):
            if x < 0 or x >= (1 << 32):
                raise ValueError("values must be 0 <= x < 2^32")
            if x >= limit:
                raise ValueError(f"value {x} exceeds {k} bits; use overflow variant")
            w = i // cap
            shift = (i % cap) * k
            words[w] = (words[w] | (x << shift)) & 0xFFFFFFFF
        return PackedData(
            words=words,
            n=n,
            kind=KIND_ALIGNED,
            k=k,
            cap=cap,
        )

    def get(self, i: int, data: PackedData) -> int:
        if i < 0 or i >= data.n:
            raise IndexError("index out of range")
        k = data.k
        if k == 0:
            return 0
        cap = data.cap if data.cap else (32 // k or 1)
        w = i // cap
        shift = (i % cap) * k
        return (data.words[w] >> shift) & ((1 << k) - 1 if k < 32 else 0xFFFFFFFF)

    def decompress(self, out: List[int], data: PackedData) -> None:
        if len(out) != data.n:
            raise ValueError("output buffer length must equal n")
        for i in range(data.n):
            out[i] = self.get(i, data)
