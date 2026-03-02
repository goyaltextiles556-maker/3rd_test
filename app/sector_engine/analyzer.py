from __future__ import annotations

from typing import Any, Dict

import numpy as np


OIL_KEYWORDS = {"oil", "gas", "refin", "petro"}
PHARMA_KEYWORDS = {"pharma", "drug", "health", "biotech"}


def analyze_sector(bundle) -> Dict[str, Any]:
    info = bundle.info
    sector = str(info.get("sector", "Unknown"))
    industry = str(info.get("industry", "Unknown"))
    text = f"{sector} {industry}".lower()

    stock_returns = bundle.price_history["Close"].pct_change().dropna()
    crude_returns = bundle.crude_history["Close"].pct_change().dropna()
    aligned = stock_returns.to_frame("stock").join(crude_returns.to_frame("crude"), how="inner")
    crude_sensitivity = float(aligned.corr().iloc[0, 1]) if len(aligned) > 50 else 0

    profile = "general"
    risks = []
    if any(k in text for k in OIL_KEYWORDS):
        profile = "oil_gas"
        risks.extend([
            "Crude volatility may pressure gross refining margins.",
            "Government pricing controls can compress pass-through margins.",
            "Import dependency can raise FX-linked procurement risk.",
        ])
    elif any(k in text for k in PHARMA_KEYWORDS):
        profile = "pharma"
        risks.extend([
            "USFDA or CDSCO observations can disrupt exports.",
            "Patent cliff risk may weaken product pricing power.",
            "API import dependence may increase supply chain concentration risk.",
        ])

    score_base = 65
    score_adj = -15 * abs(crude_sensitivity) if profile == "oil_gas" else 0
    score = max(20, min(90, score_base + score_adj))

    return {
        "sector": sector,
        "industry": industry,
        "profile": profile,
        "metrics": {
            "crude_sensitivity": crude_sensitivity,
            "proxy_fuel_demand_growth": float(np.clip(stock_returns.rolling(252).mean().iloc[-1] * 252, -0.3, 0.3)) if len(stock_returns) > 260 else 0,
        },
        "sector_risks": risks,
        "score": round(float(score), 2),
    }
