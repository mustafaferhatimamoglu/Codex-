import argparse
import csv
import sqlite3
import requests
from typing import List, Dict, Tuple, Optional
import math

def fetch_trending() -> List[Dict[str, str]]:
    """Return a list of trending coins with id, name and symbol."""
    url = "https://api.coingecko.com/api/v3/search/trending"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    coins = data.get("coins", [])
    results = []
    for c in coins:
        item = c.get("item", {})
        results.append(
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "symbol": item.get("symbol"),
            }
        )
    return results


def fetch_prices(coin_id: str, days: int = 15) -> List[float]:
    """Fetch daily closing prices for the given coin id."""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days, "interval": "daily"}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        return []
    data = resp.json()
    prices = [p[1] for p in data.get("prices", [])]
    return prices


def compute_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    """Return the RSI for the given list of prices."""
    if len(prices) <= period:
        return None
    gains = []
    losses = []
    for i in range(1, period + 1):
        delta = prices[i] - prices[i - 1]
        if delta > 0:
            gains.append(delta)
        else:
            losses.append(-delta)
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def analyze_coin(coin: Dict[str, str]) -> Tuple[str, float, str]:
    """Return (symbol, rsi, signal) for a coin."""
    prices = fetch_prices(coin["id"])
    rsi = compute_rsi(prices)
    if rsi is None:
        signal = "neutral"
    elif rsi < 30:
        signal = "buy"
    elif rsi > 70:
        signal = "sell"
    else:
        signal = "neutral"
    return coin["symbol"], rsi if rsi is not None else float("nan"), signal

def save_csv(rows, path):
    """Save results to a CSV file."""
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["name", "symbol", "rsi", "signal"]
        )
        writer.writeheader()
        writer.writerows(rows)


def save_db(rows, path):
    """Save results to a SQLite database."""
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS trending (name TEXT, symbol TEXT, rsi REAL, signal TEXT)"
    )
    cur.execute("DELETE FROM trending")
    cur.executemany(
        "INSERT INTO trending (name, symbol, rsi, signal) VALUES (?, ?, ?, ?)",
        [
            (r["name"], r["symbol"], r["rsi"], r["signal"])
            for r in rows
        ],
    )
    conn.commit()
    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Fetch trending cryptocurrencies from CoinGecko"
    )
    parser.add_argument(
        "--csv", help="Path to CSV file to store the results"
    )
    parser.add_argument(
        "--db", help="Path to SQLite database to store the results"
    )
    args = parser.parse_args()

    coins = fetch_trending()[:7]
    results = []
    for coin in coins:
        symbol, rsi, signal = analyze_coin(coin)
        results.append(
            {
                "name": coin["name"],
                "symbol": symbol,
                "rsi": round(rsi, 2) if not math.isnan(rsi) else None,
                "signal": signal,
            }
        )
        rsi_display = f"{rsi:.2f}" if not math.isnan(rsi) else "n/a"
        print(f"{coin['name']} ({symbol}) - RSI {rsi_display} -> {signal}")

    if args.csv:
        save_csv(results, args.csv)
        print(f"Saved results to {args.csv}")

    if args.db:
        save_db(results, args.db)
        print(f"Saved results to {args.db}")


if __name__ == "__main__":
    main()
