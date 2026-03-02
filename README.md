# Local Institutional Indian Equity Research Assistant

A browser-based local stock analysis tool for Indian equities (NSE tickers like `RELIANCE.NS`) that produces a structured **Buy / Accumulate / Hold / Avoid** verdict using free data sources.

## What this app does
- Accepts only one input: ticker symbol.
- Auto-collects 5-10Y style data from free sources (`yfinance` + NSE best-effort quote reconciliation).
- Runs modular analysis engines:
  - data_collection
  - financial_engine
  - sector_engine
  - governance_engine
  - risk_engine
  - valuation_engine
  - technical_engine
  - decision_engine
- Cross-references profitability, leverage, valuation, macro sensitivity, and sector risk.
- Displays:
  - Recommendation box
  - Composite score + confidence
  - Chart vs Nifty 50
  - Risk heatmap
  - Ownership proxy
  - Valuation summary

## Free data sources used
- Yahoo Finance (via `yfinance`) for market data, financials, and holder proxies.
- NSE quote API (best effort) for spot cross-validation.
- Nifty data via `^NSEI`.
- Crude proxy via `CL=F`.
- India 10Y proxy using available Yahoo symbols with fallback assumption.

---

## Beginner Setup Guide (step-by-step)

## 1) Install Python
1. Open browser and go to: https://www.python.org/downloads/
2. Download Python 3.11 or newer.
3. During install, tick **Add Python to PATH**.
4. Verify in terminal:
   ```bash
   python --version
   ```

## 2) Install Visual Studio Code
1. Download from https://code.visualstudio.com/
2. Install with default options.
3. Open VS Code and install extension: **Python** (by Microsoft).

## 3) Open project in VS Code
1. Open VS Code.
2. Click **File → Open Folder**.
3. Select this project folder (`3rd_test`).

## 4) Create virtual environment
In VS Code terminal:
```bash
python -m venv .venv
```

Activate:
- Windows PowerShell:
  ```bash
  .\.venv\Scripts\Activate.ps1
  ```
- macOS/Linux:
  ```bash
  source .venv/bin/activate
  ```

## 5) Install dependencies
```bash
pip install -r requirements.txt
```

## 6) Run the web app
```bash
python -m app.main
```

## 7) Open in browser
Go to:
- http://127.0.0.1:5000

Enter ticker like `SUNPHARMA.NS` and click **Analyze**.

---

## Troubleshooting
- **Error: Module not found**
  - Ensure venv is activated.
  - Re-run `pip install -r requirements.txt`.
- **No data for ticker**
  - Confirm NSE ticker format like `TCS.NS`.
  - Try another ticker to isolate symbol issues.
- **NSE quote fetch fails**
  - App auto-falls back to Yahoo data.
- **Slow analysis**
  - First run can be slower due to data download latency.
- **Port already in use**
  - Stop old Flask process or run with another port:
    ```bash
    flask --app app.main run --port 5050
    ```

## Notes
- This is an educational decision-support engine, not investment advice.
- Some governance data points (promoter pledging, auditor remarks) are marked as “cross-check with filings” where free APIs are limited.
