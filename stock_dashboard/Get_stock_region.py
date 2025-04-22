import yfinance as yf
from typing import Dict

def get_stock_region(ticker: str) -> str:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        exchange = info.get("exchange", "").lower()

        region_map = {
    "American Stock": [
        "nasdaq", "nyse", "amex", "arca", "pcx", "nms", "nyq", "snp", "cboe", "bats", "tsx", "tsxv", "cse", "ne"
    ],
    "European Stock": [
        "lse", "euronext", "xetra", "bme", "six", "fra", "ams", "par", "mil", "lis", "vse", "omx", "wse", "prague",
        "athens", "budapest", "bvx", "micex", "moex", "hel", "sto", "oslo", "dublin", "bolsa-madrid","ger","ebs"
    ],
    "Asian Stock": [
        "tse", "sse", "hkex", "kospi", "kosdaq", "nse", "bse", "szse", "taiex", "jpxt", "hsi", "idx", "pse",
        "bursa-malaysia", "set", "hkg", "jpx", "tky", "sto", "shanghai", "shenzhen", "taipei", "karachi", "dhaka","ksc","nsi"
    ],
    "Other/Unknown Region": [
        "asx", "nzx", "jse", "bvc", "bmv", "b3", "bovespa", "safex", "adx", "dfm", "tadawul", "qse", "egx", "casablanca",
        "nairobi", "lagos", "muscat", "doha", "kuwait", "manama", "colombia", "peru", "chile", "argentina"
    ]
}

        for region, exchanges in region_map.items():
            if any(ex in exchange for ex in exchanges):
                return region

        return f"Other/Unknown Region (Exchange: {exchange})"

    except Exception as e:
        return f"Error fetching data for {ticker}: {e}"

def stock_region_diversification(tickers_with_quantity: Dict[str, int]) -> Dict[str, float]:
    try:
        if not tickers_with_quantity:
            raise ValueError("Input tickers_with_quantity is empty.")

        region_totals = {}
        total_investment = 0

        for ticker, quantity in tickers_with_quantity.items():
            stock = yf.Ticker(ticker)
            current_price = stock.info.get("regularMarketPrice", 0)
            if current_price <= 0:
                continue

            investment = current_price * quantity
            total_investment += investment

            region = get_stock_region(ticker)
            if region not in region_totals:
                region_totals[region] = 0
            region_totals[region] += investment

        if total_investment == 0:
            return {"Error": "Total investment is zero. Cannot calculate diversification."}

        region_percentages = {
            region: (amount / total_investment) * 100
            for region, amount in region_totals.items()
        }

        return region_percentages

    except Exception as e:
        return {"Error": f"Error calculating diversification: {e}"}