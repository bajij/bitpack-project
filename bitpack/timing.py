from __future__ import annotations
import gc
import statistics
import time
import random
from dataclasses import dataclass
from typing import Callable, Iterable, List, Tuple

from .header import PackedData
from .factory import create

@dataclass
class Stats:
    samples_ns: List[int]
    median_ns: int
    mean_ns: float
    stdev_ns: float

def _time_repeated(fn: Callable[[], None], warmups: int = 3, repeats: int = 10, disable_gc: bool = True) -> Stats:
    if disable_gc:
        gc_was_enabled = gc.isenabled()
        gc.disable()
    try:
        for _ in range(max(warmups, 0)):
            fn()
        samples: List[int] = []
        for _ in range(max(repeats, 1)):
            t0 = time.perf_counter_ns()
            fn()
            t1 = time.perf_counter_ns()
            samples.append(t1 - t0)
        med = int(statistics.median(samples))
        mean = float(statistics.fmean(samples))
        stdev = float(statistics.pstdev(samples)) if len(samples) > 1 else 0.0
        return Stats(samples, med, mean, stdev)
    finally:
        if disable_gc and gc_was_enabled:
            gc.enable()

def ns_to_s(ns: int | float) -> float:
    return float(ns) / 1_000_000_000.0

def bits_to_seconds(bits: int, bandwidth_mbps: float) -> float:
    """Retourne le temps de transmission en secondes pour `bits` à `bandwidth_mbps` (Mbps)."""
    if bandwidth_mbps <= 0:
        return float("inf")
    bps = bandwidth_mbps * 1_000_000.0
    return bits / bps

def total_time_without_compression(n: int, bandwidth_mbps: float, latency_ms: float) -> float:
    """T_no = t + S_raw/B ; S_raw = 32*n bits."""
    S_raw_bits = 32 * n
    return (latency_ms / 1000.0) + bits_to_seconds(S_raw_bits, bandwidth_mbps)

def total_time_with_compression(
    packed: PackedData,
    t_comp_ns: int,
    t_decomp_ns: int,
    bandwidth_mbps: float,
    latency_ms: float,
) -> float:
    """T_yes = t + T_comp + S_comp/B + T_decomp ; S_comp = taille totale du payload compressé (header + mots)."""
    payload_bits = len(packed.to_bytes()) * 8
    return (latency_ms / 1000.0) + ns_to_s(t_comp_ns) + bits_to_seconds(payload_bits, bandwidth_mbps) + ns_to_s(t_decomp_ns)

def compression_ratio(packed: PackedData, n: int) -> float:
    S_raw_bits = 32 * n
    S_comp_bits = len(packed.to_bytes()) * 8
    return S_comp_bits / S_raw_bits if S_raw_bits > 0 else 1.0

def bench_pack(
    kind: str,
    arr: List[int],
    warmups: int = 3,
    repeats: int = 10,
    get_samples: int | None = None,
    seed: int = 12345,
):
    """
    Mesure :
      - T_comp (ns) sur `repeats` répétitions (median/mean/stdev),
      - T_decomp (ns),
      - T_get_rand (ns par accès moyen) sur M accès aléatoires.
    Retourne (packed_ref, stats_comp, stats_decomp, avg_get_ns).
    """
    packer = create(kind)

    # 1) Mesurer compress (repeats fois)
    def _do_compress() -> None:
        _ = packer.compress(arr)
    stats_comp = _time_repeated(_do_compress, warmups=warmups, repeats=repeats, disable_gc=True)

    # 2) Obtenir un PackedData de référence (hors mesures) pour chronométrer get & decompress
    packed_ref = packer.compress(arr)

    # 3) Mesurer decompress
    out = [0] * len(arr)
    def _do_decompress() -> None:
        packer.decompress(out, packed_ref)
    stats_decomp = _time_repeated(_do_decompress, warmups=warmups, repeats=repeats, disable_gc=True)

    # 4) Mesurer get(i) aléatoire, M accès
    n = len(arr)
    M = min(n, 100_000) if get_samples is None else min(n, get_samples)
    if M == 0:
        avg_get_ns = 0.0
    else:
        rnd = random.Random(seed)
        idxs = [rnd.randrange(0, n) for _ in range(M)]
        t0 = time.perf_counter_ns()
        s = 0
        for i in idxs:
            s ^= packer.get(i, packed_ref)  # contrer "optimisation" du CPU (trivial en Python, mais on xore)
        t1 = time.perf_counter_ns()
        # on "utilise" s pour éviter qu'il ne soit optimisé (il ne le sera pas en CPython, mais par hygiène)
        if s == -1:
            print("", end="")  # no-op
        avg_get_ns = (t1 - t0) / M

    return packed_ref, stats_comp, stats_decomp, avg_get_ns
