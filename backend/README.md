# Backend: что изучить и с чего начать

Этот файл - короткая дорожная карта для участника, который отвечает за backend проекта **AI-Investment-Assistant**.

Исходная точка: ты знаешь Python. Этого достаточно, чтобы за 2 дня собрать рабочий backend MVP, если не распыляться и идти по шагам.

---

## 1. Что должен делать backend в нашем проекте

Backend - это прослойка между frontend, внешними API и AI.

Он должен:

- принять тикер компании от frontend;
- проверить, что тикер корректный;
- получить данные об акции из внешнего API;
- получить новости по компании;
- отправить данные и новости в AI API или fallback-анализатор;
- собрать единый ответ;
- вернуть frontend готовый JSON.

Главная идея: frontend не должен сам ходить во внешние API. Он обращается только к нашему backend.

---

## 2. Минимальный стек для backend

Рекомендуемый стек:

- **Python** - основной язык;
- **FastAPI** - фреймворк для создания API;
- **Uvicorn** - сервер для запуска FastAPI;
- **Pydantic** - описание и проверка структуры данных;
- **python-dotenv** - чтение переменных окружения из `.env`;
- **httpx** или **requests** - запросы к внешним API.

Для нашего проекта лучше выбрать **FastAPI**, потому что он простой, быстрый и хорошо подходит для REST API.

---

## 3. Что почитать в первую очередь

### 3.1. HTTP и REST API

Нужно понимать:

- что такое клиент и сервер;
- что такое HTTP-запрос;
- чем отличаются `GET`, `POST`, `PUT`, `DELETE`;
- что такое URL path и query parameters;
- что такое JSON;
- что такое HTTP status codes: `200`, `400`, `404`, `500`.

Для проекта достаточно уверенно понимать `GET` и JSON-ответы.

### 3.2. FastAPI

Изучить:

- как создать FastAPI-приложение;
- как сделать endpoint;
- как принимать path parameter: `/api/analyze/{ticker}`;
- как вернуть JSON;
- как выбрасывать ошибку через `HTTPException`;
- как запустить приложение через `uvicorn`.

Минимальный пример:

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/api/analyze/{ticker}")
def analyze_ticker(ticker: str):
    ticker = ticker.upper()

    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")

    return {
        "ticker": ticker,
        "message": "Backend works"
    }
```

### 3.3. Pydantic

Нужно понимать:

- как описывать модели данных;
- зачем нужны `BaseModel`;
- как сделать структуру ответа более понятной.

Пример:

```python
from pydantic import BaseModel

class StockResponse(BaseModel):
    ticker: str
    companyName: str
    price: float
    currency: str
    dailyChangePercent: float
```

### 3.4. Работа с внешними API

Нужно изучить:

- как отправлять HTTP-запрос из Python;
- как передавать API key;
- как читать JSON-ответ;
- как обрабатывать ошибки;
- что делать, если API ничего не вернул.

Для запросов можно использовать `httpx`.

Пример:

```python
import httpx

response = httpx.get("https://example.com/api")
data = response.json()
```

### 3.5. Переменные окружения

API-ключи нельзя хранить прямо в коде.

Нужно изучить:

- что такое `.env`;
- как хранить ключи вроде `OPENAI_API_KEY` или `FINNHUB_API_KEY`;
- как читать их через `os.getenv`.

Пример `.env`:

```text
DATA_API_KEY=your_key_here
AI_API_KEY=your_key_here
```

Пример Python:

```python
import os
from dotenv import load_dotenv

load_dotenv()

data_api_key = os.getenv("DATA_API_KEY")
```

---

## 4. Что нужно реализовать в backend

### Обязательный минимум

Нужно сделать endpoint:

```text
GET /api/analyze/{ticker}
```

Он должен возвращать:

```json
{
  "ticker": "AAPL",
  "companyName": "Apple Inc.",
  "price": 190.12,
  "currency": "USD",
  "dailyChangePercent": 1.24,
  "companyDescription": "Short company description.",
  "news": [
    {
      "title": "News title",
      "publishedAt": "2026-05-29",
      "summary": "Short summary",
      "url": "https://example.com",
      "impact": "neutral",
      "impactReason": "No strong positive or negative signal."
    }
  ],
  "aiAnalysis": "Final short analytical report."
}
```

### Минимальная логика endpoint

1. Получить `ticker`.
2. Привести к верхнему регистру.
3. Проверить, что тикер не пустой.
4. Получить данные об акции.
5. Получить новости.
6. Проанализировать новости.
7. Сформировать итоговый ответ.
8. Вернуть JSON frontend.

---

## 5. Рекомендуемая структура backend

```text
backend/
  README.md
  requirements.txt
  .env.example
  app/
    main.py
    config.py
    models.py
    services/
      stock_service.py
      news_service.py
      ai_service.py
