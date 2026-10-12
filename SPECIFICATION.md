# Atlas Market and Portfolio Dashboard Specification

## Purpose and original request

Build a one-stop website resembling a trading platform where the user can track all Nasdaq-100 stocks and the top ten cryptocurrencies, consider gold and Treasuries when planning a portfolio, view financial-market and crypto fear-and-greed indices, and inspect the trend of a selected stock. Implement the website with Streamlit and run it locally for viewing.

The requested “perfect portfolio” is interpreted as an adjustable planning tool with transparent risk analysis. The application must not promise an optimal allocation or guaranteed returns. Personalized recommendations would require the user's investment horizon, goals, liquidity needs, financial circumstances, and risk tolerance.

## Scope

The application is a single-user research and portfolio-planning dashboard. It provides market monitoring, historical charts, sentiment, illustrative allocations, rebalancing calculations, and downloadable results. All monetary values use USD.

Brokerage integration, order execution, account authentication, public hosting, persistent holdings storage, real-time streaming quotes, tax optimization, and automated portfolio optimization are outside the current scope.

## Functional requirements

### Market overview

- Display summary prices and changes for Nasdaq-100 exposure, Bitcoin, gold exposure, and short-term Treasury exposure.
- Use QQQ, BTC-USD, GLD, and SGOV respectively.
- Clearly identify ETF proxies and distinguish them from index levels, spot gold, and Treasury yields.
- Provide a refresh control that clears cached market data and loaded watchlist quotes.

### Nasdaq-100 stocks

- Retrieve the complete constituent universe dynamically from Nasdaq's official public feed.
- Show the provider's constituent date and retrieval timestamp.
- Support more than 100 securities when companies have multiple included share classes.
- Allow searching by ticker or company name and selecting a stock.
- Display adjusted daily price history, selected-period return, latest observed price, and its position relative to the average of the latest 50 observations.
- Overlay 20- and 50-observation moving averages on the stock chart.
- Offer horizons of one, three, and six months and one, two, and five years.
- Provide an explicit action to load prices for all constituents; retain missing quotes as unavailable rather than fabricating values.
- Export the displayed watchlist as CSV.
- If the constituent feed fails, allow an individual ticker lookup.

### Top ten cryptocurrencies

- Rank cryptocurrencies dynamically by current USD market capitalization using CoinGecko.
- Include stablecoins and wrapped assets if they appear in the provider's top ten.
- Display rank, name, symbol, price, 24-hour percentage change, market capitalization, and provider update time.
- Allow selecting a cryptocurrency and inspecting its USD price trend.
- Limit historical requests to 365 days for the public API, even when a longer general chart horizon is selected.
- State that tracking the largest cryptocurrencies does not imply recommending their purchase.

### Gold and Treasuries

- Provide selectable charts for GLD, SGOV, SHY, IEF, and TLT.
- Identify their exposures as gold, 0–3 month Treasuries, 1–3 year Treasuries, 7–10 year Treasuries, and 20+ year Treasuries respectively.
- Explain that Treasury ETFs fluctuate and that longer maturity funds have greater interest-rate sensitivity.
- Explain that gold pays no income and SGOV is an ETF rather than a directly held Treasury bill.
- Link to official Treasury yield information; ETF prices must not be presented as yields.

### Fear and greed

- Provide separate stock-market and crypto sentiment panels.
- Use CNN Business for stock-market sentiment and Alternative.me for crypto sentiment.
- Display the provider's score on a 0–100 scale, classification, timestamp, gauge, and recent historical observations when available.
- Label 0 as extreme fear and 100 as extreme greed.
- Attribute both providers and link to their index pages.
- Explain that Alternative.me's index primarily measures Bitcoin sentiment and that sentiment alone is not a trading signal.
- If a feed fails, show its unavailable status and source link. Do not generate a substitute score.

### Portfolio planner

- Offer conservative, balanced, and growth scenarios as illustrative starting allocations.
- Allow entering a portfolio value and adjusting five asset weights.
- Require weights to total exactly 100% before presenting a valid plan or running analysis.
- Display target percentages, dollar amounts, an allocation chart, and a CSV export.
- Accept current dollar holdings and calculate buy/sell differences against target allocations using the total entered holdings.
- Use Bitcoin as the illustrative crypto sleeve; do not automatically allocate to every tracked cryptocurrency.
- Include broad US equity exposure alongside Nasdaq-100 exposure as an implementation choice for diversification.

