from pydantic import BaseModel, Field
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