```

### За что отвечает каждый файл

`app/main.py`

- создает FastAPI-приложение;
- содержит endpoint `/api/analyze/{ticker}`;
- соединяет сервисы между собой.

`app/config.py`

- читает переменные окружения;
- хранит настройки проекта.

`app/models.py`

- содержит Pydantic-модели;
- описывает структуру новостей и ответа.

`app/services/stock_service.py`

- получает данные об акции.

`app/services/news_service.py`

- получает новости по тикеру или названию компании.

`app/services/ai_service.py`

- формирует AI-анализ;
- возвращает fallback, если AI недоступен.

---

## 6. План работы backend-разработчика на 2 дня

### День 1

#### Шаг 1. Поднять FastAPI

Результат:

- backend запускается;
- endpoint `/api/health` возвращает `{"status": "ok"}`.

#### Шаг 2. Сделать тестовый endpoint анализа

Результат:

- endpoint `/api/analyze/{ticker}` работает;
- пока можно возвращать mock-данные без внешнего API.

#### Шаг 3. Подключить API акций

Результат:

- backend получает реальную цену, валюту, название компании и изменение за день.

#### Шаг 4. Подключить новости

Результат:

- backend возвращает 3-5 новостей по компании.

### День 2

#### Шаг 5. Добавить AI или fallback-анализ

Результат:

- каждая новость получает `impact` и `impactReason`;
- итоговый ответ получает поле `aiAnalysis`.

#### Шаг 6. Обработать ошибки

Нужно обработать:

- пустой тикер;
- несуществующий тикер;
- внешний API не отвечает;
- превышен лимит API;
- AI API не отвечает.

#### Шаг 7. Интеграция с frontend

Результат:

- frontend может вызвать backend;
- структура ответа совпадает с ожиданиями frontend-разработчика.

#### Шаг 8. Финальная проверка

Проверить тикеры:

- `AAPL`
- `MSFT`
- `TSLA`
- неправильный тикер, например `AAAAAAA`
- пустой ввод

---

## 7. Что можно сделать без внешнего API, если не успеваешь

Если интеграция с внешним API занимает слишком много времени, сначала сделай mock-режим.

Пример:

```python
def get_mock_stock_data(ticker: str):
    return {
        "ticker": ticker,
        "companyName": "Demo Company",
        "price": 100.0,
        "currency": "USD",
        "dailyChangePercent": 0.5
    }
```

Это позволит frontend-разработчику не ждать backend и продолжать работу.

Потом mock можно заменить реальными запросами.

---

## 8. Что важно не забыть

- Не хранить API-ключи в коде.
- Не возвращать frontend огромные сырые ответы внешних API.
- Всегда возвращать понятные ошибки.
- Согласовать с frontend точные названия полей.
- Ограничить новости до 3-5 штук.
- Не писать в AI-анализе прямой совет "покупать" или "продавать".
- Добавить предупреждение, что анализ не является финансовой рекомендацией.

---

## 9. Минимальные команды

Создание виртуального окружения:

```bash
python -m venv venv
```

Активация:

```bash
source venv/bin/activate
```

Установка зависимостей:

```bash
pip install fastapi uvicorn python-dotenv httpx
```

Запуск backend:

```bash
uvicorn app.main:app --reload
```

Проверка health endpoint:

```bash
curl http://127.0.0.1:8000/api/health
```

Проверка анализа тикера:

```bash
curl http://127.0.0.1:8000/api/analyze/AAPL
```

---

## 10. Минимальный результат, который от тебя нужен

К концу работы backend должен:

- запускаться локально;
- иметь endpoint `/api/health`;
- иметь endpoint `/api/analyze/{ticker}`;
- возвращать данные в согласованном формате;
- не падать при неправильном тикере;
- отдавать понятную ошибку, если данные получить нельзя;
- быть готовым к подключению frontend.

Если это работает - backend MVP выполнен.
