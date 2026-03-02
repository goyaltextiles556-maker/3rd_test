from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import requests
import yfinance as yf


@dataclass
class DataBundle:
    ticker: str
    info: Dict[str, Any]
    price_history: pd.DataFrame
    nifty_history: pd.DataFrame
    crude_history: pd.DataFrame
    financials: pd.DataFrame
    balance_sheet: pd.DataFrame
    cashflow: pd.DataFrame
    macro: Dict[str, float]
    ownership: Dict[str, Any]
    reconciled_snapshot: Dict[str, Any]


def _nse_quote_snapshot(ticker: str) -> Dict[str, Any]:
    """Best-effort snapshot from NSE quote API for cross-source checks."""
    symbol = ticker.replace(".NS", "")
    url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://www.nseindia.com/",
    }
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        resp = session.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        price = payload.get("priceInfo", {}).get("lastPrice")
        mcap = payload.get("securityInfo", {}).get("issuedCap")
        return {"price": price, "shares_outstanding": mcap}
    except Exception:
        return {}


def _safe_series_val(series: pd.Series, default: float = 0.0) -> float:
    if series is None or series.empty:
        return default
    val = series.dropna()
    return float(val.iloc[0]) if not val.empty else default


def collect_all_data(ticker: str) -> DataBundle:
    end = datetime.now()
    start = end - timedelta(days=3650)

    stock = yf.Ticker(ticker)
    info = stock.info or {}

    price_history = stock.history(start=start, end=end, auto_adjust=True)
    if price_history.empty:
        raise ValueError(f"No historical price data found for {ticker}")

    nifty = yf.Ticker("^NSEI").history(start=start, end=end, auto_adjust=True)
    crude = yf.Ticker("CL=F").history(start=start, end=end, auto_adjust=True)

    financials = stock.financials.T.sort_index()
    balance_sheet = stock.balance_sheet.T.sort_index()
    cashflow = stock.cashflow.T.sort_index()

    ten_year_symbols = ["^INDI10Y", "IN10Y.BD", "^TNX"]
    risk_free = np.nan
    for symbol in ten_year_symbols:
        try:
            history = yf.Ticker(symbol).history(period="6mo")
            if not history.empty:
                risk_free = float(history["Close"].dropna().iloc[-1]) / 100
                break
        except Exception:
            continue
    if np.isnan(risk_free):
        risk_free = 0.07

    macro = {
        "risk_free_rate": risk_free,
        "inflation_proxy": 0.05,
    }

    ownership = {
        "major_holders": stock.major_holders.to_dict() if stock.major_holders is not None else {},
        "institutional_holders": stock.institutional_holders.to_dict("records") if stock.institutional_holders is not None else [],
        "insider_transactions": stock.insider_transactions.to_dict("records") if stock.insider_transactions is not None else [],
    }

    nse_snapshot = _nse_quote_snapshot(ticker)
    yahoo_price = float(price_history["Close"].iloc[-1])
    nse_price = nse_snapshot.get("price")
    reconciled_price = float(np.nanmean([yahoo_price, nse_price])) if nse_price else yahoo_price

    shares = info.get("sharesOutstanding") or nse_snapshot.get("shares_outstanding") or 0
    market_cap = float(reconciled_price * shares) if shares else float(info.get("marketCap", 0))

    reconciled_snapshot = {
        "price": reconciled_price,
        "market_cap": market_cap,
        "beta": float(info.get("beta", 1.0) or 1.0),
        "volatility": float(price_history["Close"].pct_change().std() * np.sqrt(252)),
        "source_check": {
            "yahoo_price": yahoo_price,
            "nse_price": nse_price,
        },
    }

    return DataBundle(
        ticker=ticker,
        info=info,
        price_history=price_history,
        nifty_history=nifty,
        crude_history=crude,
        financials=financials,
        balance_sheet=balance_sheet,
        cashflow=cashflow,
        macro=macro,
        ownership=ownership,
        reconciled_snapshot=reconciled_snapshot,
    )
