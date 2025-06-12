import argparse
import csv
import sqlite3
import requests
from typing import List, Tuple
from datetime import datetime

COIN_ID = "blockasset"


def fetch_coin_details() -> dict:
    """Fetch detailed information about Blockasset."""
    url = f"https://api.coingecko.com/api/v3/coins/{COIN_ID}"
    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "true",
        "developer_data": "true",
        "sparkline": "false",
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_price_history(days: int = 365) -> List[Tuple[int, float]]:
    """Return list of (timestamp, price) for the given number of days.

    CoinGecko sometimes returns a duplicate entry for the most recent day.
    Deduplicate by keeping the last price for each date.
    """
    url = f"https://api.coingecko.com/api/v3/coins/{COIN_ID}/market_chart"
    params = {"vs_currency": "usd", "days": days, "interval": "daily"}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    per_date = {}
    for ts, price in data.get("prices", []):
        date = datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d")
        per_date[date] = (int(ts), float(price))

    rows = [per_date[d] for d in sorted(per_date)]
    return rows


def save_csv(rows: List[Tuple[int, float]], path: str) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "price_usd"])
        for ts, price in rows:
            date = datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d")
            writer.writerow([date, price])


def save_db(rows: List[Tuple[int, float]], path: str) -> None:
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS prices (date TEXT, price REAL)")
    cur.execute("DELETE FROM prices")
    cur.executemany(
        "INSERT INTO prices (date, price) VALUES (?, ?)",
        [
            (datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d"), price)
            for ts, price in rows
        ],
    )
    conn.commit()
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Blockasset price history")
    parser.add_argument("--csv", help="Path to CSV file to store price history")
    parser.add_argument("--db", help="Path to SQLite DB to store price history")
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Number of days of historical data to fetch (default: 365)",
    )
    args = parser.parse_args()

    print("Fetching coin details...")
    info = fetch_coin_details()
    name = info.get("name")
    symbol = info.get("symbol")
    current = info.get("market_data", {}).get("current_price", {}).get("usd")
    print(f"{name} ({symbol}) current price: {current} USD")

    print("Fetching historical prices...")
    prices = fetch_price_history(days=args.days)
    print(f"Fetched {len(prices)} daily prices")
    if prices:
        first_date = datetime.utcfromtimestamp(prices[0][0] / 1000).strftime("%Y-%m-%d")
        last_date = datetime.utcfromtimestamp(prices[-1][0] / 1000).strftime("%Y-%m-%d")
        print(f"Range: {first_date} to {last_date}")

    if args.csv:
        save_csv(prices, args.csv)
        print(f"Saved CSV to {args.csv}")

    if args.db:
        save_db(prices, args.db)
        print(f"Saved DB to {args.db}")


if __name__ == "__main__":
    main()
