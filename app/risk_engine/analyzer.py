from __future__ import annotations

from typing import Any, Dict

import numpy as np


def analyze_risk(bundle, financial_metrics: Dict[str, Any], sector_metrics: Dict[str, Any]) -> Dict[str, Any]:
    returns = bundle.price_history["Close"].pct_change().dropna()
    beta = bundle.reconciled_snapshot.get("beta", 1.0)
    volatility = float(returns.std() * np.sqrt(252))

    leverage = financial_metrics.get("debt_to_equity", 0)
    crude_sensitivity = abs(sector_metrics.get("crude_sensitivity", 0))

    commodity_risk = min(1.0, crude_sensitivity)
    leverage_risk = min(1.0, leverage / 2)
    market_risk = min(1.0, volatility / 0.5)
    concentration_risk = 0.4
    regulatory_risk = 0.45 if sector_metrics else 0.5
    currency_risk = 0.35
    supply_chain_risk = 0.5

    risk_vector = {
        "commodity": commodity_risk,
        "currency": currency_risk,
        "regulatory": regulatory_risk,
        "leverage": leverage_risk,
        "concentration": concentration_risk,
        "supply_chain": supply_chain_risk,
        "market": market_risk,
        "beta": min(1.0, beta / 2),
    }

    risk_score = 100 * (1 - np.mean(list(risk_vector.values())))

    return {
        "risk_vector": risk_vector,
        "volatility": volatility,
        "score": round(float(risk_score), 2),
    }
