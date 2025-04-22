import logging
import yfinance as yf
from typing import Optional, Dict, Any
import pandas as pd
import streamlit as st


def get_info_on_stock(ticker: str) -> Dict[str, Any]:
    """
    Fetch stock information for a given ticker using yfinance.

    Args:
        ticker (str): The stock ticker symbol.

    Returns:
        dict: A dictionary containing stock information.
    """
    try:
        stock = yf.Ticker(ticker)
        stock_info = stock.info
        # Removed the debugging output to avoid displaying stock info
        # st.write(f"Stock Info for {ticker}: {stock_info}")  # Debugging output
        return stock_info
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return {}


# Configure logging
logging.basicConfig(filename='stock_data.log', level=logging.INFO, format='%(asctime)s - %(message)s')