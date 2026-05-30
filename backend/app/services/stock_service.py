import httpx
from fastapi import HTTPException

from app.config import MARKET_DATA_TIMEOUT

STOOQ_DAILY_URL = "https://stooq.com/q/d/l/"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
YAHOO_QUOTE_SUMMARY_URL = "https://query2.finance.yahoo.com/v10/finance/quoteSummary/{ticker}"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 AI-Investment-Assistant/1.0",
    "Accept": "application/json",
}

KNOWN_COMPANY_DESCRIPTIONS = {
    "AAPL": (
        "Apple Inc. разрабатывает и продает смартфоны iPhone, компьютеры Mac, планшеты iPad, "
        "носимые устройства, программное обеспечение и цифровые сервисы. Компания зарабатывает "
        "на экосистеме устройств, App Store, подписках и сервисах, а ее результаты сильно зависят "
        "от спроса на премиальную электронику и обновления продуктовой линейки."
    ),
    "MSFT": (
        "Microsoft Corporation разрабатывает корпоративное программное обеспечение, облачные сервисы Azure, "
        "Windows, Microsoft 365, игровые продукты и AI-инструменты. Ключевые драйверы компании — облачная "
        "инфраструктура, подписочная модель и внедрение искусственного интеллекта в продукты для бизнеса."
    ),
    "TSLA": (
        "Tesla, Inc. производит электромобили, аккумуляторные системы, энергетические решения и развивает "
        "технологии автономного вождения. На результаты компании влияют спрос на электромобили, ценовая "
        "конкуренция, производственные объемы и ожидания по будущим технологиям."
    ),
    "NVDA": (
        "NVIDIA Corporation проектирует графические процессоры, ускорители для дата-центров и платформы "
        "для искусственного интеллекта. Основной фокус инвесторов — спрос на AI-чипы, дата-центры, "
        "маржинальность и конкуренция на рынке полупроводников."
    ),
    "AMZN": (
        "Amazon.com, Inc. развивает электронную коммерцию, облачную платформу AWS, рекламу, подписки и "
        "логистическую инфраструктуру. На бизнес влияют потребительский спрос, облачные расходы компаний "
        "и эффективность операционных затрат."
    ),
    "GOOGL": (
        "Alphabet Inc. владеет Google, YouTube, рекламными платформами, облачным бизнесом Google Cloud "
        "и AI-направлениями. Главные факторы для оценки — рекламный рынок, конкуренция в поиске, "
        "облачный рост и расходы на искусственный интеллект."
    ),
    "META": (
        "Meta Platforms, Inc. управляет Facebook, Instagram, WhatsApp и Threads, а также инвестирует "
        "в искусственный интеллект и VR/AR-направления. Бизнес зависит от рекламного рынка, вовлеченности "
        "пользователей, регулирования данных и эффективности AI-инвестиций."
    ),
}


def _fetch_chart(ticker: str, range_value: str = "1mo") -> dict:
    try:
        response = httpx.get(
            YAHOO_CHART_URL.format(ticker=ticker),
            params={
                "range": range_value,
                "interval": "1d",
                "includePrePost": "false",
                "events": "div,splits",
            },
            headers=REQUEST_HEADERS,
            timeout=MARKET_DATA_TIMEOUT,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch live stock data for '{ticker}': {exc}",
        ) from exc

    data = response.json()
    result = data.get("chart", {}).get("result") or []
    error = data.get("chart", {}).get("error")
    if error:
        raise HTTPException(status_code=502, detail=error.get("description", "Yahoo Finance error"))
    if not result:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found or no live data available")

    return result[0]


def _format_date(timestamp: int) -> str:
    from datetime import datetime

    return datetime.fromtimestamp(timestamp).strftime("%d.%m")


def _format_stooq_symbol(ticker: str) -> str:
    if "." in ticker:
        return ticker.lower()
    return f"{ticker.lower()}.us"


def _parse_stooq_csv(text: str) -> list:
    import csv
    from io import StringIO

    reader = csv.DictReader(StringIO(text))
    rows = []
    for row in reader:
        if row.get("Close") in (None, "", "N/D"):
            continue
        date_value = row["Date"]
        rows.append({
            "date": f"{date_value[8:10]}.{date_value[5:7]}",
            "price": round(float(row["Close"]), 2),
        })
    return rows


