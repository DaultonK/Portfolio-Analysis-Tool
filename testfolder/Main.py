from get_info_on_stock import get_info_on_stock
import pandas as pd
import yfinance as yf



ticker_list = []
test_list = ['aapl','goog','msft']
indexes = 'SPY'
test_list.append(indexes)
for stock in test_list:
    get_info_on_stock(stock)

import yfinance as yf

#ticker = 'SPY'
#try:
#    stock = yf.Ticker(ticker)
#    print(stock.info)  # Check if the data is fetched correctly
#except Exception as e:
#    print(f"Error fetching data for {ticker}: {e}")