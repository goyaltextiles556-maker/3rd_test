from __future__ import annotations

from typing import Any, Dict

import numpy as np


def build_decision(engines: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    f = engines["financial"]
    s = engines["sector"]
    g = engines["governance"]
    r = engines["risk"]
    v = engines["valuation"]
    t = engines["technical"]

    cross_checks = {
        "profitability_vs_leverage": f["metrics"].get("revenue_cagr", 0) - max(f["metrics"].get("debt_to_equity", 0) - 0.8, 0),
        "valuation_vs_growth": -v["metrics"].get("pe_vs_5y_avg", 0) + f["metrics"].get("revenue_cagr", 0),
        "commodity_vs_margin": -abs(s["metrics"].get("crude_sensitivity", 0)) + f["metrics"].get("margin_stability", 0),
        "promoter_behavior_vs_stress": g["score"] / 100 - f["metrics"].get("debt_to_equity", 0) / 2,
    }

    composite = (
        0.25 * f["score"]
        + 0.12 * s["score"]
        + 0.12 * g["score"]
        + 0.18 * r["score"]
        + 0.2 * v["score"]
        + 0.13 * t["score"]
    )

    cross_bonus = 8 * np.mean(list(cross_checks.values()))
    composite = float(np.clip(composite + cross_bonus, 0, 100))

    if composite >= 75:
        verdict = "Buy"
    elif composite >= 62:
        verdict = "Accumulate"
    elif composite >= 48:
        verdict = "Hold"
    else:
        verdict = "Avoid"

    expected_return = (
        0.5 * f["metrics"].get("revenue_cagr", 0.08)
        + 0.3 * max(v["metrics"].get("margin_of_safety", 0), -0.2)
        + 0.2 * t["metrics"].get("trend_vs_200dma", 0)
    )
    risk_penalty = (1 - r["score"] / 100) * 0.2
    risk_adj_return = expected_return - risk_penalty

    confidence = float(np.clip((composite / 100) * (1 - abs(risk_adj_return - expected_return)), 0.2, 0.95))
    probability_upside = float(np.clip(0.45 + risk_adj_return, 0.1, 0.9))

    reasons = []
    if verdict in {"Buy", "Accumulate"}:
        reasons.extend([
            "Core business quality and cash generation are supportive.",
            "Valuation and risk balance indicates favorable risk-reward.",
            "Trend and relative strength are not signaling structural weakness.",
        ])
    else:
        reasons.extend([
            "Risk-adjusted return potential is not attractive at current levels.",
            "At least one of leverage, valuation, or margin quality is pressuring conviction.",
            "Wait for cleaner governance/earnings visibility or better valuation entry.",
        ])

    return {
        "composite_score": round(composite, 2),
        "verdict": verdict,
        "forward_probability_upside": probability_upside,
        "risk_adjusted_expected_return": risk_adj_return,
        "confidence": confidence,
        "holding_horizon_years": "3-5" if verdict == "Buy" else "2-4" if verdict == "Accumulate" else "Monitor quarterly",
        "exit_conditions": [
            "Debt to equity rises above 1.5 with weak cash conversion.",
            "Two consecutive quarters of margin compression without volume growth.",
            "Material negative governance/regulatory event.",
        ],
        "warning_signals": f.get("red_flags", []) + s.get("sector_risks", [])[:2],
        "reconsider_for_avoid": [
            "Valuation margin of safety improves above 20%.",
            "Cash flow quality improves and leverage trend declines.",
            "Sector risk normalizes with stable regulatory context.",
        ],
        "assumptions": [
            "Historical financial trends remain directionally relevant for next 3-5 years.",
            "No extreme policy shock beyond historical volatility bands.",
            "Risk-free rate proxy based on available 10Y benchmark source.",
        ],
        "cross_checks": cross_checks,
        "reasons": reasons,
    }
