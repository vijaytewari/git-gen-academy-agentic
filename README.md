# Atlas market and portfolio desk

Local Streamlit research dashboard for Nasdaq-100 constituents, the current top ten cryptocurrencies by market capitalization, gold and Treasury ETFs, sentiment, and portfolio scenarios.

## Run on Windows

From this directory, run `./start.ps1`, then open http://localhost:8501.

First-time setup:

```powershell
.\.python64\python.exe -m venv .venv64
.\.venv64\Scripts\python.exe -m pip install -r requirements.txt
.\start.ps1
```

The project uses a separate 64-bit Python 3.11 runtime in `.python64` because the existing 32-bit Python cannot run Streamlit's Arrow dependency. You can also create `.venv64` with an existing 64-bit Python 3.11 installation. The server binds to loopback only. Stop it with Ctrl+C.

## Data and limits

- Nasdaq's official public constituent feed supplies company names and tickers, with its source date shown. No static membership list is silently substituted.
- Yahoo Finance's public chart endpoint supplies adjusted daily prices. The current trading day may be incomplete. Quotes are not guaranteed real-time. Load all constituent prices with the watchlist button; missing prices remain blank.
- CoinGecko ranks the top ten by USD market capitalization, including stablecoins and wrapped assets. History requests are capped at 365 days to suit public API availability.
- CNN's unofficial public data endpoint supplies stock-market fear and greed. It may block automated requests. Alternative.me supplies primarily Bitcoin sentiment with attribution. Unavailable feeds display errors and source links, never invented readings.
- Data caches: prices and crypto rankings 5 minutes, sentiment 15 minutes, constituents 6 hours. Refresh clears caches. Network access is required.
- GLD, SGOV, SHY, IEF, and TLT are ETF price proxies. They are not spot gold, directly held Treasury securities, or Treasury yields.

## Portfolio methodology

Scenario weights are illustrative and editable, not tailored recommendations or an optimized portfolio. Allocation must total 100%. Broad US equities complement concentrated Nasdaq exposure. Bitcoin is the illustrative crypto sleeve; tracking the largest ten coins does not imply buying them.

Historical analysis uses two years of available adjusted closes, restricted to overlapping dates of all positive-weight assets. It models daily constant-weight rebalancing, uses 252 observations per year, and excludes costs and taxes. Annualized return is compounded, volatility is sample standard deviation times sqrt(252), and maximum drawdown is the largest loss from the previous portfolio peak. Crypto weekends are excluded from this mixed-asset analysis. Past returns are not forecasts.

Rebalancing amounts are computed against the total of entered holdings. CSV exports are available for watchlists and target allocations. The app does not connect to a brokerage or submit orders.
