from __future__ import annotations
from typing import List, Tuple
from .core import (
    WORD_BITS, ceil_div, bits_needed_unsigned, read_bits, write_bits, mask
)
from .header import PackedData, KIND_OVERFLOW

def _log2_ceil(n: int) -> int:
    if n <= 1:
        return 0
    return (n - 1).bit_length()

class BitPackingOverflow:
    def __init__(self, word_bits: int = WORD_BITS, k_prime: int | None = None, auto_select: bool = True):
        if word_bits != 32:
            raise ValueError("only 32-bit words supported")
        self.word_bits = word_bits
        self.k_prime_opt = k_prime
        self.auto_select = auto_select

    def _choose_params(self, arr: List[int]) -> Tuple[int, int, int, int]:
        """Retourne (k_prime, p, k_over, cost_bits_total) minimal."""
        if not arr:
            return (0, 0, 0, 0)
        vmax = max(arr)
        kmax = bits_needed_unsigned(vmax)
        if self.k_prime_opt is not None and not self.auto_select:
            k_prime = max(0, min(self.k_prime_opt, 32))
            # compute cost for this k'
            over_vals = [x for x in arr if bits_needed_unsigned(x) > k_prime]
            m = len(over_vals)
            p = 0 if m <= 1 else _log2_ceil(m)
            k_over = bits_needed_unsigned(max(over_vals) if over_vals else 0)
            s = 1 + max(k_prime, p)
            total = len(arr) * s + m * k_over
            return (k_prime, p, k_over, total)

        # auto search over 0..kmax
        best = None
        for k_prime in range(0, min(32, kmax) + 1):
            over_vals = [x for x in arr if bits_needed_unsigned(x) > k_prime]
            m = len(over_vals)
            p = 0 if m <= 1 else _log2_ceil(m)
            k_over = bits_needed_unsigned(max(over_vals) if over_vals else 0)
            s = 1 + max(k_prime, p)
            total = len(arr) * s + m * k_over
            cand = (k_prime, p, k_over, total)
            if best is None or cand[3] < best[3]:
                best = cand
        return best  # type: ignore

    def compress(self, arr: List[int]) -> PackedData:
        n = len(arr)
        if n == 0:
            return PackedData(words=[], n=0, kind=KIND_OVERFLOW, k_prime=0, p=0, k_over=0, main_bits=0, over_bits=0)

        # validation
        for x in arr:
            if x < 0 or x >= (1 << 32):
                raise ValueError("values must be 0 <= x < 2^32")

        k_prime, p, k_over, _ = self._choose_params(arr)
        s = 1 + max(k_prime, p)

        # marque les positions overflow + construit le tableau overflow
        overflow_values: List[int] = []
        overflow_index_per_pos: List[int] = [-1] * n
        limit_inline = 1 << k_prime
        for i, x in enumerate(arr):
            if bits_needed_unsigned(x) > k_prime:
                overflow_index_per_pos[i] = len(overflow_values)
                overflow_values.append(x)

        m = len(overflow_values)
        main_bits = n * s
        over_bits = m * k_over
        total_bits = main_bits + over_bits
        words_count = ceil_div(total_bits, self.word_bits) if total_bits > 0 else 0
        words = [0] * words_count

        # écrire zone principale
        bit_off = 0
        for i, x in enumerate(arr):
            if overflow_index_per_pos[i] == -1:
                # inline
                slot = (x & mask(k_prime)) << 1  # flag=0 en LSB
            else:
                idx = overflow_index_per_pos[i]
                if p == 0 and idx != 0:
                    # impossible si p==0, mais gardons le garde-fou
                    raise ValueError("internal: p==0 but multiple overflow indices")
                slot = ( (idx & mask(p)) << 1 ) | 0x1  # flag=1
            write_bits(words, bit_off, s, slot)
            bit_off += s

        # écrire zone overflow (valeurs brutes en k_over bits)
        bit_off_over = main_bits
        for v in overflow_values:
            write_bits(words, bit_off_over, k_over, v)
            bit_off_over += k_over

        return PackedData(
            words=words, n=n, kind=KIND_OVERFLOW,
            k_prime=k_prime, p=p, k_over=k_over,
            main_bits=main_bits, over_bits=over_bits
        )

    def get(self, i: int, data: PackedData) -> int:
        if i < 0 or i >= data.n:
            raise IndexError("index out of range")
        s = 1 + max(data.k_prime, data.p)
        slot = read_bits(data.words, i * s, s)
        flag = slot & 1
        if flag == 0:
            # inline
            return (slot >> 1) & mask(data.k_prime)
        # overflow
        idx = (slot >> 1) & mask(data.p) if data.p > 0 else 0
        if data.k_over == 0:
            return 0
        bit_off_over = data.main_bits + idx * data.k_over
        return read_bits(data.words, bit_off_over, data.k_over)

    def decompress(self, out: List[int], data: PackedData) -> None:
        if len(out) != data.n:
            raise ValueError("output buffer length must equal n")
        for i in range(data.n):
            out[i] = self.get(i, data)
