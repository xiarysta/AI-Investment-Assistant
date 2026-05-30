const USE_MOCK_API = true;
const API_BASE_URL = "http://localhost:8000";

const form = document.querySelector("#search-form");
const tickerInput = document.querySelector("#ticker-input");
const submitButton = document.querySelector("#submit-button");
const message = document.querySelector("#message");
const emptyState = document.querySelector("#empty-state");
const results = document.querySelector("#results");

const resultTicker = document.querySelector("#result-ticker");
const companyName = document.querySelector("#company-name");
const stockPrice = document.querySelector("#stock-price");
const stockChange = document.querySelector("#stock-change");
const companyDescription = document.querySelector("#company-description");
const aiAnalysis = document.querySelector("#ai-analysis");
const newsCount = document.querySelector("#news-count");
const newsList = document.querySelector("#news-list");
const priceChart = document.querySelector("#price-chart");
const chartPeriod = document.querySelector("#chart-period");
const chartPointsCount = document.querySelector("#chart-points-count");

function setMessage(text, type = "info") {
  message.textContent = text;
  message.className = `message ${type === "error" ? "error-message" : ""}`;
}

function hideMessage() {
  message.textContent = "";
  message.className = "message hidden";
}

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.textContent = isLoading ? "Загрузка" : "Анализ";
}

