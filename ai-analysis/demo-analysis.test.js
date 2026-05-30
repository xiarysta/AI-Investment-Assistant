const fs = require("fs");
const path = require("path");
const vm = require("vm");
const assert = require("assert");

const rootDir = path.resolve(__dirname, "..");
const context = vm.createContext({});

for (const file of ["ai-analysis/analysisRules.js"]) {
  const source = fs.readFileSync(path.join(rootDir, file), "utf8");
  vm.runInContext(source, context, { filename: file });
}

const demoAnalysisRules = vm.runInContext("demoAnalysisRules", context);

assert.ok(demoAnalysisRules, "demoAnalysisRules должен быть доступен для тестов");

const sampleStocks = {
  AAPL: {
    ticker: "AAPL",
    companyName: "Apple Inc.",
    dailyChangePercent: 1.24,
    priceHistory: [
      { date: "28.05", price: 189.3 },
      { date: "29.05", price: 190.12 }
    ],
    news: [
      { title: "Apple сообщает о росте спроса", summary: "Спрос поддерживает выручку." },
      { title: "Аналитики предупреждают о рисках", summary: "Риски могут давить на маржу." },
      { title: "Поставщик ожидает стабильный объем", summary: "Производство остается стабильным." }
    ]
  },
  MSFT: {
    ticker: "MSFT",
    companyName: "Microsoft Corporation",
    dailyChangePercent: 0.82,
    priceHistory: [
      { date: "28.05", price: 429.7 },
      { date: "29.05", price: 430.48 }
    ],
    news: [
      { title: "Microsoft усиливает облачное направление", summary: "Рост спроса поддерживает бизнес." },
      { title: "Расходы на AI-инфраструктуру остаются высокими", summary: "Затраты могут давить на маржу." },
      { title: "Клиенты расширяют подписки", summary: "Подписки дают стабильную выручку." }
    ]
  },
  TSLA: {
    ticker: "TSLA",
    companyName: "Tesla, Inc.",
    dailyChangePercent: -1.63,
    priceHistory: [
      { date: "28.05", price: 181.3 },
      { date: "29.05", price: 178.34 }
    ],
    news: [
      { title: "Tesla снижает цены", summary: "Снижение цен может ухудшить маржу." },
      { title: "Производство аккумуляторов растет", summary: "Рост производства поддерживает стратегию." },
      { title: "Конкуренция усиливается", summary: "Конкуренты давят на рынок." }
    ]
  }
};

for (const ticker of ["AAPL", "MSFT", "TSLA"]) {
  const result = demoAnalysisRules.enrichStock(sampleStocks[ticker]);

  assert.equal(result.ticker, ticker);
  assert.ok(result.aiAnalysis.includes(result.companyName));
  assert.ok(result.aiAnalysis.includes("не является рекомендацией"));
  assert.ok(result.news.length >= 3);

  for (const newsItem of result.news) {
    assert.ok(["positive", "negative", "neutral"].includes(newsItem.impact));
    assert.ok(newsItem.impactReason.length > 20);
  }
}

const inferredNegative = demoAnalysisRules.inferNewsImpact({
  title: "Компания предупреждает о снижении спроса и давлении на маржу"
});
assert.equal(inferredNegative, "negative");

const inferredPositive = demoAnalysisRules.inferNewsImpact({
  title: "Компания сообщает о росте спроса и расширяет производство"
});
assert.equal(inferredPositive, "positive");

console.log("Demo AI analysis tests passed");
