const demoAnalysisRules = (() => {
  const POSITIVE_KEYWORDS = [
    "рост",
    "растет",
    "расширяет",
    "развитие",
    "стабильн",
    "усиливает",
    "поддерж",
    "спрос",
    "выручк",
    "производство"
  ];

  const NEGATIVE_KEYWORDS = [
    "снижа",
    "слаб",
    "риск",
    "давлен",
    "конкурен",
    "затрат",
    "расход",
    "марж",
    "огранич",
    "предупреж"
  ];

  function normalizeText(value) {
    return String(value || "").toLowerCase();
  }

  function countKeywordHits(text, keywords) {
    return keywords.reduce((hits, keyword) => {
      return text.includes(keyword) ? hits + 1 : hits;
    }, 0);
  }

  function inferNewsImpact(newsItem) {
    if (["positive", "negative", "neutral"].includes(newsItem.impact)) {
      return newsItem.impact;
    }

    const text = normalizeText(
      `${newsItem.title || ""} ${newsItem.summary || ""} ${newsItem.impactReason || ""}`
    );
    const positiveHits = countKeywordHits(text, POSITIVE_KEYWORDS);
    const negativeHits = countKeywordHits(text, NEGATIVE_KEYWORDS);

    if (positiveHits > negativeHits) {
      return "positive";
    }

    if (negativeHits > positiveHits) {
      return "negative";
    }

    return "neutral";
  }

  function buildImpactReason(newsItem, impact) {
    if (newsItem.impactReason) {
      return newsItem.impactReason;
    }

    if (impact === "positive") {
      return "Новость может поддержать ожидания по выручке, спросу или операционной устойчивости.";
    }

    if (impact === "negative") {
      return "Новость указывает на риск для спроса, маржинальности или конкурентной позиции.";
    }

    return "Новость важна для контекста, но не дает сильного положительного или отрицательного сигнала.";
  }

  function enrichNews(newsItems) {
    return (newsItems || []).map((newsItem) => {
      const impact = inferNewsImpact(newsItem);

      return {
        ...newsItem,
        impact,
        impactReason: buildImpactReason(newsItem, impact)
      };
    });
  }

  function getTrendLabel(stock) {
    const history = stock.priceHistory || [];

    if (history.length < 2) {
      return "недостаточно данных по динамике цены";
    }

    const firstPrice = history[0].price;
    const lastPrice = history[history.length - 1].price;
    const trendPercent = ((lastPrice - firstPrice) / firstPrice) * 100;

    if (trendPercent >= 2) {
      return `цена за период заметно выросла примерно на ${trendPercent.toFixed(1)}%`;
    }

    if (trendPercent <= -2) {
      return `цена за период снизилась примерно на ${Math.abs(trendPercent).toFixed(1)}%`;
    }

    return "цена за период двигалась без резкого отклонения";
  }

  function getDailyChangeLabel(value) {
    if (typeof value !== "number") {
      return "дневное изменение не указано";
    }

    if (value > 0) {
      return `дневное изменение положительное: +${value.toFixed(2)}%`;
    }

    if (value < 0) {
      return `дневное изменение отрицательное: ${value.toFixed(2)}%`;
    }

    return "дневное изменение около нуля";
  }

  function getDominantMood(counts) {
    if (counts.positive > counts.negative) {
      return "умеренно позитивной";
    }

    if (counts.negative > counts.positive) {
      return "осторожной";
    }

    return "смешанной";
  }

  function pickNewsTitles(news, impact) {
    return news
      .filter((newsItem) => newsItem.impact === impact)
      .map((newsItem) => newsItem.title)
      .filter(Boolean)
      .slice(0, 2);
  }

  function buildListText(items, fallback) {
    if (!items.length) {
      return fallback;
    }

    return items.join("; ");
  }

  function buildAiAnalysis(stock) {
    const news = enrichNews(stock.news || []);
    const counts = news.reduce(
      (accumulator, newsItem) => {
        accumulator[newsItem.impact] += 1;
        return accumulator;
      },
      { positive: 0, negative: 0, neutral: 0 }
    );
    const mood = getDominantMood(counts);
    const positiveFactors = buildListText(
      pickNewsTitles(news, "positive"),
      "явных позитивных новостей в демо-наборе нет"
    );
    const riskFactors = buildListText(
      pickNewsTitles(news, "negative"),
      "сильных негативных сигналов в демо-наборе нет"
    );
    const neutralFactors = buildListText(
      pickNewsTitles(news, "neutral"),
      "нейтральные факторы выражены слабо"
    );
    const trendLabel = getTrendLabel(stock);
    const dailyChangeLabel = getDailyChangeLabel(stock.dailyChangePercent);

    return `${stock.companyName} (${stock.ticker}) выглядит ${mood} по демо-данным: ${dailyChangeLabel}, ${trendLabel}. В новостях: ${counts.positive} положительных, ${counts.negative} отрицательных и ${counts.neutral} нейтральных сигналов. Позитивные факторы: ${positiveFactors}. Риски: ${riskFactors}. Нейтральный контекст: ${neutralFactors}. Итог: ситуацию стоит рассматривать как краткую аналитическую справку по ограниченному набору данных; это не является рекомендацией покупать или продавать ценные бумаги.`;
  }

  function enrichStock(stock) {
    const news = enrichNews(stock.news || []);

    return {
      ...stock,
      news,
      aiAnalysis: buildAiAnalysis({
        ...stock,
        news
      }),
      analysisMode: "demo-rules"
    };
  }

  return {
    buildAiAnalysis,
    enrichNews,
    enrichStock,
    inferNewsImpact
  };
})();
