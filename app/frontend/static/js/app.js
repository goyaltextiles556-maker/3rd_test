let chart;

const byId = (id) => document.getElementById(id);
const sections = ["summary", "chartSection", "riskHeatmap", "reasoning"];

function showSections() { sections.forEach((id) => byId(id).classList.remove("hidden")); }
function hideSections() { sections.forEach((id) => byId(id).classList.add("hidden")); }

function riskColor(val) {
  if (val > 0.66) return "#7f1d1d";
  if (val > 0.33) return "#92400e";
  return "#14532d";
}

async function analyzeTicker() {
  const ticker = byId("tickerInput").value.trim().toUpperCase();
  byId("errorBox").classList.add("hidden");
  if (!ticker) {
    byId("errorBox").textContent = "Please enter a valid ticker symbol.";
    byId("errorBox").classList.remove("hidden");
    return;
  }

  byId("loader").classList.remove("hidden");
  hideSections();

  try {
    const resp = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || "Unknown error");

    const d = data.decision;
    const v = data.engines.valuation.metrics;
    const g = data.engines.governance.metrics;

    byId("verdict").textContent = d.verdict;
    byId("confidence").textContent = `Confidence: ${(d.confidence * 100).toFixed(1)}%`;
    byId("horizon").textContent = `Suggested horizon: ${d.holding_horizon_years}`;
    byId("score").textContent = d.composite_score.toFixed(1);
    byId("riskReturn").textContent = `Risk-adjusted return: ${(d.risk_adjusted_expected_return * 100).toFixed(1)}%`;
    byId("probability").textContent = `Forward upside probability: ${(d.forward_probability_upside * 100).toFixed(1)}%`;

    byId("valuationList").innerHTML = `
      <li>Trailing PE: ${v.trailing_pe?.toFixed?.(2) ?? "NA"}</li>
      <li>PE vs 5Y avg: ${((v.pe_vs_5y_avg || 0) * 100).toFixed(1)}%</li>
      <li>EV/EBITDA: ${v.ev_ebitda?.toFixed?.(2) ?? "NA"}</li>
      <li>Price/Book: ${v.price_to_book?.toFixed?.(2) ?? "NA"}</li>
      <li>Margin of Safety: ${((v.margin_of_safety || 0) * 100).toFixed(1)}%</li>
    `;

    byId("ownershipList").innerHTML = `
      <li>Institutional Value Proxy: ${Math.round(g.institutional_value_proxy || 0).toLocaleString()}</li>
      <li>Insider Net Shares Proxy: ${Math.round(g.insider_net_shares_proxy || 0).toLocaleString()}</li>
      <li>Cross-check promoter pledging with exchange filings</li>
    `;

    byId("reasonList").innerHTML = (d.reasons || []).map((x) => `<li>${x}</li>`).join("");
    byId("warningList").innerHTML = [...(d.warning_signals || []), ...(d.exit_conditions || [])]
      .map((x) => `<li>${x}</li>`)
      .join("");

    const riskGrid = byId("riskGrid");
    riskGrid.innerHTML = "";
    Object.entries(data.engines.risk.risk_vector).forEach(([k, val]) => {
      const div = document.createElement("div");
      div.className = "risk-item";
      div.style.background = riskColor(val);
      div.textContent = `${k}: ${(val * 100).toFixed(0)}%`;
      riskGrid.appendChild(div);
    });

    if (chart) chart.destroy();
    chart = new Chart(byId("priceChart"), {
      type: "line",
      data: {
        labels: data.charts.dates,
        datasets: [
          { label: `${data.ticker} Price`, data: data.charts.price, borderColor: "#22c55e", tension: 0.2 },
          { label: "Nifty 50", data: data.charts.nifty, borderColor: "#60a5fa", tension: 0.2 },
        ],
      },
    });

    showSections();
  } catch (e) {
    byId("errorBox").textContent = e.message;
    byId("errorBox").classList.remove("hidden");
  } finally {
    byId("loader").classList.add("hidden");
  }
}

byId("analyzeBtn").addEventListener("click", analyzeTicker);
