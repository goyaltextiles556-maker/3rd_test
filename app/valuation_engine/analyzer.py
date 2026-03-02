from __future__ import annotations

from typing import Any, Dict

import numpy as np


def analyze_valuation(bundle, financial_metrics: Dict[str, Any], risk_output: Dict[str, Any]) -> Dict[str, Any]:
    info = bundle.info
    price = bundle.reconciled_snapshot["price"]

    trailing_pe = float(info.get("trailingPE") or 0)
    pb = float(info.get("priceToBook") or 0)
    ev_ebitda = float(info.get("enterpriseToEbitda") or 0)

    hist = bundle.price_history["Close"]
    pe_5y_avg_proxy = max(trailing_pe * (hist.rolling(252).mean().iloc[-1] / hist.iloc[-1]), 0.1) if trailing_pe else 0
    pe_vs_avg = (trailing_pe / pe_5y_avg_proxy - 1) if pe_5y_avg_proxy else 0

    growth = max(financial_metrics.get("revenue_cagr", 0.08), 0.02)
    risk_free = bundle.macro["risk_free_rate"]
    risk_premium = max(0.05, risk_output["volatility"] * 0.4)
    discount_rate = risk_free + risk_premium

    fcf_est = float(bundle.cashflow.get("Free Cash Flow", [0])[-1]) if not bundle.cashflow.empty and "Free Cash Flow" in bundle.cashflow else 0
    fcf_est = max(fcf_est, 0)
    terminal_growth = min(0.05, growth * 0.5)

    intrinsic = 0
    if fcf_est > 0 and discount_rate > terminal_growth:
        years = 5
        pv = 0.0
        current = fcf_est
        for y in range(1, years + 1):
            current *= (1 + growth)
            pv += current / ((1 + discount_rate) ** y)
        terminal = (current * (1 + terminal_growth)) / (discount_rate - terminal_growth)
        intrinsic = pv + terminal / ((1 + discount_rate) ** years)
        shares = bundle.info.get("sharesOutstanding") or 1
        intrinsic = intrinsic / shares

    margin_safety = (intrinsic - price) / price if price else 0

    score = 65
    score += -20 if pe_vs_avg > 0.25 else 10
    score += 10 if margin_safety > 0.2 else (-10 if margin_safety < -0.2 else 0)

    return {
        "metrics": {
            "trailing_pe": trailing_pe,
            "pe_5y_avg_proxy": pe_5y_avg_proxy,
            "pe_vs_5y_avg": pe_vs_avg,
            "price_to_book": pb,
            "ev_ebitda": ev_ebitda,
            "dcf_intrinsic_value": intrinsic,
            "margin_of_safety": margin_safety,
            "discount_rate": discount_rate,
        },
        "score": max(20, min(95, score)),
    }
