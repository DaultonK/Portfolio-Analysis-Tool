import streamlit as st
import plotly.express as px
import pandas as pd
import warnings
from nextpage import nav_page

# Suppress warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(page_title='Stock Portfolio Analysis', page_icon=':bar_chart:', layout='wide')

# Custom CSS for styling
st.markdown(
    """
    <style>
    .stApp {
        background-color: #121212;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title and subtitle
st.markdown(
    """
    <h1 style="color:white;">Stock Portfolio Analysis</h1>
    <h3 style="color:white; font-size:16px; margin-top:-10px;">Managing your stock portfolio efficiently</h3>
    """,
    unsafe_allow_html=True
)

# Add a horizontal divider
st.divider()

# Initialize session state for stocks
if "stocks" not in st.session_state:
    st.session_state.stocks = []

# Function to add a new stock entry
def add_stock():
    st.session_state.stocks.append({"ticker": "", "quantity": ""})

# Section: Add Your Stocks
st.markdown(
    """
    <h2 style="color:white; font-size:30px; margin-top:-20px;">Add Your Stocks</h2>
    """,
    unsafe_allow_html=True
)

# Dynamic input fields for stocks
for i, stock in enumerate(st.session_state.stocks):
    col1, col2 = st.columns(2)
    stock["ticker"] = col1.text_input(f"Stock Ticker {i+1}", value=stock["ticker"], key=f"ticker_{i}")
    stock["quantity"] = col2.text_input(f"Quantity Owned {i+1}", value=stock["quantity"], key=f"quantity_{i}")

# Button to add another stock
if st.button("Add Another Stock"):
    add_stock()

# Section: Display Portfolio
if st.session_state.stocks:
    st.markdown(
        """
        <h2 style="color:white; font-size:30px; margin-top:20px;">Current Portfolio</h2>
        """,
        unsafe_allow_html=True
    )
    portfolio_df = pd.DataFrame(st.session_state.stocks)
    st.dataframe(portfolio_df)

    # Bar chart for stock quantities
    portfolio_df["quantity"] = pd.to_numeric(portfolio_df["quantity"], errors="coerce")
    fig = px.bar(portfolio_df, x="ticker", y="quantity", title="Stock Quantities")
    st.plotly_chart(fig)

# Navigation buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("< Prev"):
        nav_page("Foo")
with col2:
    if st.button("Next >"):
        nav_page("Bar")