# 👇 Full code begins here
import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from fpdf import FPDF
from io import BytesIO
import plotly.io as pio
import tempfile
from datetime import date
import plotly.graph_objects as go


# Project-specific imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from stock_dashboard.Get_stock_region import stock_region_diversification
from stock_dashboard.get_info_on_stock import get_info_on_stock

st.set_page_config(page_title="📈 Portfolio Dashboard", layout="wide")

# ----------------- STYLING -----------------
st.markdown("""
<style>
.card {
    background-color: #1E1E1E;
    padding: 25px;
    border-radius: 15px;
    margin-bottom: 25px;
}
</style>
""", unsafe_allow_html=True)


portfolio = st.session_state.get("portfolio", [])

if not portfolio:
    st.warning("No portfolio found. Using sample data.")
    portfolio = [
        {"ticker": "AAPL", "quantity": 10}, {"ticker": "MSFT", "quantity": 5},
        {"ticker": "TSLA", "quantity": 3}, {"ticker": "AMZN", "quantity": 8},
        {"ticker": "GOOGL", "quantity": 6}, {"ticker": "NESN.SW", "quantity": 12},
        {"ticker": "ASML.AS", "quantity": 4}, {"ticker": "MC.PA", "quantity": 2},
        {"ticker": "SIE.DE", "quantity": 7}, {"ticker": "ULVR.L", "quantity": 9},
        {"ticker": "7203.T", "quantity": 15}, {"ticker": "005930.KS", "quantity": 1},
        {"ticker": "9988.HK", "quantity": 10}, {"ticker": "TCS.NS", "quantity": 5},
        {"ticker": "0700.HK", "quantity": 8}
    ]

df = pd.DataFrame(portfolio)
df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
df.dropna(subset=["quantity"], inplace=True)

# ----------------- INIT CHART VARIABLES -----------------
fig_alloc = None
fig_region = None

# --- Fetch Prices ---
@st.cache_data(show_spinner=False)
def fetch_price(ticker):
    try:
        stock_info = get_info_on_stock(ticker)
        return stock_info.get("regularMarketPrice", 0)
    except:
        return 0

df["price"] = df["ticker"].apply(fetch_price)
df["value"] = df["price"] * df["quantity"]
df = df[df["price"] > 0]
total_value = df["value"].sum()

