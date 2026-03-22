#!/usr/bin/env python3
"""
Send price history to Claude API for trend analysis and buy recommendation.
Outputs to stdout (captured as GitHub Actions job summary).
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

import anthropic
import yaml


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_prices(path: str = "prices.json") -> list:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def group_by_route(prices: list) -> dict:
    grouped = defaultdict(list)
    for entry in prices:
        key = f"{entry['origin']}→{entry['destination']} ({entry['date_from']} – {entry['date_to']})"
        grouped[key].append(entry)
    return dict(grouped)


def build_prompt(route_key: str, entries: list, style: str = "concise") -> str:
    history_lines = []
    for e in sorted(entries, key=lambda x: x["fetched_at"]):
        fetched = datetime.fromisoformat(e["fetched_at"]).strftime("%Y-%m-%d %H:%M UTC")
        history_lines.append(
            f"  - {fetched}: {e['price']} {e['currency']} "
            f"(airline: {e['airline']}, duration: {e['duration_hours']}h, stopovers: {e['stopovers']})"
        )

    history_str = "\n".join(history_lines)
    passengers = entries[-1]["passengers"]
    pax_str = f"{passengers['adults']} adult(s), {passengers['children']} child(ren)"

    detail_instruction = (
        "Be concise: 3–5 sentences maximum per route."
        if style == "concise"
        else "Be thorough: include trend strength, confidence level, and specific timing advice."
    )

    return f"""You are an expert travel price analyst. Analyze the following flight price history and provide a clear, actionable recommendation.

Route: {route_key}
Passengers: {pax_str}

Price history (chronological):
{history_str}

Tasks:
1. Identify the price trend: rising / falling / stable / volatile
2. Flag any anomalies or outliers
3. Give a buy recommendation: BUY NOW / WAIT / WATCH
4. Provide a confidence level: HIGH / MEDIUM / LOW
5. Give a brief rationale explaining your recommendation

{detail_instruction}

Format your response as:
TREND: [trend]
ANOMALY: [any anomaly, or "None"]
RECOMMENDATION: [BUY NOW / WAIT / WATCH]
CONFIDENCE: [HIGH / MEDIUM / LOW]
RATIONALE: [your explanation]
"""


def analyze_route(client: anthropic.Anthropic, route_key: str, entries: list, config: dict) -> str:
    model = config.get("analysis", {}).get("model", "claude-sonnet-4-6")
    style = config.get("analysis", {}).get("prompt_style", "concise")

    prompt = build_prompt(route_key, entries, style)

    message = client.messages.create(
        model=model,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text.strip()


def format_summary(route_key: str, entries: list, analysis: str) -> str:
    latest = sorted(entries, key=lambda x: x["fetched_at"])[-1]
    data_points = len(entries)

    lines = [
        f"## ✈️ {route_key}",
        f"",
        f"**Latest price:** {latest['price']} {latest['currency']} "
        f"({latest['airline']}, {latest['duration_hours']}h) — "
        f"as of {datetime.fromisoformat(latest['fetched_at']).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Data points:** {data_points}",
        f"",
        "**Analysis:**",
        f"```",
        analysis,
        f"```",
        f"",
        f"[🔗 Book now]({latest['deep_link']})" if latest.get("deep_link") else "",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def write_github_summary(content: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a") as f:
            f.write(content)
    else:
        print(content)


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    config = load_config()
    prices = load_prices()

    if not prices:
        print("No price data found. Run fetch_prices.py first.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    grouped = group_by_route(prices)

    header = f"# ✈️ Flight Price Analysis\n\n_Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_\n\n---\n\n"
    write_github_summary(header)

    print(f"Analyzing {len(grouped)} route(s)...")

    for route_key, entries in grouped.items():
        print(f"  {route_key} ({len(entries)} data points)...")
        analysis = analyze_route(client, route_key, entries, config)
        summary = format_summary(route_key, entries, analysis)
        write_github_summary(summary)
        print(f"    ✓ Done")

    print("\nAnalysis complete. Check the GitHub Actions job summary for results.")


if __name__ == "__main__":
    main()
