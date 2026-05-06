#!/usr/bin/env python3
"""
Envoie du trafic léger en boucle pour que Prometheus/Grafana aient toujours des séries visibles.

  python scripts/pulse_metrics.py              # toutes les 3 s jusqu'à Ctrl+C
  python scripts/pulse_metrics.py --interval 2 --burst 5
  python scripts/pulse_metrics.py --heavy      # 1 s, 10 requêtes/burst (plus de points)

L'API doit tourner sur http://127.0.0.1:8010
"""
from __future__ import annotations

import argparse
import sys
import time

import httpx

API = "http://127.0.0.1:8010"
BUDGET = {
    "model_type": "budget",
    "features": {
        "flowtype": 1,
        "participants": 30,
        "budget_sub_category": 2,
        "budget_month": 6,
        "duration_days": 3,
        "season": 2024,
    },
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=float, default=3.0, help="Seconds between bursts")
    ap.add_argument("--burst", type=int, default=3, help="POST /predict per burst")
    ap.add_argument(
        "--heavy",
        action="store_true",
        help="Shortcut: interval=1s, burst=10 (denser time series for Prometheus/Grafana)",
    )
    args = ap.parse_args()
    if args.heavy:
        args.interval = 1.0
        args.burst = 10

    try:
        httpx.get(f"{API}/health", timeout=5.0).raise_for_status()
    except Exception as e:
        print(f"[!] API unreachable at {API}: {e}", file=sys.stderr)
        sys.exit(1)

    n = 0
    print(f"[*] Pulsing {API} every {args.interval}s ({args.burst} predicts/burst). Ctrl+C to stop.")
    with httpx.Client() as client:
        while True:
            client.get(f"{API}/health", timeout=10.0)
            for _ in range(args.burst):
                r = client.post(f"{API}/predict", json=BUDGET, timeout=60.0)
                n += 1
                if r.status_code != 200:
                    print(f"[!] predict status {r.status_code}", file=sys.stderr)
            if n % 30 == 0:
                print(f"    ... {n} predicts sent")
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
