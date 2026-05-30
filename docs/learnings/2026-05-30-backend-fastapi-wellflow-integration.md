# Как устроен backend: полный разбор реализации

Это документ для изучения. Здесь объяснён каждый файл backend'а — что он делает, почему написан именно так, и какие концепции за этим стоят.

---

## Общая картина: как данные проходят через backend

Когда пользователь вводит `AAPL` и нажимает «Анализ», происходит следующее:

```
Браузер (frontend)
  → GET http://localhost:8001/api/analyze/AAPL
    → main.py принимает запрос
      → stock_service.py  запрашивает Yahoo Finance (цена, описание)
      → stock_service.py  запрашивает Yahoo Finance (история цен)
      → news_service.py   запрашивает Yahoo Finance (новости)
      → ai_service.py     анализирует новости + строит текст через WellFlow или keywords
    → main.py собирает всё в один JSON
  → Браузер получает готовый ответ и отображает данные
```

Backend — это **прослойка**: он сам не хранит данных, а собирает их из разных источников и возвращает в едином формате.

---

## Файл 1: `requirements.txt` — зависимости проекта

```
fastapi
uvicorn[standard]
python-dotenv
httpx
yfinance
```

**Что каждая библиотека делает:**

| Библиотека | Назначение |
|---|---|
| `fastapi` | Фреймворк для создания API. Принимает HTTP-запросы, вызывает твои функции, возвращает JSON |
| `uvicorn[standard]` | Сервер, который запускает FastAPI. Без него приложение не будет слушать запросы |
| `python-dotenv` | Читает файл `.env` и загружает переменные окружения (API-ключи) |
| `httpx` | HTTP-клиент для Python — делает запросы к внешним API (WellFlow) |
| `yfinance` | Обёртка над Yahoo Finance — получает данные акций, новости, историю цен |

**Почему именно эти, а не другие?**
- `fastapi` выбран потому что он современный, быстрый и автоматически генерирует документацию по адресу `/docs`
- `yfinance` — бесплатный, без API-ключа, достаточно для MVP
- `httpx` вместо `requests` — поддерживает async, лучше интегрируется с FastAPI

---

## Файл 2: `app/config.py` — переменные окружения

```python
import os
from dotenv import load_dotenv

load_dotenv()

WELLFLOW_API_KEY = os.getenv("WELLFLOW_API_KEY", "")
WELLFLOW_BASE_URL = "https://api.wellflow.dev/v1"
WELLFLOW_MODEL = "claude-haiku-4.5"
```

**Что происходит строка за строкой:**

`load_dotenv()` — читает файл `.env` в папке проекта и добавляет его содержимое как переменные окружения. После этого можно читать их через `os.getenv`.

`os.getenv("WELLFLOW_API_KEY", "")` — читает переменную `WELLFLOW_API_KEY`. Второй аргумент `""` — значение по умолчанию если переменная не задана. Благодаря этому приложение не падает когда `.env` не существует.

**Почему ключи хранятся в `.env`, а не прямо в коде?**

Если ты напишешь ключ в коде и закоммитишь — он попадёт в git-историю навсегда, даже если потом удалишь. Файл `.env` добавлен в `.gitignore` и никогда не попадает в репозиторий. `.env.example` — шаблон без реальных значений, его коммитить можно.

---

## Файл 3: `app/models.py` — структуры данных

```python
from pydantic import BaseModel
from typing import List, Optional


class NewsItem(BaseModel):
    title: str
    publishedAt: str
    summary: str
    url: Optional[str] = None
    impact: str = "neutral"
    impactReason: str = ""


class PricePoint(BaseModel):
    date: str
    price: float


class StockResponse(BaseModel):
    ticker: str
    companyName: str
    price: float
    currency: str
    dailyChangePercent: float
    priceHistory: List[PricePoint] = []
    companyDescription: str
    news: List[NewsItem] = []
    aiAnalysis: str
```

**Что такое Pydantic и зачем нужны эти классы?**

Pydantic — библиотека для описания структур данных с автоматической валидацией. Когда ты пишешь `class StockResponse(BaseModel)` — ты описываешь какой именно JSON вернёт backend.

FastAPI использует эти классы для двух вещей:
1. **Валидация** — если в `StockResponse` поле `price` объявлено как `float`, FastAPI не позволит вернуть строку вместо числа
2. **Документация** — по адресу `http://localhost:8001/docs` автоматически появится описание всех полей

