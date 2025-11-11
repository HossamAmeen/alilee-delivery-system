#!/usr/bin/env python3
"""
Simple generator for user transactions (deposits / withdrawals) via the API.

Edit the constants below and run the script. No CLI args.

Defaults:
  - BASE_URL: https://alilee.hossamstore.store
  - DRY_RUN: True (won't POST unless you change to False)

Endpoints used (based on project routers):
  - POST /api/transactions/user/  (create transaction)
  - GET  /api/traders/            (to list trader IDs)
  - POST /api/users/login/        (to obtain JWT if EMAIL/PASSWORD used)

Install requirements: pip install requests
"""
import random
import sys
from decimal import Decimal

import requests

# --- Configuration (edit these) ---
BASE_URL = "https://alilee.hossamstore.store"

# Authentication: either set TOKEN or set EMAIL and PASSWORD
TOKEN = None
EMAIL = None
PASSWORD = None

# How many transactions to create
COUNT = 10

# Amount range
MIN_AMOUNT = 1.0
MAX_AMOUNT = 200.0

# Default transaction types to pick from
TRANSACTION_TYPES = ["deposit", "withdraw"]

# If True, the script will only print prepared payloads and won't POST
DRY_RUN = True
# ----------------------------------


def get_token_by_credentials(session, base_url, email, password):
    url = f"{base_url}/api/users/login/"
    resp = session.post(url, json={"email": email, "password": password})
    if resp.status_code not in (200, 201):
        print(f"Failed to obtain token via {url}: {resp.status_code} {resp.text}")
        return None
    data = resp.json()
    if "access" in data:
        return data["access"]
    for key in ("token", "access_token", "accessToken"):
        if key in data:
            return data[key]
    print("Token not found in login response; keys:", list(data.keys()))
    return None


def fetch_all(session, url):
    resp = session.get(url)
    resp.raise_for_status()
    data = resp.json()
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
    if isinstance(data, list):
        return data
    raise RuntimeError(f"Unexpected response format from {url}: {type(data)}")


def main():
    base_url = BASE_URL.rstrip("/")
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})

    token = TOKEN
    if not token and EMAIL and PASSWORD:
        token = get_token_by_credentials(session, base_url, EMAIL, PASSWORD)
    if token:
        session.headers.update({"Authorization": f"Bearer {token}"})
    else:
        print("No TOKEN and no EMAIL/PASSWORD set. Edit the script to add credentials or a token.")
        sys.exit(1)

    # fetch traders to get user_account IDs
    traders_url = f"{base_url}/api/traders/"
    print(f"Fetching traders from {traders_url} ...")
    traders = fetch_all(session, traders_url)
    trader_ids = [t.get("id") for t in traders if t.get("id") is not None]
    if not trader_ids:
        print("No traders found. Aborting.")
        sys.exit(1)

    tx_url = f"{base_url}/api/transactions/user/"
    print(f"Preparing up to {COUNT} unique transactions. Dry run={DRY_RUN}")

    creations = []
    tries = 0
    max_tries = COUNT * 10
    while len(creations) < COUNT and tries < max_tries:
        tries += 1
        trader = random.choice(trader_ids)
        tx_type = random.choice(TRANSACTION_TYPES)
        amount = round(random.uniform(MIN_AMOUNT, MAX_AMOUNT), 2)
        payload = {"user_account": trader, "transaction_type": tx_type, "amount": str(Decimal(amount).quantize(Decimal("0.01")))}
        # avoid exact duplicate payloads in this run
        key = (trader, tx_type)
        if key in [(c["user_account"], c["transaction_type"]) for c in creations]:
            continue
        creations.append(payload)

    print(f"Prepared {len(creations)} transactions.")

    results = []
    for payload in creations:
        if DRY_RUN:
            print("DRY", payload)
            results.append({"status": "dry", "payload": payload})
            continue
        r = session.post(tx_url, json=payload)
        if r.status_code in (200, 201):
            print(f"Created: {r.status_code} -> {r.json()}")
            results.append({"status": "created", "data": r.json()})
        else:
            print(f"Failed to create {payload}: {r.status_code} {r.text}")
            results.append({"status": "failed", "code": r.status_code, "text": r.text, "payload": payload})

    print("Done. Summary:")
    created = [r for r in results if r.get("status") == "created"]
    failed = [r for r in results if r.get("status") == "failed"]
    dry = [r for r in results if r.get("status") == "dry"]
    print(f"  created: {len(created)}")
    print(f"  failed:  {len(failed)}")
    print(f"  dry:     {len(dry)}")


if __name__ == "__main__":
    main()
