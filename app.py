import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from market_data import constituents, history, crypto_markets, crypto_history, sentiment, portfolio_statistics

st.set_page_config(page_title='Atlas | Market & Portfolio Desk', page_icon='◈', layout='wide')
st.markdown('''<style>
.block-container{padding-top:2rem;max-width:1550px}
h1{letter-spacing:-1.8px} [data-testid="stMetric"]{background:#111c2e;padding:18px;border:1px solid #223149;border-radius:12px}
[data-testid="stSidebar"]{border-right:1px solid #223149} .stTabs [data-baseweb="tab"]{font-size:16px}
</style>''', unsafe_allow_html=True)

def chart(series, title, averages=False):
    fig = go.Figure(go.Scatter(x=series.index, y=series, name='Adjusted close', line=dict(color='#38d9ba', width=2), fill='tozeroy', fillcolor='rgba(56,217,186,.06)'))
    if averages:
        for days, color in [(20, '#fbbf24'), (50, '#879cff')]:
            fig.add_trace(go.Scatter(x=series.index, y=series.rolling(days).mean(), name='{}-day average'.format(days), line=dict(color=color, width=1)))
    fig.update_layout(title=title, height=420, template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10,r=10,t=45,b=15), legend=dict(orientation='h'), hovermode='x unified', yaxis_title='USD')
    st.plotly_chart(fig, use_container_width=True)

def price_metrics(series):
    series = series.dropna()
    if len(series) < 2:
        st.info('Not enough observations for trend metrics.'); return
    a,b,c = st.columns(3)
    a.metric('Latest observed price', '${:,.2f}'.format(series.iloc[-1]), '{:+.2f}% vs previous observation'.format((series.iloc[-1]/series.iloc[-2]-1)*100))
    b.metric('Selected period return', '{:+.2f}%'.format((series.iloc[-1]/series.iloc[0]-1)*100))
    c.metric('Trend vs 50-observation average', 'Above' if series.iloc[-1] > series.tail(50).mean() else 'Below')
    st.caption('Latest observation: {} • Adjusted prices from Yahoo Finance for securities; CoinGecko USD prices for crypto. Trend indicators describe history, not a forecast.'.format(series.index[-1]))

with st.sidebar:
    st.markdown('## ◈ ATLAS')
    st.caption('YOUR MARKET & PORTFOLIO DESK')
    period = st.selectbox('Chart horizon', ['1mo','3mo','6mo','1y','2y','5y'], index=3)
    if st.button('↻ Refresh market data', use_container_width=True):
        st.cache_data.clear()
        st.session_state.pop('stock_quotes', None)
        st.rerun()
    st.divider()
    st.markdown('**Market data**\n\nYahoo Finance · CoinGecko\n\n**Sentiment**\n\nCNN Business · Alternative.me')
    st.caption('Quotes may be delayed. Prices cache for 5 minutes, sentiment for 15 minutes, constituents for 6 hours. Public feeds can restrict requests.')
    st.link_button('Nasdaq index information', 'https://www.nasdaq.com/products/global-indexes/nasdaq-100')

st.caption('MULTI-ASSET INTELLIGENCE / USD')
st.title('Market Intelligence')
st.write('Explore markets. Read sentiment. Build a portfolio with a risk level you understand.')
overview = ['QQQ','BTC-USD','GLD','SGOV']
try:
    prices = history(overview, '5d')
    for col, ticker, name in zip(st.columns(4), overview, ['Nasdaq-100 · QQQ','Bitcoin','Gold · GLD','T-bills · SGOV']):
        with col:
            s = prices[ticker].dropna()
            if len(s)>1: st.metric(name, '${:,.2f}'.format(s.iloc[-1]), '{:+.2f}%'.format((s.iloc[-1]/s.iloc[-2]-1)*100))
            else: st.metric(name, 'Unavailable')
    st.caption('Latest available adjusted daily prices; the current trading day may be incomplete. Change vs previous observation. ETF prices are proxies, not index levels, spot gold, or Treasury yields.')
except Exception as exc:
    st.warning('Overview feed unavailable: {}'.format(exc))