**Почему поля называются `companyName`, а не `company_name`?**

Frontend (`app.js`) ожидает поля в формате camelCase — именно так принято в JavaScript. Python обычно использует snake_case. Мы сознательно назвали поля в camelCase прямо в Pydantic-модели, чтобы не делать дополнительных преобразований. Это важное архитектурное решение — если переименовать хоть одно поле, frontend перестанет его видеть без каких-либо ошибок.

**Что означает `Optional[str] = None`?**

`Optional[str]` значит что поле может быть строкой или `None` (отсутствовать). `= None` — значение по умолчанию. Для `url` у новости это важно: не все новости имеют ссылку на источник.

**Что означает `List[PricePoint] = []`?**

`List[PricePoint]` — список объектов типа `PricePoint`. `= []` — если история цен не пришла, поле будет пустым списком, а не вызовет ошибку.

---

## Файл 4: `app/services/stock_service.py` — данные акции

```python
import yfinance as yf
from fastapi import HTTPException


def get_stock_data(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    info = t.info

    if not info or ... len(info) < 5:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")

    price = (
        info.get("currentPrice")
        or info.get("regularMarketPrice")
        or info.get("previousClose")
        or 0.0
    )

    daily_change = info.get("regularMarketChangePercent") or 0.0
    company_name = info.get("longName") or info.get("shortName") or ticker
    currency = info.get("currency") or "USD"

    description = info.get("longBusinessSummary") or f"{company_name} — публично торгуемая компания."
    if len(description) > 500:
        description = description[:497] + "..."

    return {
        "ticker": ticker,
        "companyName": company_name,
        "price": float(price),
        ...
    }
```

**Как работает `yfinance`:**

```python
t = yf.Ticker("AAPL")   # создаём объект для тикера
t.info                   # словарь с ~100 полями: цена, объём, P/E, описание...
t.history(period="10d")  # DataFrame с историей цен за последние 10 дней
t.news                   # список последних новостей
```

`yfinance` парсит публичные страницы Yahoo Finance. Это бесплатно, но иногда нестабильно — поля могут отсутствовать или называться по-разному для разных тикеров. Именно поэтому везде стоит `or` — цепочка fallback-значений.

**Почему используется `or` вместо `if`?**

```python
# Длинный способ:
if info.get("currentPrice") is not None:
    price = info.get("currentPrice")
elif info.get("regularMarketPrice") is not None:
    price = info.get("regularMarketPrice")
else:
    price = 0.0

# Короткий способ через or:
price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
```

В Python `or` возвращает первое «правдивое» значение. `None` и `0` считаются «ложными», поэтому цепочка `or` идёт дальше пока не найдёт что-то реальное.

**Что такое `HTTPException` и почему именно 404?**

`HTTPException` — это способ вернуть ошибку с нужным HTTP-кодом:
- `400` — плохой запрос (неправильный тикер по формату)
- `404` — не найдено (тикер не существует на бирже)
- `502` — ошибка внешнего сервиса (Yahoo Finance не ответил)

Когда `raise HTTPException(status_code=404, ...)` — FastAPI автоматически прекращает выполнение и возвращает JSON вида `{"detail": "Ticker not found"}` с кодом 404.

**Как работает история цен:**

```python
def get_price_history(ticker: str) -> list:
    t = yf.Ticker(ticker)
    hist = t.history(period="12d")  # DataFrame: строки = дни, колонки = Open/High/Low/Close/Volume

    points = []
    for date_idx, row in hist.tail(8).iterrows():  # берём последние 8 торговых дней
        date_str = date_idx.strftime("%d.%m")       # формат "29.05"
        points.append({
            "date": date_str,
            "price": round(float(row["Close"]), 2)  # цена закрытия
        })

    return points
```

`t.history(period="12d")` возвращает pandas DataFrame. `hist.tail(8)` берёт последние 8 строк (торговых дней). `.iterrows()` перебирает строки DataFrame — `date_idx` это дата, `row` это словарь с ценами.

---

## Файл 5: `app/services/news_service.py` — новости

