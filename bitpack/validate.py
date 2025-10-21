from __future__ import annotations
import random
import time
from dataclasses import dataclass
from typing import List, Dict, Any

from .factory import create
from .header import PackedData

@dataclass
class ValidationResult:
    n: int
    format: str
    samples: int
    mismatches_get: int
    mismatches_decompress: int
    t_comp_ns: int
    t_get_ns_avg: float
    t_decomp_ns: int
    payload_bits: int
    raw_bits: int
    ratio: float

def validate_access(
    kind: str,
    arr: List[int],
    samples: int = 100_000,
    seed: int = 12345,
) -> ValidationResult:
    """Vérifie l'accès direct (get) et la fidélité de la décompression, et renvoie des métriques."""
    n = len(arr)
    packer = create(kind)

    # 1) compress + temps
    t0 = time.perf_counter_ns()
    packed = packer.compress(arr)
    t1 = time.perf_counter_ns()
    t_comp_ns = t1 - t0

    # 2) get() aléatoire
    if n == 0:
        mismatches_get = 0
        avg_get_ns = 0.0
    else:
        rnd = random.Random(seed)
        M = min(n, samples)
        idxs = [rnd.randrange(0, n) for _ in range(M)]
        mismatches_get = 0
        t0 = time.perf_counter_ns()
        for i in idxs:
            if packer.get(i, packed) != arr[i]:
                mismatches_get += 1
        t1 = time.perf_counter_ns()
        avg_get_ns = (t1 - t0) / max(M, 1)

    # 3) decompress + comparaison complète
    out = [0] * n
    t0 = time.perf_counter_ns()
    packer.decompress(out, packed)
    t1 = time.perf_counter_ns()
    t_decomp_ns = t1 - t0
    mismatches_decompress = 0
    for a, b in zip(arr, out):
        if a != b:
            mismatches_decompress += 1

    # 4) tailles
    blob = packed.to_bytes()
    payload_bits = len(blob) * 8
    raw_bits = 32 * n
    ratio = (payload_bits / raw_bits) if raw_bits else 1.0

    return ValidationResult(
        n=n,
        format=kind,
        samples=min(n, samples),
        mismatches_get=mismatches_get,
        mismatches_decompress=mismatches_decompress,
        t_comp_ns=t_comp_ns,
        t_get_ns_avg=avg_get_ns,
        t_decomp_ns=t_decomp_ns,
        payload_bits=payload_bits,
        raw_bits=raw_bits,
        ratio=ratio,
    )

def render_markdown_report(v: ValidationResult) -> str:
    ok_get = (v.mismatches_get == 0)
    ok_decomp = (v.mismatches_decompress == 0)
    status = "OK ✅" if (ok_get and ok_decomp) else "FAIL ❌"
    lines = []
    lines.append("# Rapport de validation — Accès direct & fidélité\n")
    lines.append(f"- **Format** : `{v.format}`")
    lines.append(f"- **n** : {v.n}")
    lines.append(f"- **Échantillons get()** : {v.samples}")
    lines.append(f"- **Verdict** : **{status}**")
    lines.append("")
    lines.append("## Résultats")
    lines.append(f"- Mismatches `get(i)` : **{v.mismatches_get}** / {v.samples}")
    lines.append(f"- Mismatches `decompress` : **{v.mismatches_decompress}** / {v.n}")
    lines.append("")
    lines.append("## Tailles")
    lines.append(f"- Taille brute (bits) : {v.raw_bits}")
    lines.append(f"- Taille compressée (bits) : {v.payload_bits}")
    lines.append(f"- **Ratio** (comp/brut) : **{v.ratio:.4f}**")
    lines.append("")
    lines.append("## Temps (ns)")
    lines.append(f"- `T_comp` médian (1 run) : {v.t_comp_ns}")
    lines.append(f"- `T_decomp` (1 run) : {v.t_decomp_ns}")
    lines.append(f"- `T_get` moyen (ns/accès) : {v.t_get_ns_avg:.1f}")
    lines.append("")
    lines.append("## Interprétation")
    if ok_get and ok_decomp:
        lines.append("- L’accès direct `get(i)` restitue exactement les valeurs d’origine (0 erreur sur l’échantillon).")
        lines.append("- La décompression retrouve le tableau complet à l’identique (0 erreur).")
        lines.append("- Conclusion : **aucune perte d’accès ni de fidélité introduite par la compression**.")
    else:
        lines.append("- Des erreurs ont été détectées : revoir l’implémentation et/ou les paramètres.")
    lines.append("")
    return "\n".join(lines)
