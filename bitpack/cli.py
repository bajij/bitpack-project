from __future__ import annotations
import argparse
import csv
from typing import List

from .factory import create
from .header import PackedData, KIND_CROSSING, KIND_ALIGNED, KIND_OVERFLOW
from .timing import (
    bench_pack,
    total_time_without_compression,
    total_time_with_compression,
    ns_to_s,
)

def _kind_str_to_id(s: str) -> int:
    return {"crossing": KIND_CROSSING, "aligned": KIND_ALIGNED, "overflow": KIND_OVERFLOW}[s]

def _read_u32_file(path: str) -> List[int]:
    with open(path, "rb") as f:
        data = f.read()
    if len(data) % 4 != 0:
        raise ValueError("input file length is not a multiple of 4 bytes (u32)")
    return [int.from_bytes(data[i:i+4], "little") for i in range(0, len(data), 4)]

def _write_u32_file(path: str, arr: List[int]) -> None:
    with open(path, "wb") as f:
        for x in arr:
            f.write((x & 0xFFFFFFFF).to_bytes(4, "little"))

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="bitpack")
    sub = p.add_subparsers(dest="cmd", required=True)

    # --- compress ---
    pc = sub.add_parser("compress", help="compress a u32 file")
    pc.add_argument("--input", required=True)
    pc.add_argument("--format", choices=["crossing", "aligned", "overflow"], required=True)
    pc.add_argument("--out", required=True)

    # --- get ---
    pg = sub.add_parser("get", help="read i-th value from a packed file")
    pg.add_argument("--file", required=True)
    pg.add_argument("--format", choices=["crossing", "aligned", "overflow"], required=True)
    pg.add_argument("--index", type=int, required=True)

    # --- decompress ---
    pd = sub.add_parser("decompress", help="decompress to u32 file")
    pd.add_argument("--file", required=True)
    pd.add_argument("--format", choices=["crossing", "aligned", "overflow"], required=True)
    pd.add_argument("--out", required=True)

    # --- bench ---
    pb = sub.add_parser("bench", help="benchmark compress/decompress/get and compute break-even")
    pb.add_argument("--format", choices=["crossing", "aligned", "overflow"], required=True)
    src = pb.add_mutually_exclusive_group(required=True)
    src.add_argument("--input", help="optional u32 file as input dataset (mutually exclusive with generators)")
    src.add_argument("--scenario", choices=["uniform", "skewed"], help="data generator scenario")
    pb.add_argument("--n", type=int, help="size for generator scenarios")
    pb.add_argument("--k", type=int, help="bits for uniform scenario")
    pb.add_argument("--k-small", type=int, dest="k_small", help="small bits for skewed")
    pb.add_argument("--k-large", type=int, dest="k_large", help="large bits for skewed")
    pb.add_argument("--ratio-large", type=float, dest="ratio_large", default=0.001,
                    help="ratio of large values in skewed")
    pb.add_argument("--warmups", type=int, default=3)
    pb.add_argument("--repeats", type=int, default=10)
    pb.add_argument("--get-samples", type=int, default=100000)
    pb.add_argument("--latency-ms", type=float, default=30.0, help="network latency (ms)")
    pb.add_argument("--bandwidth-mbps", type=float, default=10.0, help="network bandwidth (Mbps)")
    pb.add_argument("--csv", help="optional path to write CSV results")

    # --- validate (rapport accès direct) ---
    pv = sub.add_parser("validate", help="validate random-access & decompression fidelity; emit Markdown")
    pv.add_argument("--format", choices=["crossing", "aligned", "overflow"], required=True)
    srcv = pv.add_mutually_exclusive_group(required=True)
    srcv.add_argument("--input", help="u32 file as input dataset")
    srcv.add_argument("--scenario", choices=["uniform", "skewed"], help="data generator scenario")
    pv.add_argument("--n", type=int, help="size for generator scenarios")
    pv.add_argument("--k", type=int, help="bits for uniform")
    pv.add_argument("--k-small", type=int, dest="k_small", help="small bits for skewed")
    pv.add_argument("--k-large", type=int, dest="k_large", help="large bits for skewed")
    pv.add_argument("--ratio-large", type=float, dest="ratio_large", default=0.001)
    pv.add_argument("--samples", type=int, default=100000, help="get() samples")
    pv.add_argument("--report", required=True, help="output Markdown report path")

    args = p.parse_args(argv)

    # --- compress ---
    if args.cmd == "compress":
        arr = _read_u32_file(args.input)
        packer = create(args.format)
        packed = packer.compress(arr)
        with open(args.out, "wb") as f:
            f.write(packed.to_bytes())
        return 0

    # --- get ---
    if args.cmd == "get":
        with open(args.file, "rb") as f:
            data = f.read()
        packed = PackedData.from_bytes(data)
        expected = _kind_str_to_id(args.format)
        if packed.kind != expected:
            raise SystemExit(f"format mismatch: file contains kind={packed.kind}, CLI asked for {args.format}")
        packer = create(args.format)
        val = packer.get(args.index, packed)
        print(val)
        return 0

    # --- decompress ---
    if args.cmd == "decompress":
        with open(args.file, "rb") as f:
            data = f.read()
        packed = PackedData.from_bytes(data)
        expected = _kind_str_to_id(args.format)
        if packed.kind != expected:
            raise SystemExit(f"format mismatch: file contains kind={packed.kind}, CLI asked for {args.format}")
        packer = create(args.format)
        out = [0] * packed.n
        packer.decompress(out, packed)
        _write_u32_file(args.out, out)
        return 0

    # --- bench ---
    if args.cmd == "bench":
        # Préparer les données
        if args.input:
            arr = _read_u32_file(args.input)
            scenario_name = "file"
            scenario_params = {"path": args.input}
        else:
            if args.scenario == "uniform":
                if args.n is None or args.k is None:
                    raise SystemExit("uniform requires --n and --k")
                from .scenarios import uniform_u32
                arr = uniform_u32(args.n, args.k)
                scenario_name = "uniform"
                scenario_params = {"n": args.n, "k": args.k}
            else:
                if args.n is None or args.k_small is None or args.k_large is None:
                    raise SystemExit("skewed requires --n, --k-small and --k-large")
                from .scenarios import skewed
                arr = skewed(args.n, args.k_small, args.k_large, args.ratio_large)
                scenario_name = "skewed"
                scenario_params = {
                    "n": args.n,
                    "k_small": args.k_small,
                    "k_large": args.k_large,
                    "ratio_large": args.ratio_large,
                }

        # Bench (mesures)
        packed, stc, std, avg_get_ns = bench_pack(
            args.format, arr, warmups=args.warmups, repeats=args.repeats, get_samples=args.get_samples
        )

        # Tailles & ratio (1 seul to_bytes)
        n = len(arr)
        blob = packed.to_bytes()
        payload_bits = len(blob) * 8
        raw_bits = 32 * n
        ratio = (payload_bits / raw_bits) if raw_bits else 1.0

        # Temps de transmission
        T_no = total_time_without_compression(n, args.bandwidth_mbps, args.latency_ms)
        # compute T_yes here using payload_bits already computed
        def _bits_to_seconds(bits: int, mbps: float) -> float:
            return bits / (mbps * 1_000_000.0) if mbps > 0 else float("inf")

        T_yes = (args.latency_ms / 1000.0) + (stc.median_ns / 1e9) + _bits_to_seconds(payload_bits, args.bandwidth_mbps) + (std.median_ns / 1e9)
        gain_s = T_no - T_yes


        # Affichage console
        print("=== Bench Summary ===")
        print(f"Format           : {args.format}")
        print(f"Scenario         : {scenario_name} {scenario_params}")
        print(f"n                : {n}")
        print(f"Raw size (bits)  : {raw_bits}")
        print(f"Comp size (bits) : {payload_bits}")
        print(f"Compression ratio: {ratio:.4f}")
        print("")
        print(f"T_comp median    : {stc.median_ns} ns  ({ns_to_s(stc.median_ns)*1000:.3f} ms)")
        print(f"T_decomp median  : {std.median_ns} ns  ({ns_to_s(std.median_ns)*1000:.3f} ms)")
        print(f"T_get avg        : {avg_get_ns:.1f} ns per access")
        print("")
        print(f"Latency (ms)     : {args.latency_ms}")
        print(f"Bandwidth (Mbps) : {args.bandwidth_mbps}")
        print(f"T_no-compress    : {T_no*1000:.3f} ms")
        print(f"T_with-compress  : {T_yes*1000:.3f} ms")
        print(f"Gain             : {gain_s*1000:.3f} ms  ({'beneficial' if gain_s>0 else 'not beneficial'})")

        # CSV optionnel
        if args.csv:
            fieldnames = [
                "format", "scenario", "n", "raw_bits", "comp_bits", "ratio",
                "t_comp_ns_median", "t_decomp_ns_median", "t_get_ns_avg",
                "latency_ms", "bandwidth_mbps", "T_no_ms", "T_yes_ms", "gain_ms",
            ]
            row = {
                "format": args.format,
                "scenario": scenario_name,
                "n": n,
                "raw_bits": raw_bits,
                "comp_bits": payload_bits,
                "ratio": ratio,
                "t_comp_ns_median": stc.median_ns,
                "t_decomp_ns_median": std.median_ns,
                "t_get_ns_avg": avg_get_ns,
                "latency_ms": args.latency_ms,
                "bandwidth_mbps": args.bandwidth_mbps,
                "T_no_ms": T_no * 1000.0,
                "T_yes_ms": T_yes * 1000.0,
                "gain_ms": gain_s * 1000.0,
            }
            with open(args.csv, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(row)
            print(f"\nCSV écrit : {args.csv}")
        return 0

    # --- validate ---
    if args.cmd == "validate":
        # charger ou générer les données
        if args.input:
            arr = _read_u32_file(args.input)
        else:
            if args.scenario == "uniform":
                if args.n is None or args.k is None:
                    raise SystemExit("uniform requires --n and --k")
                from .scenarios import uniform_u32
                arr = uniform_u32(args.n, args.k)
            else:
                if args.n is None or args.k_small is None or args.k_large is None:
                    raise SystemExit("skewed requires --n, --k-small and --k-large")
                from .scenarios import skewed
                arr = skewed(args.n, args.k_small, args.k_large, args.ratio_large)

        # exécuter la validation et écrire le rapport
        from .validate import validate_access, render_markdown_report
        res = validate_access(args.format, arr, samples=args.samples)
        md = render_markdown_report(res)
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Validation report written to: {args.report}")
        return 0

    return 1

if __name__ == "__main__":
    raise SystemExit(main())
