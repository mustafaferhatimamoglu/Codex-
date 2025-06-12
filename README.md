# Codex-

This repo includes Python scripts with small demos.

## Scripts

- `hello.py` prints "Hello, world!".
- `crypto_trending.py` lists trending cryptocurrencies from the public CoinGecko API, calculates a basic RSI indicator and can store the results in a CSV file or SQLite database.
- `blockasset_data.py` downloads price history for the Blockasset coin and can save the data to CSV or SQLite.

### Running the scripts

To run the hello script:

```bash
python3 hello.py
```

To fetch trending coins (requires `requests`):

```bash
pip install requests
python3 crypto_trending.py
```

The script prints each trending coin along with a 14-day RSI and a simple trading signal (``buy``, ``sell`` or ``neutral``).

To store the results in a CSV file:

```bash
python3 crypto_trending.py --csv trending.csv
```

To store the results in a SQLite database:

```bash
python3 crypto_trending.py --db trending.db
```

To fetch all Blockasset price data and store it in CSV and SQLite files:

The market data endpoint occasionally returns a duplicate entry for the
current day. The script automatically removes duplicates so the CSV and
database contain one row per day.

```bash
python3 blockasset_data.py --csv blockasset.csv --db blockasset.db
```
