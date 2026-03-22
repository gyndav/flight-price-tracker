# ✈️ flight-price-tracker

An agentic flight price monitor that fetches fares, tracks trends over time, and tells you **when to buy** — powered by the Kiwi.com API, GitHub Actions, and the Claude API.

> Not just a price scraper. An agent that reads the trend and makes a recommendation.

---

## What It Does

- Fetches current flight prices for configured routes and travel windows via the **Kiwi.com (Tequila) API**
- Persists historical prices in a local `prices.json` file (committed to the repo, version-controlled history for free)
- Sends the price history to the **Claude API** for trend analysis: rising, falling, or stable
- Outputs a plain-language **buy recommendation** directly to your inbox via GitHub Actions summary or email notification
- Runs on a **cron schedule** via GitHub Actions — zero infrastructure, zero maintenance

---

## Architecture

```
┌─────────────────────┐
│   GitHub Actions    │  ← runs on schedule (cron)
│   (cron trigger)    │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   fetch_prices.py   │  ← calls Kiwi.com Tequila API
│                     │     for each configured route
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│    prices.json      │  ← append new data points
│  (persisted store)  │     committed back to repo
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   analyze.py        │  ← sends history to Claude API
│   (Claude API)      │     asks: "should I buy now?"
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  GitHub Actions     │  ← plain-language recommendation
│  Job Summary        │     in your workflow run summary
└─────────────────────┘
```

---

## Monitored Routes

| Origin | Destination | Window | Passengers |
|--------|-------------|--------|------------|
| Montpellier (MPL) | Dubai (DXB) | May 2026 | 2 adults, 1 child |
| Lyon (LYS) | Dubai (DXB) | May 2026 | 2 adults, 1 child |
| Marseille (MRS) | Dubai (DXB) | May 2026 | 2 adults, 1 child |

Only top-tier carriers are included. Budget airlines are filtered out.

---

## Stack

- **Python 3.13** — fetch, persist, analyze
- **Kiwi.com Tequila API** — flight search and pricing
- **Claude API** (`claude-sonnet`) — trend reasoning and buy recommendation
- **GitHub Actions** — scheduler, runner, no infrastructure needed
- **prices.json** — lightweight persistent store, version-controlled history

---

## Setup

### 1. Fork or clone

```bash
git clone https://github.com/gyndav/flight-price-tracker.git
cd flight-price-tracker
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure secrets

Add the following to your GitHub repository secrets (`Settings > Secrets and variables > Actions`):

| Secret | Description |
|--------|-------------|
| `KIWI_API_KEY` | Your Kiwi.com Tequila API key |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |

### 4. Configure routes

Edit `config.yaml` to set your routes, travel window, passenger count, and carrier filters:

```yaml
routes:
  - origin: MPL
    destination: DXB
    date_from: "2026-05-01"
    date_to: "2026-05-31"
    adults: 2
    children: 1
    max_stopovers: 1
    carriers_exclude: []   # add IATA codes to exclude budget carriers

analysis:
  model: claude-sonnet-4-6
  prompt_style: concise    # concise | detailed
```

### 5. Run locally

```bash
python fetch_prices.py    # fetch and append to prices.json
python analyze.py         # send to Claude, print recommendation
```

### 6. Schedule via GitHub Actions

The workflow runs automatically on the configured cron schedule. To trigger manually:

```bash
gh workflow run price-tracker.yml
```

---

## How the Agentic Layer Works

After each fetch, `analyze.py` sends the full price history for each route to Claude with a structured prompt:

```
Given the following price history for MPL→DXB in May 2026,
identify the trend (rising / falling / stable / volatile),
flag any anomalies, and give a clear buy recommendation
with a confidence level and brief rationale.
```

Claude returns a structured response with:
- **Trend** — direction and strength
- **Anomalies** — any outlier data points
- **Recommendation** — Buy now / Wait / Watch
- **Rationale** — 2–3 sentence plain-language explanation

This is what gets written to the GitHub Actions job summary, making it readable directly from the Actions tab — no dashboard needed.

---

## Example Output

```
Route: MPL → DXB | May 10–17, 2026 | 2 adults + 1 child

Trend: Falling (-12% over 14 days)
Anomaly: Spike on 2026-03-15 (+18%) — likely inventory reduction, now corrected.

Recommendation: WAIT 🟡
Rationale: Prices are trending down and have not yet stabilized.
Based on the current trajectory, a better window is likely in the
next 7–10 days. Set a floor alert at €1,800 total.
```

---

## Project Structure

```
flight-price-tracker/
├── .github/
│   └── workflows/
│       └── price-tracker.yml   # cron schedule + job definition
├── fetch_prices.py             # Kiwi.com API client + data append
├── analyze.py                  # Claude API analysis + recommendation
├── config.yaml                 # routes, passengers, model config
├── prices.json                 # persisted price history (auto-updated)
├── requirements.txt
└── README.md
```

---

## Why This Approach

Most price trackers alert you when a price drops below a threshold.
This one does something different: it **reads the trend** and tells you whether dropping prices are likely to keep dropping, or whether you're at the floor.

The difference is the reasoning layer — which is what makes it agentic rather than just automated.

---

## Topics

`python` · `github-actions` · `claude-api` · `kiwi-api` · `agentic` · `automation` · `flight-tracking` · `price-tracker`

---

## License

MIT
