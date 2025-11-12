#!/usr/bin/env python3
"""
Generate trader-delivery-zone records by calling the API on the given base URL.

Usage examples:
  # using an existing JWT access token
  python scripts/generate_trader_delivery_zones.py --base-url https://alilee.hossamstore.store --token <JWT_ACCESS_TOKEN> --count 20

  # obtain token using email/password (will call /api/users/login/)
  python scripts/generate_trader_delivery_zones.py --base-url https://alilee.hossamstore.store --email you@example.com --password secret --count 50

The script will fetch available traders from /api/traders/ and delivery zones from
/api/geo/delivery-zones/ and then POST combinations to /api/pricing/trader-delivery-zones/.

Notes:
 - The API endpoints are assumed to match the Django project routers (see repo).
 - Authentication uses the Authorization: Bearer <token> header when --token is provided.
 - If --email/--password are provided and token retrieval fails, the script will abort.
"""
import argparse
import random
import sys
from decimal import Decimal

import requests


def parse_args():
    p = argparse.ArgumentParser(description="Generate trader-delivery-zones via API")
    p.add_argument(
        "--base-url",
        default="https://alilee.hossamstore.store",
        help="Base URL of the API (no trailing slash) or with https://",
    )
    p.add_argument(
        "--token", help="JWT access token to use for Authorization: Bearer <token>"
    )
    p.add_argument("--email", help="Email to obtain token via /api/users/login/")
    p.add_argument("--password", help="Password to obtain token via /api/users/login/")
    p.add_argument("--count", type=int, default=10, help="Number of entries to create")
    p.add_argument(
        "--min-price",
        type=float,
        default=5.0,
        help="Minimum price for generated entries",
    )
    p.add_argument(
        "--max-price",
        type=float,
        default=50.0,
        help="Maximum price for generated entries",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually POST, just print what would be created",
    )
    return p.parse_args()


def get_token_by_credentials(session, base_url, email, password):
    url = f"{base_url}/api/users/login/"
    resp = session.post(url, json={"email": email, "password": password})
    if resp.status_code not in (200, 201):
        return None
    data = resp.json()
    # common response from SimpleJWT: {"access": "..", "refresh": ".."}
    if "access" in data:
        return data["access"]
    # some projects might return token under 'token' or 'access_token'
    for key in ("token", "access_token", "accessToken"):
        if key in data:
            return data[key]
    return None


def fetch_all(session, url):
    resp = session.get(url)
    resp.raise_for_status()
    data = resp.json()
    # DRF paginated responses usually contain 'results'
    if isinstance(data, dict) and "results" in data:
        results = list(data["results"])
        next_url = data.get("next")
        while next_url:
            r = session.get(next_url)
            r.raise_for_status()
            chunk = r.json()
            results.extend(chunk.get("results", []))
            next_url = chunk.get("next")
        return results
    # if it's a list already
    if isinstance(data, list):
        return data
    # Unknown format
    raise RuntimeError(f"Unexpected response format from {url}: {type(data)}")


def main():
    args = parse_args()
    base_url = args.base_url.rstrip("/")

    session = requests.Session()
    session.headers.update({"Accept": "application/json"})

    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxODE2ODU0OTYxLCJpYXQiOjE3NjI4NTQ5NjEsImp0aSI6IjViYmRmZGRiOWIzNDRmZGZhMjkyNWZkYjQ1ZjdkMTU3IiwidXNlcl9pZCI6IjEifQ.xs3CL4n0WwDJrmQGugyKqWVtSRxTyOPZjRRieX3cjeE"
    session.headers.update({"Authorization": f"Bearer {token}"})

    # fetch traders
    traders_url = f"{base_url}/api/traders/"
    traders = fetch_all(session, traders_url)
    trader_ids = [t.get("id") for t in traders if t.get("id") is not None]
    if not trader_ids:
        sys.exit(1)

    # fetch delivery zones
    dz_url = f"{base_url}/api/geo/delivery-zones/"
    zones = fetch_all(session, dz_url)
    zone_ids = [z.get("id") for z in zones if z.get("id") is not None]
    if not zone_ids:
        sys.exit(1)

    # fetch existing combos to avoid duplicates
    existing_url = f"{base_url}/api/pricing/trader-delivery-zones/"
    existing = fetch_all(session, existing_url)
    existing_pairs = set((e.get("trader"), e.get("delivery_zone")) for e in existing)

    creations = []
    tries = 0
    max_tries = args.count * 10
    while len(creations) < args.count and tries < max_tries:
        tries += 1
        trader = random.choice(trader_ids)
        zone = random.choice(zone_ids)
        pair = (trader, zone)
        if pair in existing_pairs or pair in creations:
            continue
        price = round(random.uniform(args.min_price, args.max_price), 2)
        creations.append((trader, zone, str(Decimal(price).quantize(Decimal("0.01")))))

    if len(creations) < args.count:
        pass

    results = []
    for trader, zone, price in creations:
        payload = {"price": price, "trader": trader, "delivery_zone": zone}
        if args.dry_run:
            results.append({"status": "dry", "payload": payload})
            continue
        r = session.post(existing_url, json=payload)
        if r.status_code in (200, 201):
            results.append({"status": "created", "data": r.json()})
        else:
            results.append(
                {
                    "status": "failed",
                    "code": r.status_code,
                    "text": r.text,
                    "payload": payload,
                }
            )


if __name__ == "__main__":
    main()