def _fetch_stooq_history(ticker: str) -> list:
    try:
        response = httpx.get(
            STOOQ_DAILY_URL,
            params={"s": _format_stooq_symbol(ticker), "i": "d"},
            headers=REQUEST_HEADERS,
            timeout=MARKET_DATA_TIMEOUT,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch live stock data for '{ticker}' from Stooq: {exc}",
        ) from exc

    points = _parse_stooq_csv(response.text)
    if not points:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found in live data providers")
    return points


def _fetch_company_profile(ticker: str) -> dict:
    try:
        response = httpx.get(
            YAHOO_QUOTE_SUMMARY_URL.format(ticker=ticker),
            params={"modules": "assetProfile,summaryProfile,price"},
            headers=REQUEST_HEADERS,
            timeout=MARKET_DATA_TIMEOUT,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return {}

    result = response.json().get("quoteSummary", {}).get("result") or []
    if not result:
        return {}

    data = result[0]
    return {
        **(data.get("assetProfile") or {}),
        **(data.get("summaryProfile") or {}),
        "price": data.get("price") or {},
    }


def _build_company_description(company_name: str, ticker: str, profile: dict) -> str:
    if ticker in KNOWN_COMPANY_DESCRIPTIONS:
        return KNOWN_COMPANY_DESCRIPTIONS[ticker]

    sector = profile.get("sector")
    industry = profile.get("industry")
    country = profile.get("country")
    website = profile.get("website")
    employees = profile.get("fullTimeEmployees")

    parts = [f"{company_name} ({ticker}) — публичная компания"]
    if sector:
        parts.append(f"из сектора {sector}")
    if industry:
        parts.append(f"в отрасли {industry}")
    if country:
        parts.append(f"с основным присутствием в {country}")

    description = " ".join(parts) + "."
    if employees:
        description += f" В компании работает около {employees:,}".replace(",", " ") + " сотрудников."
    if website:
        description += f" Официальный сайт: {website}."

    if not profile:
        description += " Подробный профиль временно недоступен у внешнего источника, но цена и динамика берутся из live-рыночных данных."

    return description


def get_stock_data(ticker: str) -> dict:
    try:
        chart = _fetch_chart(ticker, "5d")
        meta = chart.get("meta", {})
        quote = (chart.get("indicators", {}).get("quote") or [{}])[0]
        closes = [value for value in quote.get("close", []) if value is not None]

        price = meta.get("regularMarketPrice")
        if price is None and closes:
            price = closes[-1]
        if price is None:
            raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found or no live price available")

        previous_close = meta.get("chartPreviousClose")
        if previous_close:
            daily_change = ((float(price) - float(previous_close)) / float(previous_close)) * 100
        elif len(closes) >= 2 and closes[-2]:
            daily_change = ((float(closes[-1]) - float(closes[-2])) / float(closes[-2])) * 100
        else:
            daily_change = 0.0

        company_name = meta.get("longName") or meta.get("shortName") or meta.get("symbol") or ticker
        currency = meta.get("currency") or "USD"
    except HTTPException as yahoo_error:
        points = _fetch_stooq_history(ticker)
        price = points[-1]["price"]
        previous_price = points[-2]["price"] if len(points) >= 2 else price
        daily_change = ((price - previous_price) / previous_price) * 100 if previous_price else 0.0
        company_name = ticker
        currency = "USD"

        if yahoo_error.status_code not in (404, 502):
            raise

    profile = _fetch_company_profile(ticker)
    if profile.get("price", {}).get("longName"):
        company_name = profile["price"]["longName"]
    elif profile.get("price", {}).get("shortName"):
        company_name = profile["price"]["shortName"]

    description = _build_company_description(company_name, ticker, profile)

    return {
        "ticker": ticker,
        "companyName": company_name,
        "price": float(price),
        "currency": currency,
        "dailyChangePercent": float(daily_change),
        "companyDescription": description,
    }


def get_price_history(ticker: str) -> list:
    try:
        chart = _fetch_chart(ticker, "1mo")
        timestamps = chart.get("timestamp") or []
        quote = (chart.get("indicators", {}).get("quote") or [{}])[0]
        closes = quote.get("close") or []

        points = []
        for timestamp, close in zip(timestamps, closes):
            if close is None:
                continue
            points.append({
                "date": _format_date(timestamp),
                "price": round(float(close), 2),
            })
    except HTTPException:
        points = _fetch_stooq_history(ticker)

    return points[-8:]
