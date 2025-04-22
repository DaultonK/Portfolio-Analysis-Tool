import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px

def render_summary_tab(df):
    # === Full Dark Theme + White Text Styling ===
    st.markdown("""
    <style>
    html, body, [class*="stApp"] {
        background-color: #1E1E2F !important;
        color: white !important;
        font-family: 'Montserrat', sans-serif !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #262637 !important;
    }
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    .stMetric label, .stMetric div, .stMarkdown {
        color: white !important;
    }
    label, .stSelectbox label, .stTextInput label, .stSlider label,
    .css-1c7y2kd, .css-1d391kg, .css-1v0mbdj, .stRadio label {
        color: white !important;
    }
    button {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("Stock Trading Dashboard")

    if "ticker" not in df.columns:
        st.error("Input DataFrame must contain a 'ticker' column.")
        return None, None

    tickers = df["ticker"].dropna().unique().tolist()
    selected = st.selectbox("Select a stock to analyze", tickers)

    @st.cache_data
    def get_stock_data(ticker):
        t = yf.Ticker(ticker)
        info = t.info
        hist = t.history(period="1y", auto_adjust=True)
        hist["SMA_50"] = hist["Close"].rolling(50).mean()
        hist["SMA_200"] = hist["Close"].rolling(200).mean()
        hist["Volatility"] = hist["Close"].pct_change().rolling(30).std() * np.sqrt(252)
        hist["RSI"] = 100 - (100 / (1 + hist["Close"].pct_change().rolling(14).apply(
            lambda x: (x[x > 0].sum() / abs(x[x < 0].sum())) if abs(x[x < 0].sum()) > 0 else 0)))
        hist["Upper Band"] = hist["Close"].rolling(20).mean() + 2 * hist["Close"].rolling(20).std()
        hist["Lower Band"] = hist["Close"].rolling(20).mean() - 2 * hist["Close"].rolling(20).std()
        return info, hist

    info, hist = get_stock_data(selected)
    current_price = hist["Close"].iloc[-1]
    avg_volume = hist["Volume"].rolling(20).mean().iloc[-1]
    earnings = info.get("nextEarningsDate", "N/A")
    rsi = hist["RSI"].iloc[-1]

    # === Summary Metrics ===
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Price", f"${current_price:,.2f}")
    col2.metric("RSI", f"{rsi:.2f}")
    col3.metric("Vol vs Avg", f"{hist['Volume'].iloc[-1]:,.0f} / {avg_volume:,.0f}")
    col4.metric("Next Earnings", f"{earnings}")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("P/E", f"{info.get('trailingPE', 'N/A')}")
    col6.metric("EPS (Fwd)", f"{info.get('forwardEps', 'N/A')}")
    col7.metric("Div Yield", f"{(info.get('dividendYield') or 0)*100:.2f}%")
    col8.metric("Beta", f"{info.get('beta', 'N/A')}")

    st.markdown(f"**Sector:** {info.get('sector', 'N/A')}  |  **Industry:** {info.get('industry', 'N/A')}  |  **Exchange:** {info.get('exchange', 'N/A')}")
    st.markdown("---")

    def update_white_layout(fig, height=300):
        return fig.update_layout(
            paper_bgcolor="#1E1E2F",
            plot_bgcolor="#1E1E2F",
            font_color="white",
            title_font_color="white",
            xaxis=dict(color="white", showgrid=False),
            yaxis=dict(color="white", showgrid=False),
            legend=dict(font=dict(color="white")),
            hoverlabel=dict(bgcolor="#2A2D3A", font_color="white"),
            height=height
        )

    # === Price + SMA + Bollinger
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=hist.index, y=hist["Close"], name="Price", line=dict(color="cyan")))
    fig_price.add_trace(go.Scatter(x=hist.index, y=hist["SMA_50"], name="SMA 50", line=dict(dash="dot")))
    fig_price.add_trace(go.Scatter(x=hist.index, y=hist["SMA_200"], name="SMA 200", line=dict(dash="dot")))
    fig_price.add_trace(go.Scatter(x=hist.index, y=hist["Upper Band"], name="Upper Band", line=dict(color="gray")))
    fig_price.add_trace(go.Scatter(x=hist.index, y=hist["Lower Band"], name="Lower Band", line=dict(color="gray")))
    fig_price.update_layout(title="Price with SMA & Bollinger Bands")
    fig_price = update_white_layout(fig_price, height=350)

    # === RSI Chart
    fig_rsi = px.line(hist, y="RSI", title="Relative Strength Index (14)")
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
    fig_rsi = update_white_layout(fig_rsi)

    # === Volume Chart
    fig_vol = px.area(hist, y="Volume", title="Volume Trend")
    fig_vol = update_white_layout(fig_vol)

    # === Volatility
    fig_volatility = px.line(hist, y="Volatility", title="Annualized 30-day Volatility")
    fig_volatility = update_white_layout(fig_volatility)

    # === Radar
    radar_metrics = {
        "P/E": info.get("trailingPE") or 0,
        "P/B": info.get("priceToBook") or 0,
        "Yield": (info.get("dividendYield") or 0) * 100,
        "Beta": info.get("beta") or 0
    }
    fig_radar = go.Figure(data=go.Scatterpolar(
        r=list(radar_metrics.values()),
        theta=list(radar_metrics.keys()),
        fill='toself'
    ))
    fig_radar.update_layout(
        polar=dict(bgcolor="#1E1E2F", radialaxis=dict(visible=True, color="white")),
        paper_bgcolor="#1E1E2F", font_color="white", showlegend=False,
        title=dict(text="Valuation Radar", font=dict(color="white")),
        height=500
    )

    # === Layout
    colA, colB = st.columns(2)
    colA.plotly_chart(fig_price, use_container_width=True)
    colB.plotly_chart(fig_vol, use_container_width=True)

    colC, colD = st.columns(2)
    colC.plotly_chart(fig_rsi, use_container_width=True)
    colD.plotly_chart(fig_volatility, use_container_width=True)

    st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("---")
    st.success("Live data powered by Yahoo Finance. Use this dashboard to guide tactical decisions.")

    # Sector and PE Distribution only if available
    fig_sector, fig_pe = None, None
    if "Sector" in df.columns:
        sector_counts = df["Sector"].value_counts()
        fig_sector = px.pie(
            names=sector_counts.index,
            values=sector_counts.values,
            title="Sector Exposure"
        )
        fig_sector = update_white_layout(fig_sector, height=400)
        st.plotly_chart(fig_sector, use_container_width=True)

    if "P/E" in df.columns:
        pe_distribution = df["P/E"].dropna()
        fig_pe = px.histogram(
            pe_distribution,
            nbins=20,
            title="P/E Ratio Distribution",
            labels={"value": "P/E Ratio", "count": "Frequency"}
        )
        fig_pe = update_white_layout(fig_pe, height=400)
        st.plotly_chart(fig_pe, use_container_width=True)

    return fig_sector, fig_pe