```python
def get_news(ticker: str) -> list:
    t = yf.Ticker(ticker)
    raw_news = t.news or []

    news_items = []
    for item in raw_news[:5]:                        # берём не больше 5 новостей
        content = item.get("content", {}) if isinstance(item.get("content"), dict) else {}

        title = content.get("title") or item.get("title") or "Без заголовка"

        pub_ts = item.get("providerPublishTime") or content.get("pubDate") or ""
        if isinstance(pub_ts, (int, float)) and pub_ts > 0:
            published_at = datetime.fromtimestamp(pub_ts).strftime("%Y-%m-%d")
        ...
```

**Почему код такой сложный с `content.get()` и `item.get()`?**

`yfinance` возвращает новости в разных форматах в зависимости от версии библиотеки и типа новости. Иногда данные лежат прямо в `item`, иногда вложены в `item["content"]`. Код проверяет оба варианта через `or`.

**Что такое Unix timestamp и зачем `datetime.fromtimestamp()`?**

Yahoo Finance возвращает время публикации как число — количество секунд, прошедших с 1 января 1970 года. Например `1748476800`. Это называется Unix timestamp. `datetime.fromtimestamp(1748476800)` превращает его в нормальную дату.

```python
from datetime import datetime
datetime.fromtimestamp(1748476800).strftime("%Y-%m-%d")
# → "2025-05-29"
```

---

## Файл 6: `app/services/ai_service.py` — анализ

Этот файл реализует два режима анализа и выбирает нужный:

### Режим 1: Keyword-анализ (без API-ключа)

```python
POSITIVE_KEYWORDS = ["рост", "растет", "выручк", "growth", "revenue", "profit", ...]
NEGATIVE_KEYWORDS = ["снижа", "риск", "давлен", "decline", "loss", "risk", ...]

def infer_news_impact(news_item: dict) -> str:
    text = news_item["title"] + " " + news_item["summary"]
    pos = sum(1 for kw in POSITIVE_KEYWORDS if kw in text.lower())
    neg = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text.lower())

    if pos > neg: return "positive"
    if neg > pos: return "negative"
    return "neutral"
```

Логика простая: считаем сколько позитивных и негативных слов встретилось в тексте новости. Побеждает большинство. Это перевод JavaScript-логики из `ai-analysis/analysisRules.js` на Python.

**Ключевые слова написаны как части слов намеренно.** Например `"снижа"` поймает и `"снижает"`, и `"снижается"`, и `"снижался"` — это называется стемминг вручную.

### Режим 2: Claude Haiku через WellFlow

```python
def _build_wellflow_analysis(stock: dict, news: list) -> str:
    news_lines = "\n".join(
        f"- [{n['impact'].upper()}] {n['title']}: {n['summary']}"
        for n in news
    )

    prompt = f"""
    Ты финансовый аналитический ассистент...
    - Тикер: {stock['ticker']}
    - Цена: {stock['price']} {stock['currency']}
    - Новости:
    {news_lines}
    ...
    """

    response = httpx.post(
        "https://api.wellflow.dev/v1/chat/completions",
        headers={"Authorization": f"Bearer {WELLFLOW_API_KEY}"},
        json={
            "model": "claude-haiku-4.5",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 400,
            "temperature": 0.5,
        },
        timeout=30.0,
    )
    return response.json()["choices"][0]["message"]["content"]
```

**Что такое `temperature`?**

Параметр от 0 до 1 который влияет на «случайность» ответа модели:
- `0.0` — детерминированный ответ, всегда одинаковый
- `1.0` — максимально творческий и разнообразный
- `0.5` — баланс: достаточно стабильный, но не роботизированный

**Что такое `max_tokens`?**

Ограничение длины ответа. 400 токенов ≈ 300 слов. Без этого ограничения модель могла бы генерировать очень длинный текст и тратить лишние деньги.

**Почему `response.json()["choices"][0]["message"]["content"]`?**

WellFlow возвращает ответ в формате OpenAI API:
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Текст ответа модели..."
      }
    }
  ]
}
```

`choices` — массив потому что можно попросить несколько вариантов ответа (`n=3`). Мы просим один, поэтому берём `[0]`.

### Выбор режима

```python
def build_ai_analysis(stock: dict, news: list) -> str:
    if WELLFLOW_API_KEY:           # если ключ задан в .env
        try:
            return _build_wellflow_analysis(stock, news)   # пробуем Claude
        except Exception:
            pass                   # при любой ошибке — тихо идём дальше
    return _build_keyword_analysis(stock, news)            # keyword-режим
