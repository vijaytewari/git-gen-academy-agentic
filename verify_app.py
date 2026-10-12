"""Offline UI and portfolio validation using explicitly synthetic test fixtures."""
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest
import market_data as data

def fixture_history(symbols, period='1y'):
    index = pd.date_range('2025-01-01', periods=80, freq='B')
    return pd.DataFrame({symbol:100*np.power(1.001,np.arange(80)) for symbol in symbols},index=index)

class DashboardTests(unittest.TestCase):
    def test_portfolio_compounding_and_drawdown(self):
        prices = fixture_history(['QQQ','GLD'])
        growth, ret, vol, drawdown = data.portfolio_statistics(prices,{'QQQ':.6,'GLD':.4})
        self.assertAlmostEqual(growth.iloc[-1],1.001**79)
        self.assertAlmostEqual(ret,1.001**252-1)
        self.assertAlmostEqual(vol,0)
        self.assertAlmostEqual(drawdown,0)
        prices.iloc[1:] = 90
        _, _, _, drawdown = data.portfolio_statistics(prices,{'QQQ':.6,'GLD':.4})
        self.assertAlmostEqual(drawdown,-.1)

    def test_ui_and_allocation_validation(self):
        coins = pd.DataFrame([dict(id='bitcoin',market_cap_rank=1,name='Bitcoin',symbol='btc',current_price=100,price_change_percentage_24h=1,market_cap=100000,last_updated='2025-04-01')])
        mood = pd.DataFrame({'Date':pd.date_range('2025-01-01',periods=90,tz='UTC'),'Score':[50]*90})
        with patch.object(data,'history',side_effect=fixture_history), patch.object(data,'constituents',return_value=(pd.DataFrame({'Symbol':['AAPL'],'Name':['Apple']}),'test fixture')), patch.object(data,'crypto_markets',return_value=coins), patch.object(data,'crypto_history',return_value=fixture_history(['BTC'])['BTC']), patch.object(data,'sentiment',return_value=(mood,'Neutral')):
            app = AppTest.from_file('app.py').run(timeout=30)
            self.assertEqual(len(app.exception),0)
            next(b for b in app.button if b.label=='Analyze historical risk').click().run()
            self.assertEqual(len(app.exception),0)
            self.assertTrue(any(m.label=='Maximum drawdown' for m in app.metric))
            app.slider[0].set_value(31).run()
            self.assertTrue(any('exactly 100%' in w.value for w in app.warning))

    def test_feed_failure_ui(self):
        with patch.object(data,'history',side_effect=ValueError('offline')), patch.object(data,'constituents',side_effect=ValueError('offline')), patch.object(data,'crypto_markets',side_effect=ValueError('offline')), patch.object(data,'sentiment',side_effect=ValueError('offline')):
            app = AppTest.from_file('app.py').run(timeout=30)
            self.assertEqual(len(app.exception),0)
            self.assertGreaterEqual(len(app.warning),5)

if __name__=='__main__':
    unittest.main()
