#!/usr/bin/env python3
"""
Milestone 4 – A/B Statistical Analysis
Reads accumulated /ab-report output (or synthetic data) and runs a
two-proportion z-test + bootstrap CI to produce a printable report.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import urllib.request


def two_prop_ztest(h_c: int, n_c: int, h_t: int, n_t: int) -> tuple[float, float]:
    p_c = h_c / n_c
    p_t = h_t / n_t
    delta = p_t - p_c
    p_pool = (h_c + h_t) / (n_c + n_t)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_c + 1 / n_t))
    z = delta / se if se > 0 else 0.0
    p_val = 2 * (1 - _norm_cdf(abs(z)))
    return z, p_val


def bootstrap_ci(h_c: int, n_c: int, h_t: int, n_t: int,
                 n_boot: int = 10_000, alpha: float = 0.05,
                 seed: int = 42) -> tuple[float, float]:
    rng = random.Random(seed)
    p_c = h_c / n_c
    p_t = h_t / n_t
    deltas = []
    for _ in range(n_boot):
        b_c = sum(rng.random() < p_c for _ in range(n_c)) / n_c
        b_t = sum(rng.random() < p_t for _ in range(n_t)) / n_t
        deltas.append(b_t - b_c)
    deltas.sort()
    lo = deltas[int(alpha / 2 * n_boot)]
    hi = deltas[int((1 - alpha / 2) * n_boot)]
    return lo, hi


def _norm_cdf(z: float) -> float:
    return (1 + math.erf(z / math.sqrt(2))) / 2


def fetch_live(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser(description="A/B analysis for recommender API")
    ap.add_argument("--url", default=None, help="Base URL of the live API (fetches /ab-report)")
    ap.add_argument("--control-hits", type=int, default=420)
    ap.add_argument("--control-requests", type=int, default=600)
    ap.add_argument("--treatment-hits", type=int, default=470)
    ap.add_argument("--treatment-requests", type=int, default=600)
    args = ap.parse_args()

    if args.url:
        data = fetch_live(args.url.rstrip("/") + "/ab-report")
        h_c = data["control"]["hits"]
        n_c = data["control"]["requests"]
        h_t = data["treatment"]["hits"]
        n_t = data["treatment"]["requests"]
        print(f"Fetched live data from {args.url}/ab-report")
    else:
        h_c, n_c = args.control_hits, args.control_requests
        h_t, n_t = args.treatment_hits, args.treatment_requests
        print("Using supplied / default data (no --url provided)")

    p_c = h_c / n_c
    p_t = h_t / n_t
    delta = p_t - p_c

    z, pval = two_prop_ztest(h_c, n_c, h_t, n_t)
    ci_lo, ci_hi = bootstrap_ci(h_c, n_c, h_t, n_t)

    sig = pval < 0.05
    decision = "SHIP TREATMENT (ALS)" if sig and delta > 0 else "HOLD – no significant improvement"

    print()
    print("=" * 55)
    print("  A/B EXPERIMENT REPORT  –  Recommender API (M4)")
    print("=" * 55)
    print(f"  Control   (item_item): hits={h_c}/{n_c}  rate={p_c:.4f}")
    print(f"  Treatment (ALS):       hits={h_t}/{n_t}  rate={p_t:.4f}")
    print(f"  Δ hit-rate : {delta:+.4f}")
    print(f"  Z-score    : {z:.3f}")
    print(f"  p-value    : {pval:.4f}  ({'significant' if sig else 'not significant'} @ α=0.05)")
    print(f"  Bootstrap 95% CI on Δ: [{ci_lo:.4f}, {ci_hi:.4f}]")
    print(f"  Decision   : {decision}")
    print("=" * 55)

    # Emit JSON for PDF generation
    with open("report/ab_results.json", "w") as f:
        json.dump({
            "control":   {"hits": h_c, "requests": n_c, "hit_rate": round(p_c, 4)},
            "treatment": {"hits": h_t, "requests": n_t, "hit_rate": round(p_t, 4)},
            "delta": round(delta, 4),
            "z_score": round(z, 3),
            "p_value": round(pval, 4),
            "ci_95": [round(ci_lo, 4), round(ci_hi, 4)],
            "decision": decision,
        }, f, indent=2)
    print("  JSON saved to report/ab_results.json")


if __name__ == "__main__":
    main()
