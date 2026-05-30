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


@app.get("/api/health")
def health():
    return {"status": "ok"}


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
        price=stock["price"],
        currency=stock["currency"],
        dailyChangePercent=stock["dailyChangePercent"],
        priceHistory=[PricePoint(**p) for p in history],
        companyDescription=stock["companyDescription"],
        news=[NewsItem(**n) for n in enriched],
        aiAnalysis=ai_text,
    )