# --- Tab Layout ---
tab = st.radio("📂 View Options", [
    "📊 Overview", 
    "📈 Value Over Time", 
    "📌 Price Change", 
    "📋 Summary", 
    "📁 Export"
])
# --- 📊 OVERVIEW ---
if tab == "📊 Overview":
    st.title("📈 Portfolio Overview")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Total Portfolio Value", f"${total_value:,.2f}")
    with col2:
        st.metric("📦 Total Holdings", len(df))
    with col3:
        if not df.empty:
            st.metric("🏆 Top Holding", df.loc[df["value"].idxmax()]["ticker"])

    # Allocation Chart
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📊 Allocation by Ticker")
        fig_alloc = px.pie(df, values="value", names="ticker", hole=0.4, title="Portfolio Allocation")
        st.plotly_chart(fig_alloc, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Regional Diversification
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🌍 Regional Diversification")
        tickers_qty = dict(zip(df["ticker"], df["quantity"]))
        region_data = stock_region_diversification(tickers_qty)
        if isinstance(region_data, dict):
            fig_region = px.pie(
                names=list(region_data.keys()),
                values=list(region_data.values()),
                title="Regional Diversification",
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig_region, use_container_width=True)
        else:
            st.error(f"❌ Region error: {region_data}")
        st.markdown('</div>', unsafe_allow_html=True)

    # Sector Allocation (Moved from separate tab)
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🏢 Sector Allocation")

        @st.cache_data(show_spinner=True)
        def get_sectors(tickers):
            sector_map = {}
            for ticker in tickers:
                try:
                    info = yf.Ticker(ticker).info
                    sector_map[ticker] = info.get("sector", "Unknown")
                except:
                    sector_map[ticker] = "Unknown"
            return sector_map

        sector_data = get_sectors(df["ticker"].tolist())
        df["sector"] = df["ticker"].map(sector_data)
        sector_group = df.groupby("sector")["value"].sum().reset_index().sort_values("value", ascending=False)

        fig_sector = px.pie(sector_group, names="sector", values="value", hole=0.4, title="Portfolio by Sector")
        st.plotly_chart(fig_sector, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------- PRICE CHANGE -----------------
elif tab == "📌 Price Change":
    st.title("📌 Multi-Period Price Change")

    @st.cache_data(show_spinner=True)
    def get_close_data(tickers, start="2015-01-01"):
        df = yf.download(tickers, start=start, auto_adjust=True)["Close"]
        if isinstance(df, pd.Series):
            df = df.to_frame()
        return df

    close_data = get_close_data(df["ticker"].tolist())
    timeframes = {
        "1 Week": 7, "1 Month": 30, "1 Year": 365, "5 Years": 365 * 5
    }

    for ticker in df["ticker"]:
        st.subheader(f"📈 {ticker}")
        if ticker not in close_data.columns:
            st.warning("No data available.")
            continue

        price_series = close_data[ticker].dropna()
        if price_series.empty or len(price_series) < 2:
            st.write("Not enough data.")
            continue

        def get_change(days):
            ref_date = price_series.index[-1] - pd.Timedelta(days=days)
            past = price_series[price_series.index <= ref_date]
            if past.empty:
                return None
            past_price = past.iloc[-1]
            current_price = price_series.iloc[-1]
            pct = ((current_price - past_price) / past_price) * 100
            return current_price, past_price, pct

        cols = st.columns(3)
        for i, (label, days) in enumerate(timeframes.items()):
            result = get_change(days)
            with cols[i % 3]:
                if result:
                    current, past, pct = result
                    st.metric(label, f"${current:,.2f}", f"{pct:+.2f}%")
                else:
                    st.metric(label, "N/A", "N/A")

        first = price_series.iloc[0]
        last = price_series.iloc[-1]
        pct_all_time = ((last - first) / first) * 100
        st.metric("All Time", f"${last:,.2f}", f"{pct_all_time:+.2f}%")


# --- 📈 VALUE OVER TIME ---
elif tab == "📈 Value Over Time":
    st.title("📈 Portfolio Performance Over Time")

    @st.cache_data(show_spinner=True)
    def get_price_history(tickers, start="2020-01-01"):
        tickers = list(set(tickers + ["^GSPC"]))  # Add S&P 500 for comparison
        data = yf.download(tickers, start=start, auto_adjust=True, progress=False)
    
        # Debugging output to inspect the data structure
        st.write("Downloaded Data Structure:", data.head())
    
        if data.empty:
            st.error("No historical data available for the selected tickers.")
            return pd.DataFrame()
    
        if isinstance(data.columns, pd.MultiIndex):
            st.write("MultiIndex Columns:", data.columns)
            if "Close" in data.columns.get_level_values(1):
                return data.xs("Close", axis=1, level=1)
            elif "Adj Close" in data.columns.get_level_values(1):
                return data.xs("Adj Close", axis=1, level=1)
            elif "Open" in data.columns.get_level_values(1):
                st.warning("Using 'Open' prices as fallback.")
                return data.xs("Open", axis=1, level=1)
            else:
                st.error("No suitable price columns ('Close', 'Adj Close', or 'Open') are available.")
                return pd.DataFrame()
    
        return data


    hist_data = get_price_history(df["ticker"].tolist())

    if hist_data.empty:
        st.error("No historical data available.")
    else:
        stock_prices = hist_data[df["ticker"]].dropna()
        avg_portfolio = stock_prices.mean(axis=1)
        sp500 = hist_data["^GSPC"]

        fig = go.Figure()

        # Individual stock lines
        for ticker in stock_prices.columns:
            fig.add_trace(go.Scatter(x=stock_prices.index, y=stock_prices[ticker],
                                     mode='lines', name=ticker, opacity=0.4))

        # Portfolio average
        fig.add_trace(go.Scatter(x=avg_portfolio.index, y=avg_portfolio,
                                 mode='lines', name='Portfolio Avg', line=dict(width=4, dash='dot')))

        # S&P 500
        fig.add_trace(go.Scatter(x=sp500.index, y=sp500,
                                 mode='lines', name='S&P 500', line=dict(width=4, color='black')))

        fig.update_layout(
            title="📈 Historical Performance: Portfolio vs S&P 500",
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)



# ----------------- SUMMARY -----------------
elif tab == "📋 Summary":
    st.title("📋 Stock Summary")
    for stock in df["ticker"]:
        try:
            info = yf.Ticker(stock).info
            with st.expander(f"{stock} — {info.get('longName', 'Company')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Sector:** {info.get('sector', 'N/A')}")
                    st.write(f"**Industry:** {info.get('industry', 'N/A')}")
                    st.write(f"**Shares Owned:** {df[df['ticker'] == stock]['quantity'].values[0]}")
                with col2:
                    st.write(f"**Market Cap:** ${info.get('marketCap', 'N/A'):,}")
                    st.write(f"**PE Ratio:** {info.get('trailingPE', 'N/A')}")
                    st.write(f"**52 Week High:** ${info.get('fiftyTwoWeekHigh', 'N/A')}")
                    st.write(f"**52 Week Low:** ${info.get('fiftyTwoWeekLow', 'N/A')}")
                    st.write(f"**Previous Close:** ${info.get('previousClose', 'N/A')}")
        except Exception as e:
            st.warning(f"Could not retrieve data for {stock}: {e}")

# ----------------- EXPORT -----------------
elif tab == "📁 Export":
    st.title("📁 Export Your Portfolio")

    col_csv, col_pdf = st.columns(2)

    with col_csv:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, "portfolio.csv", "text/csv")

    with col_pdf:
        def create_pdf(dataframe, charts):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            pdf.cell(200, 10, txt="Portfolio Summary", ln=True, align='C')
            pdf.ln(10)
            for _, row in dataframe.iterrows():
                line = f"{row['ticker']}: Qty={row['quantity']}, Price=${row['price']:.2f}, Value=${row['value']:.2f}"
                pdf.cell(200, 10, txt=line, ln=True)

            pdf.ln(10)
            pdf.cell(200, 10, txt=f"Total Portfolio Value: ${total_value:,.2f}", ln=True)
            pdf.ln(10)

            for fig in charts:
                if fig:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                        pio.write_image(fig, tmpfile.name, format="png")
                        pdf.image(tmpfile.name, w=180)
                        pdf.ln(10)

            buffer = BytesIO()
            pdf.output(buffer)
            buffer.seek(0)
            return buffer

        charts = [fig for fig in [fig_alloc, fig_region] if fig is not None]
        pdf_file = create_pdf(df, charts)
        st.download_button("🧾 Download PDF with Charts", pdf_file, "portfolio_summary.pdf", "application/pdf")
