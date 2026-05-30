# Frontend

Frontend сделан на обычных HTML, CSS и JavaScript без сборщика.

## Запуск

Запускай проект из корня:

```bash
python3 run.py
```

После запуска открой:

```text
http://127.0.0.1:5173/frontend/index.html
```

## Как работает

Frontend отправляет тикер в backend:

```text
GET http://localhost:8001/api/analyze/{ticker}
```

Backend возвращает реальные рыночные данные, новости и итоговый AI-анализ. Локальный mock-режим во frontend больше не используется.

## Файлы

- `index.html` — разметка приложения.
- `styles.css` — внешний вид.
- `app.js` — запрос к backend, обработка ошибок, отрисовка результата и графика.
