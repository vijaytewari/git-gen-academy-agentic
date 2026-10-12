from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import requests
import pandas as pd
import streamlit as st

HEADERS = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json,text/html'}

def get(url, params=None):
    response = requests.get(url, params=params, headers=HEADERS, timeout=18)
    response.raise_for_status()
    return response

@st.cache_data(ttl=21600)
def constituents():
    data = get('https://api.nasdaq.com/api/quote/list-type/nasdaq100').json()['data']
    table = pd.DataFrame(data['data']['rows']).rename(columns={'symbol':'Symbol','companyName':'Name'})
    table['Symbol'] = table['Symbol'].str.replace('.', '-', regex=False)
    return table[['Symbol','Name']], '{}; retrieved {}'.format(data['date'],datetime.now(timezone.utc).isoformat())

@st.cache_data(ttl=300)
def history(symbols, period='1y'):
    def fetch(symbol):
        try:
            payload = get('https://query1.finance.yahoo.com/v8/finance/chart/'+symbol,
                          {'range':period,'interval':'1d'}).json()['chart']['result'][0]
            indicators = payload['indicators']
            values = indicators['adjclose'][0]['adjclose']
            index = pd.to_datetime(payload['timestamp'],unit='s',utc=True).normalize()
            return pd.Series(values,index=index,name=symbol).dropna()
        except (requests.RequestException,KeyError,TypeError,ValueError):
            return pd.Series(dtype=float,name=symbol)
    with ThreadPoolExecutor(max_workers=6) as pool:
        close = pd.concat(list(pool.map(fetch,symbols)),axis=1)
    if close.empty:
        raise ValueError('Yahoo Finance returned no price data; it may be rate-limiting requests.')
    return close.dropna(how='all').sort_index()

@st.cache_data(ttl=300)
def crypto_markets():
    return pd.DataFrame(get('https://api.coingecko.com/api/v3/coins/markets', {
        'vs_currency': 'usd', 'order': 'market_cap_desc', 'per_page': 10,
        'page': 1, 'sparkline': 'false'}).json())

@st.cache_data(ttl=900)
def crypto_history(coin, days):
    data = get('https://api.coingecko.com/api/v3/coins/{}/market_chart'.format(coin),
               {'vs_currency': 'usd', 'days': days}).json()
    frame = pd.DataFrame(data['prices'], columns=['Date', 'Close'])
    frame['Date'] = pd.to_datetime(frame['Date'], unit='ms', utc=True)
    return frame.set_index('Date')['Close']

@st.cache_data(ttl=900)
def sentiment(kind):
    if kind == 'crypto':
        data = get('https://api.alternative.me/fng/', {'limit': 90}).json()['data']
        frame = pd.DataFrame(data)
        frame['Date'] = pd.to_datetime(frame['timestamp'].astype(int), unit='s', utc=True)
        frame['Score'] = frame['value'].astype(float)
        return frame[['Date', 'Score']].sort_values('Date'), data[0]['value_classification']
    data = get('https://production.dataviz.cnn.io/index/fearandgreed/graphdata').json()
    frame = pd.DataFrame(data['fear_and_greed_historical']['data'])
    frame['Date'] = pd.to_datetime(frame['x'], unit='ms', utc=True)
    frame['Score'] = frame['y']
    current = data['fear_and_greed']
    # Append the explicitly timestamped current reading, rather than assuming history is current.
    frame = pd.concat([frame[['Date', 'Score']], pd.DataFrame([{
        'Date': pd.to_datetime(current['timestamp'], utc=True), 'Score': current['score']}])])
    return frame.sort_values('Date'), current['rating']

def portfolio_statistics(prices, weights):
    prices = prices.dropna()
    if len(prices) < 30:
        raise ValueError('At least 30 overlapping observations are needed.')
    returns = prices.pct_change(fill_method=None).dropna()
    portfolio = returns.mul(pd.Series(weights)).sum(axis=1)
    growth = (1 + portfolio).cumprod()
    annual_return = growth.iloc[-1] ** (252 / len(portfolio)) - 1
    volatility = portfolio.std() * (252 ** 0.5)
    growth = pd.concat([pd.Series([1.0], index=[prices.index[0]]), growth])
    drawdown = (growth / growth.cummax() - 1).min()
    return growth, annual_return, volatility, drawdown
