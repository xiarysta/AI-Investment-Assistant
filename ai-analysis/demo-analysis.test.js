const fs = require("fs");
const path = require("path");
const vm = require("vm");
const assert = require("assert");

const rootDir = path.resolve(__dirname, "..");
const context = vm.createContext({});

for (const file of ["frontend/mockData.js", "ai-analysis/analysisRules.js"]) {
  const source = fs.readFileSync(path.join(rootDir, file), "utf8");
  vm.runInContext(source, context, { filename: file });
}

const mockStocks = vm.runInContext("mockStocks", context);
const demoAnalysisRules = vm.runInContext("demoAnalysisRules", context);

assert.ok(mockStocks, "mockStocks должен быть доступен для тестов");
assert.ok(demoAnalysisRules, "demoAnalysisRules должен быть доступен для тестов");

for (const ticker of ["AAPL", "MSFT", "TSLA"]) {
  const result = demoAnalysisRules.enrichStock(mockStocks[ticker]);

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
