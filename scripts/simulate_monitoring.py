#!/usr/bin/env python3
"""
Simulation scenarios for Week S13 (mandatory production-like incidents).

  python scripts/simulate_monitoring.py traffic   # high traffic → latency / load
  python scripts/simulate_monitoring.py errors    # API / validation errors → error spikes
  python scripts/simulate_monitoring.py drift     # model drift header → confidence / health
  python scripts/simulate_monitoring.py mixed     # budget + classify (plus de séries model_type)
  python scripts/simulate_monitoring.py stress    # grosse charge + erreurs + drift (démo riche)
  python scripts/simulate_monitoring.py all       # traffic + errors + drift (ordre simple)

  Options (traffic / stress / all) :
  python scripts/simulate_monitoring.py traffic --workers 32 --total 512

Requires API: http://127.0.0.1:8010 — then watch Grafana, Prometheus → Alerts, logs/scout_api.log
"""
from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

API = "http://127.0.0.1:8010"

BUDGET_BODY = {
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

CLASSIFY_BODY = {
    "model_type": "classify",
    "features": {
        "members_count": 30,
        "leaders_count": 3,
        "leaders_to_members_ratio": 0.10,
        "activities_per_member": 2.5,
        "female_ratio": 0.40,
        "activity_count": 10,
    },
}


def one_predict(client: httpx.Client, body: dict, headers: dict | None = None) -> int:
    r = client.post(f"{API}/predict", json=body, headers=headers or {}, timeout=60.0)
    return r.status_code


def scenario_mixed(workers: int = 20, total: int = 200) -> None:
    """Interleave budget and classify predictions so both model_type labels move."""
    print(f"[*] Mixed traffic: {total} predicts ({workers} workers, budget + classify)")
    bodies = [BUDGET_BODY, CLASSIFY_BODY]
    ok = 0
    with httpx.Client() as client:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [
                ex.submit(one_predict, client, bodies[i % 2])
                for i in range(total)
            ]
            for f in as_completed(futs):
                if f.result() == 200:
                    ok += 1
    print(f"    done: {ok}/{total} HTTP 200")


def scenario_traffic(workers: int = 16, total: int = 256) -> None:
    print(f"[*] High traffic: {total} budget predictions ({workers} workers)")
    ok = 0
    with httpx.Client() as client:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(one_predict, client, BUDGET_BODY) for _ in range(total)]
            for f in as_completed(futs):
                if f.result() == 200:
                    ok += 1
    print(f"    done: {ok}/{total} HTTP 200")


def scenario_errors(count: int = 40) -> None:
    print(f"[*] API / validation errors: {count} empty feature calls")
    bad = {"model_type": "budget", "features": {}}
    with httpx.Client() as client:
        for _ in range(count):
            one_predict(client, bad)
    print("    done (expect HTTP 400)")


def scenario_stress(workers: int, traffic_total: int) -> None:
    """Heavy demo: two traffic waves, errors, drift — fills many counters quickly."""
    print("[*] STRESS: wave 1 traffic")
    scenario_traffic(workers=workers, total=traffic_total)
    time.sleep(1.5)
    print("[*] STRESS: mixed models")
    scenario_mixed(workers=max(8, workers // 2), total=min(300, traffic_total))
    time.sleep(1.0)
    scenario_errors(count=60)
    time.sleep(0.5)
    scenario_drift(count=40)
    time.sleep(1.0)
    print("[*] STRESS: wave 2 traffic")
    scenario_traffic(workers=workers, total=traffic_total)
    print("    stress done — check Prometheus Graph + /alerts + logs/scout_api.log")


def scenario_drift(count: int = 25) -> None:
    print(f"[*] Model drift simulation: {count} classify calls with X-Simulate-Drift: 1")
    h = {"X-Simulate-Drift": "1"}
    with httpx.Client() as client:
        for _ in range(count):
            one_predict(client, CLASSIFY_BODY, headers=h)
            time.sleep(0.02)
    print("    done — check scout_drift_detected and logs")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "scenario",
        choices=["traffic", "errors", "drift", "mixed", "stress", "all"],
        help="Which simulation to run",
    )
    p.add_argument(
        "--workers",
        type=int,
        default=16,
        help="Parallel workers for traffic/stress/all (default 16)",
    )
    p.add_argument(
        "--total",
        type=int,
        default=256,
        help="Total /predict calls for traffic wave (default 256)",
    )
    args = p.parse_args()
    try:
        r = httpx.get(f"{API}/health", timeout=5.0)
        r.raise_for_status()
    except Exception as e:
        print(f"[!] API not reachable at {API}: {e}", file=sys.stderr)
        sys.exit(1)

    w, t = max(1, args.workers), max(1, args.total)

    if args.scenario == "traffic":
        scenario_traffic(workers=w, total=t)
    elif args.scenario == "errors":
        scenario_errors()
    elif args.scenario == "drift":
        scenario_drift()
    elif args.scenario == "mixed":
        scenario_mixed(workers=max(w, 8), total=t)
    elif args.scenario == "stress":
        scenario_stress(workers=max(w, 20), traffic_total=max(t, 320))
    else:
        scenario_traffic(workers=w, total=t)
        scenario_errors()
        scenario_drift()


if __name__ == "__main__":
    main()