```

Это паттерн **graceful degradation** — приложение работает в любых условиях. Нет ключа — работает бесплатно. Ключ есть, но WellFlow недоступен — тоже работает. Это делает backend надёжным.

---

## Файл 7: `app/main.py` — точка входа

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import StockResponse, NewsItem, PricePoint
from app.services.stock_service import get_stock_data, get_price_history
from app.services.news_service import get_news
from app.services.ai_service import enrich_news, build_ai_analysis

app = FastAPI(title="AI Investment Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
```

**Что такое CORS и почему он нужен?**

CORS (Cross-Origin Resource Sharing) — механизм безопасности браузера. Браузер запрещает JavaScript-коду на `http://localhost:5173` делать запросы к `http://localhost:8001` — потому что это разные «источники» (разные порты). Backend должен явно разрешить такие запросы через заголовок `Access-Control-Allow-Origin`.

`allow_origins=["*"]` — разрешаем запросы с любого адреса. Для продакшна нужно указать конкретный домен вместо `"*"`.

**Два endpoint'а:**

```python
@app.get("/api/health")
def health():
    return {"status": "ok"}
```

`/api/health` — простая проверка что сервер живой. Используется для мониторинга и тестирования.

```python
@app.get("/api/analyze/{ticker}", response_model=StockResponse)
def analyze(ticker: str):
    ticker = ticker.upper().strip()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")

    try:
        stock = get_stock_data(ticker)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch stock data: {str(e)}")

    try:
        history = get_price_history(ticker)
    except Exception:
        history = []

    try:
        raw_news = get_news(ticker)
    except Exception:
        raw_news = []

    enriched = enrich_news(raw_news)
    ai_text = build_ai_analysis({**stock, "priceHistory": history}, enriched)

    return StockResponse(
        ticker=stock["ticker"],
        companyName=stock["companyName"],
        ...
        news=[NewsItem(**n) for n in enriched],
        aiAnalysis=ai_text,
    )
```

**Что означает `{ticker}` в пути?**

`/api/analyze/{ticker}` — это path parameter. FastAPI автоматически извлекает значение из URL и передаёт в функцию как аргумент. При запросе `/api/analyze/AAPL` переменная `ticker` будет равна `"AAPL"`.

**Почему ошибки обрабатываются по-разному?**

```python
try:
    stock = get_stock_data(ticker)
except HTTPException:
    raise                     # перебрасываем как есть (404 от stock_service)
except Exception as e:
    raise HTTPException(502)  # любая другая ошибка → 502
```

`get_stock_data` может намеренно бросить `HTTPException(404)` когда тикер не найден — это не ошибка, это нормальный ответ. Поэтому мы его перехватываем отдельно и пробрасываем дальше без изменений. Любые другие неожиданные ошибки (сеть, парсинг) превращаем в `502 Bad Gateway`.

```python
try:
    history = get_price_history(ticker)
except Exception:
    history = []              # если история не загрузилась — пустой список
```

История цен и новости — не критичны. Если они не загрузились, возвращаем пустые списки вместо ошибки. Фронт это обработает корректно.

**Что такое `NewsItem(**n)` и `{**stock, "priceHistory": history}`?**

`**n` — это распаковка словаря. Если `n = {"title": "...", "impact": "positive"}`, то `NewsItem(**n)` эквивалентно `NewsItem(title="...", impact="positive")`.

`{**stock, "priceHistory": history}` — создаёт новый словарь из всех полей `stock` плюс добавляет `"priceHistory"`. Это нужно чтобы передать историю в `build_ai_analysis` без изменения исходного словаря.

**`response_model=StockResponse` — для чего?**

Это говорит FastAPI: «убедись что ответ соответствует структуре `StockResponse`, и автоматически сериализуй объект в JSON». Если вернуть объект `StockResponse`, FastAPI сам превратит его в JSON и вернёт с правильными заголовками `Content-Type: application/json`.

---

## Итог: схема зависимостей

```
main.py
  ├── models.py          (структуры данных)
  ├── stock_service.py   (yfinance → цена, история)
  ├── news_service.py    (yfinance → новости)
  └── ai_service.py
        ├── config.py    (ключи из .env)
        ├── keyword-анализ (всегда работает)
        └── WellFlow API  (если есть ключ)
```

Каждый файл отвечает за одну задачу — это называется **принцип единственной ответственности**. Если завтра понадобится заменить yfinance на другой источник данных, достаточно изменить только `stock_service.py` — всё остальное не трогаем.
