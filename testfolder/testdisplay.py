import streamlit as st
import pandas as pd
import warnings
from nextpage import nav_page

# Suppress warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(page_title='Stock Portfolio Home', page_icon=':bar_chart:', layout='wide')

# Google Font and Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Montserrat', sans-serif;
    background-color: #121212;
    color: white;
}

h1, h2, h3 {
    color: white;
}

.card {
    background-color: #1E1E1E;
    padding: 25px;
    border-radius: 15px;
    margin-bottom: 25px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.4);
}
</style>
""", unsafe_allow_html=True)

# Title Section
st.markdown("<h1>📊 Stock Portfolio Builder</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='margin-top:-10px;'>Build your portfolio to unlock analysis</h3>", unsafe_allow_html=True)
st.divider()

# Initialize session state
if "stocks" not in st.session_state:
    st.session_state.stocks = []

# Function to add new stock entry
def add_stock():
    st.session_state.stocks.append({"ticker": "", "quantity": ""})

# Card-style input area
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### ➕ Add Your Stocks")

for i, stock in enumerate(st.session_state.stocks):
    col1, col2 = st.columns(2)
    stock["ticker"] = col1.text_input(f"Stock Ticker {i+1}", value=stock["ticker"], key=f"ticker_{i}", help="e.g., AAPL, MSFT, TSLA")
    stock["quantity"] = col2.text_input(f"Quantity Owned {i+1}", value=stock["quantity"], key=f"quantity_{i}", help="Enter a whole number")

st.markdown("</div>", unsafe_allow_html=True)

# Add another stock button
if st.button("➕ Add Another Stock"):
    add_stock()

# Display current portfolio
valid_stocks = [s for s in st.session_state.stocks if s["ticker"] and s["quantity"].isdigit()]
if valid_stocks:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📂 Your Current Portfolio")
    df = pd.DataFrame(valid_stocks)
    df["quantity"] = df["quantity"].astype(int)
    st.dataframe(df, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Navigation button to Dashboard
if valid_stocks:
    if st.button("📈 Go to Dashboard"):
        nav_page("Dashboard")  # Replace "Dashboard" with the actual name of your next page
else:
    st.warning("Add at least one valid stock (ticker and quantity) to proceed.")
