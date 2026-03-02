from __future__ import annotations

from typing import Any, Dict


def analyze_governance(bundle) -> Dict[str, Any]:
    holders = bundle.ownership.get("institutional_holders", [])
    insiders = bundle.ownership.get("insider_transactions", [])

    inst_value = sum(float(h.get("Value", 0) or 0) for h in holders) if holders else 0
    insider_net = 0
    for tx in insiders:
        shares = float(tx.get("Shares", 0) or 0)
        text = str(tx.get("Text", "")).lower()
        insider_net += shares if "buy" in text else -shares

    score = 60
    notes = []
    if insider_net > 0:
        score += 10
        notes.append("Recent insider activity appears net positive.")
    elif insider_net < 0:
        score -= 10
        notes.append("Recent insider activity appears net negative.")

    if inst_value <= 0:
        score -= 5
        notes.append("Limited institutional ownership visibility from free sources.")

    notes.append("Promoter trend, pledging, and auditor remarks should be cross-checked with latest NSE/BSE filings.")

    return {
        "metrics": {
            "institutional_value_proxy": inst_value,
            "insider_net_shares_proxy": insider_net,
        },
        "notes": notes,
        "score": max(20, min(90, score)),
    }
