from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from app.data_collection.collectors import collect_all_data
from app.decision_engine.analyzer import build_decision
from app.financial_engine.analyzer import analyze_financials
from app.governance_engine.analyzer import analyze_governance
from app.risk_engine.analyzer import analyze_risk
from app.sector_engine.analyzer import analyze_sector
from app.technical_engine.analyzer import analyze_technical
from app.valuation_engine.analyzer import analyze_valuation

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static",
)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    payload = request.get_json(force=True)
    ticker = str(payload.get("ticker", "")).strip().upper()
    if not ticker:
        return jsonify({"error": "Ticker is required."}), 400

    try:
        bundle = collect_all_data(ticker)
        financial = analyze_financials(bundle)
        sector = analyze_sector(bundle)
        governance = analyze_governance(bundle)
        risk = analyze_risk(bundle, financial.get("metrics", {}), sector.get("metrics", {}))
        valuation = analyze_valuation(bundle, financial.get("metrics", {}), risk)
        technical = analyze_technical(bundle)

        decision = build_decision(
            {
                "financial": financial,
                "sector": sector,
                "governance": governance,
                "risk": risk,
                "valuation": valuation,
                "technical": technical,
            }
        )

        price_series = bundle.price_history["Close"].tail(300)
        nifty_series = bundle.nifty_history["Close"].reindex(price_series.index).ffill().bfill()

        return jsonify(
            {
                "ticker": ticker,
                "snapshot": bundle.reconciled_snapshot,
                "engines": {
                    "financial": financial,
                    "sector": sector,
                    "governance": governance,
                    "risk": risk,
                    "valuation": valuation,
                    "technical": technical,
                },
                "decision": decision,
                "charts": {
                    "dates": [d.strftime("%Y-%m-%d") for d in price_series.index],
                    "price": [float(v) for v in price_series.values],
                    "nifty": [float(v) for v in nifty_series.values],
                },
            }
        )
    except Exception as exc:
        return jsonify({"error": f"Analysis failed: {exc}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
