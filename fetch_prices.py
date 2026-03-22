#!/usr/bin/env python3
"""
Fetch flight prices from Kiwi.com Tequila API and append to prices.json.
"""

import json
import os
import sys
from datetime import datetime, timezone

import requests
import yaml

TEQUILA_API_BASE = "https://api.tequila.kiwi.com/v2/search"


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_prices(path: str = "prices.json") -> list:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def save_prices(data: list, path: str = "prices.json") -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def fetch_route(route: dict, api_key: str) -> dict | None:
    params = {
        "fly_from": route["origin"],
        "fly_to": route["destination"],
        "date_from": route["date_from"],
        "date_to": route["date_to"],
        "adults": route["adults"],
        "children": route.get("children", 0),
        "max_stopovers": route.get("max_stopovers", 1),
        "curr": route.get("currency", "EUR"),
        "sort": "price",
        "limit": 5,
    }

    carriers_exclude = route.get("carriers_exclude", [])
    if carriers_exclude:
        params["select_airlines"] = ",".join(carriers_exclude)
        params["select_airlines_exclude"] = "true"

    headers = {"apikey": api_key}

    try:
        response = requests.get(TEQUILA_API_BASE, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"  ERROR fetching {route['origin']}→{route['destination']}: {e}", file=sys.stderr)
        return None

    flights = data.get("data", [])
    if not flights:
        print(f"  No flights found for {route['origin']}→{route['destination']}")
        return None

    best = flights[0]
    return {
        "origin": route["origin"],
        "destination": route["destination"],
        "date_from": route["date_from"],
        "date_to": route["date_to"],
        "passengers": {"adults": route["adults"], "children": route.get("children", 0)},
        "price": best["price"],
        "currency": route.get("currency", "EUR"),
        "airline": best.get("airlines", ["unknown"])[0],
        "duration_hours": round(best.get("duration", {}).get("total", 0) / 3600, 1),
        "stopovers": best.get("route", [{}])[-1].get("stop", 0),
        "deep_link": best.get("deep_link", ""),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    api_key = os.environ.get("KIWI_API_KEY")
    if not api_key:
        print("ERROR: KIWI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    config = load_config()
    prices = load_prices()

    print(f"Fetching prices for {len(config['routes'])} route(s)...")

    new_entries = 0
    for route in config["routes"]:
        label = f"{route['origin']}→{route['destination']}"
        print(f"  {label} ({route['date_from']} – {route['date_to']})...")

        result = fetch_route(route, api_key)
        if result:
            prices.append(result)
            new_entries += 1
            print(f"    ✓ Best price: {result['price']} {result['currency']} ({result['airline']})")

    save_prices(prices)
    print(f"\nDone. {new_entries} new entries appended to prices.json ({len(prices)} total).")


if __name__ == "__main__":
    main()