stocks, crypto, defensive, mood, planner = st.tabs(['Nasdaq-100','Top 10 crypto','Gold & Treasuries','Fear & greed','Portfolio lab'])
with stocks:
    st.subheader('The Nasdaq-100 universe')
    try:
        members, fetched = constituents()
        st.caption('Constituents: Nasdaq official feed • source date {}. The index can contain more than 100 share classes.'.format(fetched))
        query = st.text_input('Search company or ticker', placeholder='Apple, NVDA, Microsoft…')
        filtered = members[members['Symbol'].str.contains(query, case=False, regex=False) | members['Name'].str.contains(query, case=False, regex=False)]
        if not filtered.empty:
            selected = st.selectbox('Select a stock', filtered['Symbol'], format_func=lambda x: '{} · {}'.format(x, members.set_index('Symbol').loc[x,'Name']))
            s = history([selected], period)[selected].dropna()
            price_metrics(s); chart(s, selected + ' / price & trend', True)
        else: st.info('No matching companies.')
        if st.button('Load prices for every constituent'):
            with st.spinner('Loading the full universe…'):
                all_prices = history(members['Symbol'].tolist(), '5d')
            rows = []
            for ticker in members['Symbol']:
                s = all_prices[ticker].dropna() if ticker in all_prices else pd.Series(dtype=float)
                rows.append({'Symbol':ticker,'Price USD':s.iloc[-1] if len(s) else None,'Change %':(s.iloc[-1]/s.iloc[-2]-1)*100 if len(s)>1 else None,'Price date':str(s.index[-1]) if len(s) else 'Unavailable'})
            st.session_state['stock_quotes'] = pd.DataFrame(rows)
        table = filtered
        if 'stock_quotes' in st.session_state: table = table.merge(st.session_state['stock_quotes'], on='Symbol', how='left')
        st.dataframe(table, hide_index=True, use_container_width=True)
        st.download_button('Export stock watchlist', table.to_csv(index=False), 'nasdaq_watchlist.csv','text/csv')
    except Exception as exc:
        st.warning('Nasdaq data unavailable: {}. You can still look up an individual ticker.'.format(exc))
        ticker = st.text_input('Stock ticker', 'AAPL').strip().upper()
        try:
            s = history([ticker], period)[ticker].dropna(); price_metrics(s); chart(s,ticker,True)
        except Exception as error: st.info(str(error))
with crypto:
    st.subheader('Top 10 by current market capitalization')
    st.caption('Ranked dynamically by CoinGecko; includes stablecoins and wrapped assets when ranked in the top ten.')
    try:
        coins = crypto_markets()
        cols = ['market_cap_rank','name','symbol','current_price','price_change_percentage_24h','market_cap','last_updated']
        st.dataframe(coins[cols].rename(columns={'market_cap_rank':'Rank','name':'Name','symbol':'Symbol','current_price':'Price USD','price_change_percentage_24h':'24h %','market_cap':'Market cap USD','last_updated':'Updated UTC'}),hide_index=True,use_container_width=True)
        coin = st.selectbox('Explore cryptocurrency', coins['id'],format_func=lambda x: coins.set_index('id').loc[x,'name'])
        days = min({'1mo':30,'3mo':90,'6mo':180,'1y':365,'2y':730,'5y':1825}[period],365)
        st.caption('Free CoinGecko history is limited to up to 365 days; provider limits may vary.')
        s = crypto_history(coin,days); price_metrics(s); chart(s,coin.title())
    except Exception as exc: st.warning('CoinGecko feed unavailable: {}. Refresh later; the free API may rate-limit requests.'.format(exc))
with defensive:
    st.subheader('Your defensive assets, in context')
    proxies = {'GLD':'Gold ETF','SGOV':'0–3 month Treasury ETF','SHY':'1–3 year Treasury ETF','IEF':'7–10 year Treasury ETF','TLT':'20+ year Treasury ETF'}
    selected = st.selectbox('Gold or Treasury exposure',list(proxies),format_func=lambda x: x+' · '+proxies[x])
    st.info('Treasury ETFs fluctuate in value; longer maturity funds are more sensitive to interest rates. Gold pays no income. SGOV is an ETF, not a direct Treasury bill.')
    try:
        s = history([selected],period)[selected].dropna(); price_metrics(s); chart(s,selected,True)
    except Exception as exc: st.warning(str(exc))
    st.link_button('Current official Treasury yield curves','https://home.treasury.gov/resource-center-data-chart-center/interest-rates')
with mood:
    st.subheader('Market temperature')
    for col, kind, title, source in zip(st.columns(2),['finance','crypto'],['Stock market · CNN','Crypto · Alternative.me'],['https://www.cnn.com/markets/fear-and-greed','https://alternative.me/crypto/fear-and-greed-index/']):
        with col:
            st.markdown('### '+title)
            try:
                frame, label = sentiment(kind)
                score = float(frame.iloc[-1]['Score'])
                st.metric(label.title(),'{:.0f} / 100'.format(score))
                fig = go.Figure(go.Indicator(mode='gauge+number',value=score,gauge={'axis':{'range':[0,100]},'bar':{'color':'#e7edf8'},'steps':[{'range':[0,25],'color':'#b54755'},{'range':[25,45],'color':'#bd8550'},{'range':[45,55],'color':'#61738d'},{'range':[55,75],'color':'#338f81'},{'range':[75,100],'color':'#207967'}]}))
                fig.update_layout(height=240,margin=dict(t=25,b=10,l=30,r=30),paper_bgcolor='rgba(0,0,0,0)',font_color='#e7edf8')
                st.plotly_chart(fig,use_container_width=True)
                st.caption('Provider timestamp: {}'.format(frame.iloc[-1]['Date']))
                st.line_chart(frame.set_index('Date')['Score'].tail(90))
            except Exception as exc: st.warning('Index unavailable: {}. No substitute score is generated.'.format(exc))
            st.link_button('View source index',source)
    st.caption('0 = extreme fear · 100 = extreme greed. Alternative.me is primarily Bitcoin sentiment. Sentiment alone is not a buy or sell signal. CNN’s public endpoint is unofficial and may block access.')
