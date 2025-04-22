import yfinance as yf
import pandas as pd


tickers = "AMZN AAPL GOOG"

data = yf.download(tickers, start="2022-01-01", group_by='tickers')
data
print(data)