| Asset | Proxy | Conservative | Balanced | Growth |
| --- | --- | ---: | ---: | ---: |
| Nasdaq-100 | QQQ | 15% | 30% | 45% |
| Broad US equities | VTI | 20% | 25% | 25% |
| Short-term Treasuries | SGOV | 45% | 30% | 15% |
| Gold | GLD | 18% | 10% | 8% |
| Bitcoin | BTC-USD | 2% | 5% | 7% |

These weights are implementation defaults, not allocations prescribed by the original request or personalized recommendations.

### Historical portfolio analysis

- Request two years of adjusted daily prices for positive-weight assets.
- Align assets on overlapping dates and require at least 30 price observations.
- Model a hypothetical portfolio with daily constant-weight rebalancing.
- Show annualized compounded return, annualized volatility, maximum drawdown, and hypothetical portfolio value over time.
- Include the initial portfolio value when computing drawdown so an immediate loss is captured.
- Display the actual analysis dates and methodological limitations.

For aligned daily returns `r[t,i]` and weights `w[i]`:

```text
Portfolio return[t] = sum(w[i] * r[t,i])
Growth[t] = product(1 + Portfolio return[t]), starting at 1
Annualized return = Final growth^(252 / number of return observations) - 1
Annualized volatility = sample standard deviation(Portfolio returns) * sqrt(252)
Maximum drawdown = minimum(Growth / running maximum(Growth) - 1)
```

Crypto weekends are excluded from the mixed-asset model because equity ETFs trade on business days. The model excludes fees, taxes, slippage, and other execution costs. Historical performance is not a forecast.

## Data sources and freshness

| Data | Source | Cache duration | Important limit |
| --- | --- | --- | --- |
| Nasdaq-100 constituents | Nasdaq public constituent API | 6 hours | Display the source date; membership can change |
| Security and portfolio prices | Yahoo Finance public chart endpoint | 5 minutes | Adjusted daily observations; current trading day may be incomplete |
| Crypto rankings and market statistics | CoinGecko public API | 5 minutes | Public API may rate-limit requests |
| Crypto historical prices | CoinGecko public API | 15 minutes | Requested history capped at 365 days |
| Stock-market sentiment | CNN public data endpoint | 15 minutes | Unofficial endpoint may block automated access |
| Crypto sentiment | Alternative.me API | 15 minutes | Primarily Bitcoin sentiment |

Network access is required. Cached values must not be described as guaranteed real-time prices. Missing data and request failures must remain visible to the user.

## Interface and technical requirements

- Use Streamlit with a dark, readable dashboard layout and Plotly charts.
- Organize the main experience into Nasdaq-100, Top 10 crypto, Gold & Treasuries, Fear & greed, and Portfolio lab tabs.
- Provide a sidebar for the chart horizon, refresh action, and source information.
- Run on Windows using the project's separate 64-bit Python 3.11 runtime and `.venv64` environment. The computer's existing 32-bit Python is unsuitable for the Arrow dependency.
- Bind the server to `127.0.0.1:8501`; the user accesses it through `http://localhost:8501`.
- Start through `start.ps1` and manage Python dependencies through `requirements.txt`.
- Keep market-data retrieval and portfolio calculations in `market_data.py`, and dashboard rendering in `app.py`.
- Disable Streamlit usage-statistics collection.
- Do not store credentials or require a brokerage account for the current public-data workflow.

## Acceptance criteria

1. The local server responds successfully at its homepage and health endpoint.
2. The user can search the full constituent universe, select a stock, and view its trend when the provider is available.
3. Crypto rankings come from the current provider response rather than a fixed list.
4. The user can inspect gold and Treasury ETF charts with clear proxy labels.
5. Both sentiment panels display either sourced readings with timestamps or explicit feed-unavailable messages and source links.
6. Portfolio weights totaling less or more than 100% block valid-plan analysis.
7. Allocation and rebalancing amounts reconcile with their respective entered totals.
8. Historical calculations correctly compound returns and include the initial value in drawdown calculations.
9. Watchlist and allocation CSV exports are available.
10. Provider failures do not cause an unhandled dashboard exception or introduce fabricated prices or sentiment.

## Verification and known limitations

At initial implementation, three automated checks passed: portfolio calculations, UI/allocation validation, and UI behavior when feeds fail. A full dashboard run using live providers completed without an unhandled exception, and the local homepage and health endpoint responded successfully. No visual browser review was performed.

Live checks returned 101 Nasdaq constituent securities and working Yahoo Finance and CoinGecko chart data. Alternative.me sentiment was available. CNN returned HTTP 418 and its panel therefore displayed an unavailable message with a source link. These observations describe the initial verification, not guaranteed future provider availability.

Public endpoints can change format, restrict requests, or become unavailable. The stock-market sentiment feed remains a known limitation until CNN access is restored or a separately approved data provider is integrated.
