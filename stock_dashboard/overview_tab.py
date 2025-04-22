import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import numpy as np
import pandas as pd
from stock_dashboard.Get_stock_region import stock_region_diversification

def render_overview_tab(df):
    st.title("Portfolio Overview")

    # ----- STYLING -----
    st.markdown("""
    <style>
    html, body, [class*="stApp"] {
        font-family: 'Montserrat', sans-serif !important;
        background-color: #1C1C24 !important;
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #262637 !important;
    }
    h1, h2, h3, h4, h5, h6, p, div, span {
        color: #FFFFFF !important;
    }
    .metric-inline {
        font-size: 15px;
        font-weight: 500;
        padding: 6px 12px;
        margin-right: 16px;
        border-radius: 6px;
        background-color: rgba(255, 255, 255, 0.04);
        display: inline-block;
    }
    .metric-label {
        color: #AAAAAA;
        margin-right: 4px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ----- CALCULATIONS -----
    df = df.copy()
    df["prev_close"] = df["ticker"].apply(lambda t: yf.Ticker(t).info.get("previousClose", np.nan))
    df["daily_change_pct"] = ((df["price"] - df["prev_close"]) / df["prev_close"]) * 100
    portfolio_daily_change = np.average(df["daily_change_pct"], weights=df["value"])

    @st.cache_data
    def get_volatility(ticker):
        try:
            hist = yf.Ticker(ticker).history(period="30d")
            returns = hist["Close"].pct_change().dropna()
            return np.std(returns)
        except:
            return np.nan
    df["volatility"] = df["ticker"].apply(get_volatility)
    portfolio_volatility = np.average(df["volatility"], weights=df["value"])

    df["div_yield"] = df["ticker"].apply(lambda t: yf.Ticker(t).info.get("dividendYield", 0))
    weighted_div_yield = np.average(df["div_yield"].fillna(0), weights=df["value"])

    @st.cache_data
    def get_sectors(tickers):
        sector_map = {}
        for ticker in tickers:
            try:
                info = yf.Ticker(ticker).info
                sector_map[ticker] = info.get("sector", "Unknown")
            except:
                sector_map[ticker] = "Unknown"
        return sector_map
    sector_map = get_sectors(df["ticker"].tolist())
    df["sector"] = df["ticker"].map(sector_map)
    sector_count = df["sector"].nunique()
    top_holding = df.loc[df['value'].idxmax()]["ticker"] if not df.empty else "N/A"

    # ----- METRICS INLINE -----
    st.markdown(f"""
    <div style="margin-top: 10px; margin-bottom: 30px;">
        <div class="metric-inline"><span class="metric-label">Total Value:</span> ${df["value"].sum():,.2f}</div>
        <div class="metric-inline"><span class="metric-label">Holdings:</span> {len(df)}</div>
        <div class="metric-inline"><span class="metric-label">Top Holding:</span> {top_holding}</div>
        <div class="metric-inline"><span class="metric-label">Daily Change:</span> {portfolio_daily_change:.2f}%</div>
        <div class="metric-inline"><span class="metric-label">Volatility:</span> {portfolio_volatility:.2%}</div>
        <div class="metric-inline"><span class="metric-label">Dividend Yield:</span> {weighted_div_yield * 100:.2f}%</div>
        <div class="metric-inline"><span class="metric-label">Sectors:</span> {sector_count}</div>
    </div>
    """, unsafe_allow_html=True)

    # ----- CHART STYLING -----
    def update_plot_style(fig):
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            legend=dict(font=dict(color='white')),
            title_font=dict(color='white'),
            hoverlabel=dict(bgcolor='black', font_size=14, font_color='white'),
        )
        fig.update_xaxes(color='white')
        fig.update_yaxes(color='white')
        return fig

    # ----- ALLOCATION CHART -----
    fig_alloc = px.pie(df, values="value", names="ticker", title="Allocation by Ticker")
    fig_alloc = update_plot_style(fig_alloc)

    # ----- REGIONAL DIVERSIFICATION -----
    tickers_qty = dict(zip(df["ticker"], df["quantity"]))
    region_data = stock_region_diversification(tickers_qty)
    if isinstance(region_data, dict):
        fig_region = px.pie(
            names=list(region_data.keys()),
            values=list(region_data.values()),
            hole=0.4,
            title="Regional Diversification"
        )
        fig_region = update_plot_style(fig_region)
    else:
        fig_region = None

    # ----- SECTOR ALLOCATION -----
    sector_group = df.groupby("sector")["value"].sum().reset_index().sort_values("value", ascending=False)
    fig_sector = px.pie(sector_group, names="sector", values="value", hole=0.4, title="Sector Allocation")
    fig_sector = update_plot_style(fig_sector)

    # ----- HISTORICAL PORTFOLIO PERFORMANCE -----
    @st.cache_data(show_spinner=True)
    def get_historical_values(tickers, qty_dict):
        hist_df = pd.DataFrame()
        for ticker in tickers:
            try:
                hist = yf.Ticker(ticker).history(period="30d")["Close"]
                hist_df[ticker] = hist * qty_dict[ticker]
            except:
                continue
        hist_df["portfolio"] = hist_df.sum(axis=1)
        spy = yf.Ticker("SPY").history(period="30d")["Close"]
        combined = pd.DataFrame({
            "Date": hist_df.index,
            "Portfolio Value": hist_df["portfolio"] / hist_df["portfolio"].iloc[0],
            "S&P 500 (SPY)": spy / spy.iloc[0]
        }).dropna()
        return combined

    hist_chart_data = get_historical_values(df["ticker"].tolist(), tickers_qty)
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(
        x=hist_chart_data["Date"],
        y=hist_chart_data["Portfolio Value"],
        mode='lines',
        name="Portfolio",
        hovertemplate='Date: %{x|%b %d}<br>Value: %{y:.2f}<extra></extra>'
    ))
    fig_hist.add_trace(go.Scatter(
        x=hist_chart_data["Date"],
        y=hist_chart_data["S&P 500 (SPY)"],
        mode='lines',
        name="S&P 500",
        line=dict(dash='dash'),
        hovertemplate='Date: %{x|%b %d}<br>S&P 500: %{y:.2f}<extra></extra>'
    ))
    fig_hist.update_layout(
        title="Portfolio vs S&P 500 (30-Day Normalized)",
        xaxis_title="Date",
        yaxis_title="Normalized Value",
    )
    update_plot_style(fig_hist)

    # ----- CHART LAYOUT -----
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Allocation by Ticker")
        st.plotly_chart(fig_alloc, use_container_width=True)

    with col2:
        st.subheader("Regional Diversification")
        if fig_region:
            st.plotly_chart(fig_region, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Sector Allocation")
        st.plotly_chart(fig_sector, use_container_width=True)

    with col4:
        st.subheader("Portfolio vs S&P 500")
        st.plotly_chart(fig_hist, use_container_width=True)

    return fig_alloc, fig_region, df["value"].sum()
