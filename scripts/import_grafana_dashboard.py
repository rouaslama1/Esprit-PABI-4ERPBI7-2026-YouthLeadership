#!/usr/bin/env python3
"""Import Scout dashboard JSON into a local Grafana (admin/admin by default)."""
from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DASH = ROOT / "monitoring" / "grafana" / "dashboards" / "scout-mlops-overview.json"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--grafana-url", default="http://127.0.0.1:3000")
    p.add_argument("--user", default="admin")
    p.add_argument("--password", default="admin")
    p.add_argument("--file", type=Path, default=DEFAULT_DASH)
    args = p.parse_args()

    body = json.dumps(
        {"dashboard": json.loads(args.file.read_text(encoding="utf-8")), "overwrite": True}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{args.grafana_url.rstrip('/')}/api/dashboards/db",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Basic "
            + base64.b64encode(f"{args.user}:{args.password}".encode()).decode(),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            out = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(e.code, e.read().decode(), file=sys.stderr)
        sys.exit(1)
    print(json.dumps(out, indent=2))
    if out.get("status") == "success" and out.get("url"):
        print("\nOpen:", f"{args.grafana_url.rstrip('/')}{out['url']}")


if __name__ == "__main__":
    main()
