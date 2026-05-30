import yfinance as yf
from fastapi import HTTPException
from datetime import datetime


def get_stock_data(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    info = t.info

    if not info or info.get("trailingPegRatio") is None and info.get("currentPrice") is None and info.get("regularMarketPrice") is None and len(info) < 5:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found or no data available")

    price = (
        info.get("currentPrice")
        or info.get("regularMarketPrice")
        or info.get("previousClose")
        or 0.0
    )

    daily_change = info.get("regularMarketChangePercent") or 0.0

    company_name = info.get("longName") or info.get("shortName") or ticker
    currency = info.get("currency") or "USD"

    description = (
        info.get("longBusinessSummary")
        or info.get("description")
        or f"{company_name} — публично торгуемая компания."
    )
    # Обрезаем описание до разумного размера
    if len(description) > 500:
        description = description[:497] + "..."

    return {
        "ticker": ticker,
        "companyName": company_name,
        "price": float(price),
        "currency": currency,
        "dailyChangePercent": float(daily_change),
        "companyDescription": description,
    }


def get_price_history(ticker: str) -> list:
    t = yf.Ticker(ticker)
    hist = t.history(period="12d")

    if hist.empty:
        return []

    points = []
    for date_idx, row in hist.tail(8).iterrows():
        if hasattr(date_idx, 'strftime'):
            date_str = date_idx.strftime("%d.%m")
        else:
            date_str = str(date_idx)[:10]
        points.append({
            "date": date_str,
            "price": round(float(row["Close"]), 2)
        })

    return points
