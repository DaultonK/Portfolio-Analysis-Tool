def render_risk_classification_tab(df):
    import streamlit as st
    import pandas as pd
    import numpy as np
    import yfinance as yf
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    import plotly.express as px

    # === Dark Theme and Full White Styling ===
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
    .stRadio label, .stSelectbox label, .stMetric label, .stMetric div, .stMarkdown {
        color: white !important;
    }
    button[kind="primary"], button[kind="secondary"] {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("Portfolio Risk Classification")

    # === Introduction with Financial Education ===
    st.markdown("""
    **Understanding Portfolio Risk**

    Portfolio risk reflects how sensitive your investments are to market volatility. High-risk portfolios often include fast-growing or speculative stocks that may fluctuate significantly, while low-risk portfolios aim for stability and income.  
    Choosing the right risk level depends on your financial goals, time horizon, and personal tolerance for market swings.

    - **Low Risk**: Prioritizes capital preservation and income. Ideal for conservative investors or short-term goals.  
      *Pros*: Stability, lower drawdowns. *Cons*: Lower growth potential.

    - **Moderate Risk**: Balanced between growth and safety. Ideal for long-term investors who want steady progress without high volatility.  
      *Pros*: Balanced exposure. *Cons*: May underperform in bull markets, or overreact in downturns.

    - **High Risk**: Focuses on aggressive growth and innovation. Suitable for long horizons and higher return expectations.  
      *Pros*: High return potential. *Cons*: Sharp drawdowns, psychological stress.

    This tool will assess your portfolio’s risk classification and provide guidance to better align with your chosen investment profile.
    """)

    if "ticker" not in df.columns:
        st.error("The input data must contain a 'ticker' column.")
        return None, None

    tickers = df["ticker"].dropna().unique().tolist()
    desired_risk = st.radio("Select your desired risk level:", options=["Low", "Moderate", "High"], horizontal=True)

    @st.cache_data
    def fetch_features(tickers):
        data = []
        for t in tickers:
            try:
                ticker = yf.Ticker(t)
                info = ticker.info
                hist = ticker.history(period="6mo", auto_adjust=True)
                volatility = hist["Close"].pct_change().rolling(30).std().mean() * np.sqrt(252)
                beta = info.get("beta", np.nan)
                pe = info.get("trailingPE", np.nan)
                dividend = (info.get("dividendYield") or 0) * 100
                stddev = hist["Close"].std()
                data.append({
                    "ticker": t,
                    "Volatility": volatility,
                    "Beta": beta,
                    "P/E Ratio": pe,
                    "Dividend Yield": dividend,
                    "Price Std Dev": stddev
                })
            except:
                continue
        return pd.DataFrame(data).dropna()

    feature_df = fetch_features(tickers)

    if feature_df.empty:
        st.warning("No valid financial data could be retrieved. Please check your ticker symbols.")
        return None, None

    def label_risk(row):
        score = 0
        if row["Volatility"] > 0.35 or row["Beta"] > 1.2: score += 2
        if row["P/E Ratio"] > 30: score += 1
        if row["Dividend Yield"] < 1: score += 1
        return "High" if score >= 3 else "Moderate" if score == 2 else "Low"

    feature_df["Risk"] = feature_df.apply(label_risk, axis=1)

    X = feature_df[["Volatility", "Beta", "P/E Ratio", "Dividend Yield", "Price Std Dev"]]
    y = feature_df["Risk"]
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y_encoded)
    feature_df["Predicted Risk"] = le.inverse_transform(model.predict(X))
    portfolio_risk = feature_df["Predicted Risk"].value_counts().idxmax()

    avg_vol = feature_df["Volatility"].mean()
    avg_beta = feature_df["Beta"].mean()
    avg_pe = feature_df["P/E Ratio"].mean()
    avg_yield = feature_df["Dividend Yield"].mean()

    st.markdown("### Portfolio Risk Summary")
    left, right = st.columns(2)

    with left:
        st.metric("Predicted Risk", portfolio_risk)
        st.markdown(f"**Average Volatility:** {avg_vol:.2f}")
        st.markdown(f"**Average Beta:** {avg_beta:.2f}")
        st.markdown(f"**Average P/E Ratio:** {avg_pe:.2f}")
        st.markdown(f"**Average Dividend Yield:** {avg_yield:.2f}%")

    with right:
        risk_distribution = feature_df["Predicted Risk"].value_counts().reset_index()
        risk_distribution.columns = ["Risk Level", "Count"]
        fig_risk_dist = px.pie(
            risk_distribution,
            names="Risk Level",
            values="Count",
            title="Risk Composition",
            color_discrete_map={"Low": "#2ca02c", "Moderate": "#ff7f0e", "High": "#d62728"}
        )
        fig_risk_dist.update_layout(
            paper_bgcolor="#1E1E2F",
            font_color="white",
            title_font_color="white",
            legend=dict(font=dict(color="white"))
        )
        st.plotly_chart(fig_risk_dist, use_container_width=True)

    # === Risk Guidance ===
    if desired_risk != portfolio_risk:
        st.warning(f"Your portfolio risk does not match your selected target of '{desired_risk}'.")
        st.subheader("Recommendations to Align with Your Risk Target")
        if desired_risk == "Low":
            st.markdown("- Reduce exposure to high-beta or high-volatility stocks.")
            st.markdown("- Increase allocation to dividend-paying or value-oriented assets.")
            st.markdown("- Rebalance toward diversified, lower-risk sectors.")
        elif desired_risk == "Moderate":
            st.markdown("- Aim for a blend of growth and defensive stocks.")
            st.markdown("- Avoid clusters of speculative positions.")
        elif desired_risk == "High":
            st.markdown("- Increase allocation to high-growth, high-beta assets.")
            st.markdown("- Consider sector tilts toward technology or emerging markets.")
    else:
        st.success("Your portfolio risk is in line with your selected target.")

    # === Stock-Level Risk Breakdown
    safest = feature_df[feature_df["Predicted Risk"] == "Low"].nsmallest(3, "Volatility")
    riskiest = feature_df[feature_df["Predicted Risk"] == "High"].nlargest(3, "Volatility")

    def display_stock_cards(df_subset):
        for _, row in df_subset.iterrows():
            st.markdown(f"""
            <div style='border:1px solid #444;padding:10px;border-radius:10px;margin-bottom:10px'>
                <strong>{row['ticker']}</strong><br>
                Volatility: {row['Volatility']:.2f}<br>
                Beta: {row['Beta']:.2f}<br>
                P/E Ratio: {row['P/E Ratio']:.2f}<br>
                Dividend Yield: {row['Dividend Yield']:.2f}%
            </div>
            """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Safest Holdings**")
        display_stock_cards(safest)

    with col2:
        st.markdown("**Riskiest Holdings**")
        display_stock_cards(riskiest)

    # === Return Key Metrics and Chart ===
    key_metrics = {
        "Avg Beta": f"{avg_beta:.2f}" if not pd.isna(avg_beta) else "N/A",
        "Avg Dividend Yield": f"{avg_yield:.2f}%" if not pd.isna(avg_yield) else "N/A"
    }

    fig_volatility = px.scatter(
        feature_df,
        x="Beta",
        y="Volatility",
        size="Price Std Dev",
        color="Risk",
        hover_name="ticker",
        title="Volatility vs Beta",
        labels={"Beta": "Beta", "Volatility": "Volatility (Annualized)"}
    )
    fig_volatility.update_layout(
        paper_bgcolor="#1E1E2F",
        font_color="white",
        title_font_color="white",
        legend=dict(font=dict(color="white")),
        xaxis=dict(color="white"),
        yaxis=dict(color="white")
    )

    st.plotly_chart(fig_volatility, use_container_width=True)

    return key_metrics, fig_volatility