with planner:
    st.subheader('Build a plan you can inspect')
    st.info('Educational scenarios, not personalized investment advice. No allocation is universally perfect. Your time horizon, liquidity needs, taxes, debt, and ability to withstand losses matter. Nasdaq exposure is concentrated; a broad-market equity allocation is included for diversification.')
    presets = {'Conservative':[15,20,45,18,2],'Balanced':[30,25,30,10,5],'Growth':[45,25,15,8,7]}
    profile = st.selectbox('Illustrative starting scenario',list(presets),index=1)
    capital = st.number_input('Portfolio value (USD)',min_value=100.0,value=10000.0,step=1000.0)
    names = ['Nasdaq-100 · QQQ','Broad US equity · VTI','T-bills · SGOV','Gold · GLD','Bitcoin · BTC-USD']
    symbols = ['QQQ','VTI','SGOV','GLD','BTC-USD']
    weights = [col.slider(name,0,100,presets[profile][i],key=profile+symbol) for i,(col,name,symbol) in enumerate(zip(st.columns(5),names,symbols))]
    total = sum(weights)
    st.caption('Allocation total: {}% • Bitcoin represents the crypto sleeve; top-ten membership is not a portfolio recommendation.'.format(total))
    if total != 100:
        st.warning('Adjust weights to total exactly 100% before running the plan.')
    else:
        plan = pd.DataFrame({'Asset':names,'Symbol':symbols,'Target %':weights,'Target USD':[capital*w/100 for w in weights]})
        left,right = st.columns([1,2])
        with left:
            fig = px.pie(plan,names='Asset',values='Target %',hole=.65,color_discrete_sequence=['#38d9ba','#879cff','#6d9dc5','#fbbf24','#eb7e62'])
            fig.update_layout(height=300,margin=dict(t=10,b=10,l=10,r=10),showlegend=False,paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig,use_container_width=True)
        with right: st.dataframe(plan,hide_index=True,use_container_width=True)
        st.download_button('Download allocation plan',plan.to_csv(index=False),'portfolio_plan.csv','text/csv')
        st.markdown('**Rebalance your holdings**')
        holdings = [col.number_input(name+' current USD',min_value=0.0,value=capital*w/100,key='holding'+symbol) for col,name,symbol,w in zip(st.columns(5),names,symbols,weights)]
        holdings_total = sum(holdings)
        if holdings_total > 0:
            rebalance = plan[['Asset','Target %']].copy()
            rebalance['Current USD'] = holdings
            rebalance['Target USD'] = [holdings_total*w/100 for w in weights]
            rebalance['Buy / sell USD'] = rebalance['Target USD']-rebalance['Current USD']
            st.dataframe(rebalance,hide_index=True,use_container_width=True)
            st.caption('Rebalancing uses the total entered holdings; positive = buy, negative = sell. Review quarterly or when allocations drift by 5 percentage points; consider taxes and transaction costs.')
        if st.button('Analyze historical risk',type='primary'):
            try:
                active = {symbol:w/100 for symbol,w in zip(symbols,weights) if w>0}
                with st.spinner('Aligning historical prices…'):
                    prices = history(list(active),'2y')[list(active)]
                    growth,ret,vol,dd = portfolio_statistics(prices,active)
                a,b,c = st.columns(3)
                a.metric('Annualized historical return','{:.1%}'.format(ret)); b.metric('Annualized volatility','{:.1%}'.format(vol)); c.metric('Maximum drawdown','{:.1%}'.format(dd))
                chart(growth*capital,'Hypothetical portfolio value')
                st.caption('Daily constant-weight rebalancing on overlapping trading dates from {} to {}. Adjusted closes approximate distributions; excludes taxes, fees, slippage. Crypto is sampled on equity trading days. Historical performance does not predict future returns.'.format(growth.index[0].date(),growth.index[-1].date()))
            except Exception as exc: st.warning('Risk analysis unavailable: {}'.format(exc))
    st.link_button('Learn about asset allocation · Investor.gov','https://www.investor.gov/introduction-investing/getting-started/asset-allocation')
st.divider()
st.caption('ATLAS / Research & planning workspace • No brokerage connection or order execution • Verify quotes before making investment decisions.')
