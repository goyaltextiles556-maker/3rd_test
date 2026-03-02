from __future__ import annotations

from typing import Any, Dict

import numpy as np


def analyze_technical(bundle) -> Dict[str, Any]:
    px = bundle.price_history["Close"].dropna()
    nifty = bundle.nifty_history["Close"].dropna()

    ma200 = px.rolling(200).mean().iloc[-1] if len(px) >= 200 else px.mean()
    trend = (px.iloc[-1] / ma200 - 1) if ma200 else 0

    aligned = px.pct_change().to_frame("s").join(nifty.pct_change().to_frame("n"), how="inner").dropna()
    rs = float((1 + aligned["s"]).prod() / (1 + aligned["n"]).prod() - 1) if len(aligned) else 0

    vol = float(px.pct_change().std() * np.sqrt(252))

    score = 50 + 25 * np.tanh(trend * 4) + 15 * np.tanh(rs * 3) - 10 * min(vol, 0.7)

    return {
        "metrics": {
            "price": float(px.iloc[-1]),
            "ma_200": float(ma200),
            "trend_vs_200dma": float(trend),
            "relative_strength_vs_nifty": rs,
            "annualized_volatility": vol,
        },
        "score": max(15, min(95, float(score))),
    }