function formatChange(value) {
  if (typeof value !== "number") {
    return "0.00%";
  }

  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function getImpactLabel(impact) {
  const labels = {
    positive: "Положительное",
    negative: "Отрицательное",
    neutral: "Нейтральное"
  };

  return labels[impact] || "Нейтральное";
}

function formatPrice(value, currency) {
  if (typeof value !== "number") {
    return `0 ${currency || ""}`.trim();
  }

  return `${value.toFixed(2)} ${currency || ""}`.trim();
}

function normalizeTicker(ticker) {
  return ticker.trim().toUpperCase();
}

function getAvailableTickersText() {
  return Object.keys(mockStocks).join(", ");
}

function wait(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

async function analyzeTicker(ticker) {
  const normalizedTicker = normalizeTicker(ticker);

  if (!normalizedTicker) {
    throw new Error("Введите тикер компании.");
  }

  if (USE_MOCK_API) {
    await wait(500);

    if (!mockStocks[normalizedTicker]) {
      throw new Error(
        `Тикер "${normalizedTicker}" не найден в демо-данных. Попробуйте: ${getAvailableTickersText()}.`
      );
    }

    return mockStocks[normalizedTicker];
  }

  const response = await fetch(`${API_BASE_URL}/api/analyze/${normalizedTicker}`);

  if (!response.ok) {
    let errorMessage = "Не удалось получить данные по тикеру.";

    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      errorMessage = "Сервер вернул ошибку без подробностей.";
    }

    throw new Error(errorMessage);
  }

  return response.json();
}

function renderNews(newsItems) {
  newsList.innerHTML = "";
  newsCount.textContent = newsItems.length;

  newsItems.forEach((newsItem) => {
    const article = document.createElement("article");
    article.className = "news-card";

    const meta = document.createElement("div");
    meta.className = "news-meta";

    const date = document.createElement("span");
    date.textContent = newsItem.publishedAt || "";

    const impact = document.createElement("span");
    impact.className = `impact impact-${newsItem.impact || "neutral"}`;
    impact.textContent = getImpactLabel(newsItem.impact);

    const title = document.createElement("h3");
    title.textContent = newsItem.title || "Без заголовка";

    const summary = document.createElement("p");
    summary.textContent = newsItem.summary || "Краткое описание недоступно.";

    const reason = document.createElement("p");
    reason.className = "impact-reason";
    reason.textContent = newsItem.impactReason || "";

    meta.append(date, impact);
    article.append(meta, title, summary, reason);

    if (newsItem.url) {
      const link = document.createElement("a");
      link.href = newsItem.url;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = "Источник";
      article.append(link);
    }

    newsList.append(article);
  });
}

function drawPriceChart(history, currency) {
  const context = priceChart.getContext("2d");
  const width = priceChart.width;
  const height = priceChart.height;
  const padding = {
    top: 28,
    right: 28,
    bottom: 44,
    left: 64
  };

  context.clearRect(0, 0, width, height);
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, width, height);

  if (!history || history.length < 2) {
    chartPeriod.textContent = "Недостаточно данных для графика";
    chartPointsCount.textContent = "0";
    context.fillStyle = "#637486";
    context.font = "18px Segoe UI, sans-serif";
    context.fillText("История цены пока недоступна", padding.left, height / 2);
    return;
  }

  const prices = history.map((point) => point.price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceRange = maxPrice - minPrice || 1;
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const firstDate = history[0].date;
  const lastDate = history[history.length - 1].date;

  chartPeriod.textContent = `${firstDate} - ${lastDate}`;
  chartPointsCount.textContent = history.length;

  function getX(index) {
    if (history.length === 1) {
      return padding.left;
    }

    return padding.left + (index / (history.length - 1)) * plotWidth;
  }

  function getY(price) {
    return padding.top + ((maxPrice - price) / priceRange) * plotHeight;
  }

  context.strokeStyle = "#e5ebf1";
  context.lineWidth = 1;
  context.fillStyle = "#637486";
  context.font = "13px Segoe UI, sans-serif";

  for (let i = 0; i <= 4; i += 1) {
    const y = padding.top + (plotHeight / 4) * i;
    const price = maxPrice - (priceRange / 4) * i;

    context.beginPath();
    context.moveTo(padding.left, y);
    context.lineTo(width - padding.right, y);
    context.stroke();
    context.fillText(formatPrice(price, currency), 8, y + 4);
  }

  const firstPointColor =
    history[history.length - 1].price >= history[0].price ? "#137348" : "#a83232";

  context.beginPath();
  history.forEach((point, index) => {
    const x = getX(index);
    const y = getY(point.price);

    if (index === 0) {
      context.moveTo(x, y);
    } else {
      context.lineTo(x, y);
    }
  });
  context.strokeStyle = firstPointColor;
  context.lineWidth = 4;
  context.lineJoin = "round";
  context.lineCap = "round";
  context.stroke();

  const gradient = context.createLinearGradient(0, padding.top, 0, height - padding.bottom);
  gradient.addColorStop(0, "rgba(20, 107, 140, 0.18)");
  gradient.addColorStop(1, "rgba(20, 107, 140, 0)");

  context.lineTo(width - padding.right, height - padding.bottom);
  context.lineTo(padding.left, height - padding.bottom);
  context.closePath();
  context.fillStyle = gradient;
  context.fill();

  history.forEach((point, index) => {
    const x = getX(index);
    const y = getY(point.price);

    context.beginPath();
    context.arc(x, y, 4, 0, Math.PI * 2);
    context.fillStyle = "#ffffff";
    context.fill();
    context.strokeStyle = firstPointColor;
    context.lineWidth = 2;
    context.stroke();
  });

  context.fillStyle = "#405266";
  context.font = "14px Segoe UI, sans-serif";
  context.fillText(firstDate, padding.left, height - 14);
  const lastDateWidth = context.measureText(lastDate).width;
  context.fillText(lastDate, width - padding.right - lastDateWidth, height - 14);
}

function renderResult(data) {
  resultTicker.textContent = data.ticker;
  companyName.textContent = data.companyName;
  stockPrice.textContent = formatPrice(data.price, data.currency);
  stockChange.textContent = formatChange(data.dailyChangePercent);
  stockChange.className =
    data.dailyChangePercent >= 0 ? "change-positive" : "change-negative";
  companyDescription.textContent = data.companyDescription;
  aiAnalysis.textContent = data.aiAnalysis;

  drawPriceChart(data.priceHistory || [], data.currency);
  renderNews(data.news || []);

  emptyState.classList.add("hidden");
  results.classList.remove("hidden");
}

window.addEventListener("resize", () => {
  if (!results.classList.contains("hidden")) {
    const currentTicker = resultTicker.textContent;
    const currentData = mockStocks[currentTicker];

    if (USE_MOCK_API && currentData) {
      drawPriceChart(currentData.priceHistory || [], currentData.currency);
    }
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideMessage();
  setLoading(true);
  setMessage("Получаем данные и готовим анализ...");

  try {
    const data = await analyzeTicker(tickerInput.value);
    renderResult(data);
    hideMessage();
  } catch (error) {
    results.classList.add("hidden");
    emptyState.classList.add("hidden");
    setMessage(error.message, "error");
  } finally {
    setLoading(false);
  }
});

document.querySelectorAll("[data-ticker]").forEach((button) => {
  button.addEventListener("click", () => {
    tickerInput.value = button.dataset.ticker;
  });
});
