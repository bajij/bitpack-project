from __future__ import annotations
from typing import List
import random

def uniform_u32(n: int, k: int, seed: int = 123) -> List[int]:
    rnd = random.Random(seed)
    limit = 1 << k
    return [rnd.randrange(0, limit) for _ in range(n)]

def skewed(n: int, k_small: int, k_large: int, ratio_large: float = 0.001, seed: int = 123) -> List[int]:
    rnd = random.Random(seed)
    small_lim = 1 << k_small
    large_lim = 1 << k_large
    arr = []
    for _ in range(n):
        if rnd.random() < ratio_large:
            arr.append(rnd.randrange(small_lim, large_lim))
        else:
            arr.append(rnd.randrange(0, small_lim))
    return arr
