import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from fpdf import FPDF
from io import BytesIO
import tempfile
import zipfile
import plotly.io as pio

def render_export_tab(ticker_df):
    st.markdown("""
    <style>
    html, body, [class*="stApp"] {
        background-color: #1E1E2F;
        color: white;
        font-family: 'Montserrat', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #262637;
    }
    section[data-testid="stSidebar"] * {
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("Export Full Portfolio Report")

    tickers = ticker_df["ticker"].dropna().unique().tolist()

    @st.cache_data
    def collect_data(tickers):
        fundamentals = []
        technicals = []
        for t in tickers:
            try:
                stock = yf.Ticker(t)
                info = stock.info
                hist = stock.history(period="1y", auto_adjust=True)
                hist["SMA_50"] = hist["Close"].rolling(50).mean()
                hist["SMA_200"] = hist["Close"].rolling(200).mean()
                hist["Volatility"] = hist["Close"].pct_change().rolling(30).std() * np.sqrt(252)
                hist["RSI"] = 100 - (100 / (1 + hist["Close"].pct_change().rolling(14).apply(
                    lambda x: (x[x > 0].sum() / abs(x[x < 0].sum())) if abs(x[x < 0].sum()) > 0 else 0)))
                hist["Ticker"] = t
                hist.reset_index(inplace=True)
                # Make datetime columns timezone-naive
                for col in hist.select_dtypes(include=["datetime64[ns, UTC]"]).columns:
                    hist[col] = hist[col].dt.tz_localize(None)
                technicals.append(hist)

                fundamentals.append({
                    "Ticker": t,
                    "Sector": info.get("sector"),
                    "Industry": info.get("industry"),
                    "Exchange": info.get("exchange"),
                    "Market Cap": info.get("marketCap"),
                    "P/E": info.get("trailingPE"),
                    "Forward EPS": info.get("forwardEps"),
                    "Dividend Yield": info.get("dividendYield"),
                    "Beta": info.get("beta"),
                    "Price to Book": info.get("priceToBook"),
                    "52W High": info.get("fiftyTwoWeekHigh"),
                    "52W Low": info.get("fiftyTwoWeekLow")
                })
            except Exception:
                continue

        return pd.DataFrame(fundamentals), pd.concat(technicals, ignore_index=True)

    fundamentals_df, technicals_df = collect_data(tickers)

    # === Export to Excel ===
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        fundamentals_df.to_excel(writer, index=False, sheet_name="Fundamentals")
        technicals_df.to_excel(writer, index=False, sheet_name="Technicals")
        ticker_df.to_excel(writer, index=False, sheet_name="Original Input")

    excel_buffer.seek(0)

    # === Export to PDF ===
    def generate_pdf(fundamentals):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, "Portfolio Summary Report", ln=True, align='C')
        pdf.ln(10)

        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "Fundamentals Overview", ln=True)
        pdf.set_font("Arial", size=11)
        for _, row in fundamentals.iterrows():
            line = f"{row['Ticker']} | Sector: {row['Sector']} | P/E: {row['P/E']} | Yield: {(row['Dividend Yield'] or 0) * 100:.2f}%"
            pdf.multi_cell(0, 8, line)
        pdf.ln(5)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf.output(tmpfile.name)
            tmpfile.seek(0)
            pdf_bytes = tmpfile.read()

        return BytesIO(pdf_bytes)

    pdf_buffer = generate_pdf(fundamentals_df)

    # === ZIP All Files ===
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("portfolio_report.xlsx", excel_buffer.getvalue())
        zf.writestr("portfolio_summary.pdf", pdf_buffer.getvalue())
    zip_buffer.seek(0)

    st.markdown("### Download Portfolio Package")
    st.download_button(
        label="Download ZIP (Excel + PDF)",
        data=zip_buffer,
        file_name="full_portfolio_export.zip",
        mime="application/zip"
    )
