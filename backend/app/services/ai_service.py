import httpx
from app.config import WELLFLOW_API_KEY, WELLFLOW_BASE_URL, WELLFLOW_MODEL

POSITIVE_KEYWORDS = [
    "рост", "растет", "расширяет", "развитие", "стабильн",
    "усиливает", "поддерж", "спрос", "выручк", "производство",
    "сильн", "интерес инвесторов", "покупк", "новая позици",
    "повысили оценку", "целевую цену",
    "growth", "expand", "revenue", "profit", "strong", "positive",
    "record", "beat", "surge", "gain", "rise", "increase",
    "purchase", "buy", "buys", "bought", "stake", "new position",
    "opens new position", "upgrade", "upgraded", "outperform",
    "price target", "bullish", "rally", "innovation", "ai",
    "artificial intelligence", "partnership", "launch",
]

NEGATIVE_KEYWORDS = [
    "снижа", "слаб", "риск", "давлен", "конкурен",
    "затрат", "расход", "марж", "огранич", "предупреж",
    "доходност", "ставк", "юридич", "регулятор", "волатильн",
    "понизили оценку",
    "decline", "drop", "fall", "loss", "weak", "miss",
    "concern", "risk", "cut", "layoff", "lawsuit", "fine",
    "downgrade", "downgraded", "bearish", "sell rating",
    "probe", "investigation", "antitrust", "treasury yield",
    "yield approaching", "rates", "5%", "pressure", "volatility",
    "uncertainty", "tariff", "not be",
]


def _count_hits(text: str, keywords: list) -> int:
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


def infer_news_impact(news_item: dict) -> str:
    if news_item.get("impact") in ("positive", "negative", "neutral"):
        return news_item["impact"]

    text = " ".join([
        news_item.get("title", ""),
        news_item.get("originalTitle", ""),
        news_item.get("summary", ""),
        news_item.get("impactReason", ""),
    ])

    pos = _count_hits(text, POSITIVE_KEYWORDS)
    neg = _count_hits(text, NEGATIVE_KEYWORDS)

    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def _build_impact_reason(news_item: dict, impact: str) -> str:
    if news_item.get("impactReason"):
        return news_item["impactReason"]
    if impact == "positive":
        return "Новость может поддержать ожидания по выручке, спросу или операционной устойчивости."
    if impact == "negative":
        return "Новость указывает на риск для спроса, маржинальности или конкурентной позиции."
    return "Новость важна для контекста, но не даёт сильного положительного или отрицательного сигнала."


def enrich_news(news_items: list) -> list:
    enriched = []
    for item in news_items:
        impact = infer_news_impact(item)
        enriched.append({
            **item,
            "impact": impact,
            "impactReason": _build_impact_reason(item, impact),
        })
    return enriched


def _get_trend_label(price_history: list) -> str:
    if len(price_history) < 2:
        return "недостаточно данных по динамике цены"
    first = price_history[0]["price"] if isinstance(price_history[0], dict) else price_history[0].price
    last = price_history[-1]["price"] if isinstance(price_history[-1], dict) else price_history[-1].price
    if first == 0:
        return "недостаточно данных по динамике цены"
    pct = ((last - first) / first) * 100
    if pct >= 2:
        return f"цена за период выросла примерно на {pct:.1f}%"
    if pct <= -2:
        return f"цена за период снизилась примерно на {abs(pct):.1f}%"
    return "цена за период двигалась без резкого отклонения"


def _build_keyword_analysis(stock: dict, news: list) -> str:
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    for n in news:
        impact = n.get("impact", "neutral")
        counts[impact] = counts.get(impact, 0) + 1

    if counts["positive"] > counts["negative"]:
        mood = "умеренно позитивной"
    elif counts["negative"] > counts["positive"]:
        mood = "осторожной"
    else:
        mood = "смешанной"

    daily = stock.get("dailyChangePercent", 0)
    if daily > 0:
        daily_label = f"дневное изменение положительное: +{daily:.2f}%"
    elif daily < 0:
        daily_label = f"дневное изменение отрицательное: {daily:.2f}%"
    else:
        daily_label = "дневное изменение около нуля"

    trend = _get_trend_label(stock.get("priceHistory", []))

    pos_titles = [n["title"] for n in news if n.get("impact") == "positive"][:2]
    neg_titles = [n["title"] for n in news if n.get("impact") == "negative"][:2]

    pos_text = "; ".join(pos_titles) if pos_titles else "явных позитивных новостей нет"
    neg_text = "; ".join(neg_titles) if neg_titles else "сильных негативных сигналов нет"

    return (
        f"{stock['companyName']} ({stock['ticker']}) выглядит {mood}: "
        f"{daily_label}, {trend}. "
        f"В новостях: {counts['positive']} положительных, "
        f"{counts['negative']} отрицательных и {counts['neutral']} нейтральных сигналов. "
        f"Позитивные факторы: {pos_text}. "
        f"Риски: {neg_text}. "
        f"Итог: ситуацию стоит рассматривать как краткую аналитическую справку; "
        f"это не является рекомендацией покупать или продавать ценные бумаги."
    )


def _build_wellflow_analysis(stock: dict, news: list) -> str:
    news_lines = "\n".join(
        f"- [{n.get('impact','neutral').upper()}] {n.get('title','')}: {n.get('summary','')}"
        for n in news
    )

    prompt = (
        f"Ты финансовый аналитический ассистент. Сформируй краткую аналитическую справку по акции.\n\n"
        f"Входные данные:\n"
        f"- Тикер: {stock['ticker']}\n"
        f"- Компания: {stock['companyName']}\n"
        f"- Текущая цена: {stock['price']} {stock['currency']}\n"
        f"- Дневное изменение: {stock['dailyChangePercent']:.2f}%\n"
        f"- Описание: {stock.get('companyDescription', '')}\n"
        f"- Новости:\n{news_lines}\n\n"
        f"Требования:\n"
        f"1. Пиши на русском языке.\n"
        f"2. Объём: 100-200 слов.\n"
        f"3. Укажи общую оценку ситуации.\n"
        f"4. Назови ключевые позитивные факторы.\n"
        f"5. Назови риски.\n"
        f"6. Не давай рекомендацию купить, продать или держать акцию.\n"
        f"7. В конце явно напиши, что это аналитическая справка, а не инвестиционная рекомендация."
    )

    response = httpx.post(
        f"{WELLFLOW_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {WELLFLOW_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": WELLFLOW_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 400,
            "temperature": 0.5,
        },
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def build_ai_analysis(stock: dict, news: list) -> str:
    if WELLFLOW_API_KEY:
        try:
            return _build_wellflow_analysis(stock, news)
        except Exception:
            pass
    return _build_keyword_analysis(stock, news)
