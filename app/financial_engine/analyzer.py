from __future__ import annotations

from typing import Any, Dict

import numpy as np


def _cagr(start_val: float, end_val: float, years: int) -> float:
    if start_val <= 0 or end_val <= 0 or years <= 0:
        return 0.0
    return (end_val / start_val) ** (1 / years) - 1


def analyze_financials(bundle) -> Dict[str, Any]:
    fin = bundle.financials
    bs = bundle.balance_sheet
    cf = bundle.cashflow

    if fin.empty:
        return {"score": 20, "commentary": ["Insufficient financial statement depth."]}

    revenue = fin.get("Total Revenue")
    ebit = fin.get("EBIT")
    net_income = fin.get("Net Income")

    years = max(len(fin.index) - 1, 1)
    revenue_cagr = _cagr(float(revenue.iloc[0]), float(revenue.iloc[-1]), years) if revenue is not None else 0

    margin_series = (ebit / revenue).replace([np.inf, -np.inf], np.nan).dropna() if ebit is not None and revenue is not None else np.array([])
    margin_stability = float(1 / (1 + np.std(margin_series))) if len(margin_series) else 0.2

    debt = bs.get("Total Debt")
    equity = bs.get("Stockholders Equity")
    debt_to_equity = float((debt.iloc[-1] / equity.iloc[-1])) if debt is not None and equity is not None and equity.iloc[-1] else 0

    op_cf = cf.get("Operating Cash Flow")
    fcf = cf.get("Free Cash Flow")
    fcf_consistency = float((fcf > 0).sum() / len(fcf)) if fcf is not None and len(fcf) else 0

    earnings_quality = float(op_cf.iloc[-1] / net_income.iloc[-1]) if op_cf is not None and net_income is not None and net_income.iloc[-1] else 0

    roce_proxy = float((ebit.iloc[-1] / (debt.iloc[-1] + equity.iloc[-1]))) if ebit is not None and debt is not None and equity is not None and (debt.iloc[-1] + equity.iloc[-1]) else 0

    score = 100 * (
        0.25 * min(max(revenue_cagr, 0), 0.25) / 0.25
        + 0.2 * min(margin_stability, 1)
        + 0.15 * min(max(roce_proxy, 0), 0.25) / 0.25
        + 0.2 * max(0, 1 - min(debt_to_equity, 3) / 3)
        + 0.2 * min(max(fcf_consistency, 0), 1)
    )

    red_flags = []
    if earnings_quality < 0.7:
        red_flags.append("Operating cash flow is weak vs net income.")
    if debt_to_equity > 1.5:
        red_flags.append("Leverage appears high relative to equity.")
    if margin_stability < 0.4:
        red_flags.append("Operating margins have been volatile.")

    return {
        "metrics": {
            "revenue_cagr": revenue_cagr,
            "margin_stability": margin_stability,
            "debt_to_equity": debt_to_equity,
            "fcf_consistency": fcf_consistency,
            "earnings_quality": earnings_quality,
            "roce_proxy": roce_proxy,
        },
        "red_flags": red_flags,
        "score": round(score, 2),
    }
