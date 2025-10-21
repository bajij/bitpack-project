from __future__ import annotations
from typing import List

U32_MASK = 0xFFFFFFFF
WORD_BITS = 32

def u32(x: int) -> int:
    return x & U32_MASK

def mask(k: int) -> int:
    if k <= 0:
        return 0
    if k >= WORD_BITS:
        # 32 bits => tous les bits à 1 sur 32
        return U32_MASK
    return (1 << k) - 1

def ceil_div(a: int, b: int) -> int:
    return -(-a // b)

def bits_needed_unsigned(x: int) -> int:
    """Nombre de bits nécessaires pour représenter x>=0 en non-signé."""
    if x <= 0:
        return 0
    return x.bit_length()

def read_bits(words: List[int], bit_off: int, k: int) -> int:
    """Lit k bits à partir du décalage global bit_off dans words (LSB-first, 32b)."""
    if k == 0:
        return 0
    w = bit_off // WORD_BITS
    shift = bit_off % WORD_BITS
    if shift + k <= WORD_BITS:
        return (words[w] >> shift) & mask(k)
    # chevauchement sur deux mots
    low = WORD_BITS - shift
    part1 = (words[w] >> shift) & mask(low)
    part2 = words[w + 1] & mask(k - low)
    return part1 | (part2 << low)

def write_bits(words: List[int], bit_off: int, k: int, value: int) -> None:
    """Écrit k bits de value à bit_off en LSB-first. words doit être déjà dimensionné."""
    if k == 0:
        return
    value &= mask(k)
    w = bit_off // WORD_BITS
    shift = bit_off % WORD_BITS
    if shift + k <= WORD_BITS:
        words[w] = u32(words[w] | (value << shift))
        return
    # chevauchement
    low = WORD_BITS - shift
    part1 = value & mask(low)
    part2 = value >> low
    words[w] = u32(words[w] | (part1 << shift))
    words[w + 1] = u32(words[w + 1] | part2)
