import yfinance as yf
from datetime import datetime


def get_news(ticker: str) -> list:
    t = yf.Ticker(ticker)
    raw_news = t.news or []

    news_items = []
    for item in raw_news[:5]:
        # yfinance news может иметь разную структуру
        content = item.get("content", {}) if isinstance(item.get("content"), dict) else {}

        title = (
            content.get("title")
            or item.get("title")
            or "Без заголовка"
        )

        # timestamp → дата
        pub_ts = item.get("providerPublishTime") or content.get("pubDate") or ""
        if isinstance(pub_ts, (int, float)) and pub_ts > 0:
            published_at = datetime.fromtimestamp(pub_ts).strftime("%Y-%m-%d")
        elif isinstance(pub_ts, str) and pub_ts:
            published_at = pub_ts[:10]
        else:
            published_at = datetime.now().strftime("%Y-%m-%d")

        summary = (
            content.get("summary")
            or item.get("summary")
            or content.get("description")
            or item.get("description")
            or ""
        )

        url = (
            content.get("canonicalUrl", {}).get("url") if isinstance(content.get("canonicalUrl"), dict) else None
        ) or item.get("link") or item.get("url") or ""

        news_items.append({
            "title": title,
            "publishedAt": published_at,
            "summary": summary,
            "url": url,
        })

    return news_items
