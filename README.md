# Quant Risk Engine

Portfolio stress testing and quantitative risk measurement.

This project answers: given a portfolio and adverse market assumptions, how large
could losses be, what drives them, and how sensitive are estimates to modeling
choices?

It is complementary to the **Volatility Intelligence Platform** (RV forecasting /
factor screening). QRE does not rebuild VIP.

## Status

Milestones **M0–M2 complete** (foundations, historical VaR/ES, stress +
linear contributions). Later milestones (Monte Carlo, GARCH, …) are planned
in `plan.md` and not implemented yet.

See `plan.md` and `docs/milestones/`.

## Install

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## CLI

```bash
qre --help
qre info
qre ingest --symbol SPY
qre ingest --symbol SPY --symbol TLT --start 2015-01-01
qre ingest --all-universe
qre analyze --portfolio configs/portfolios/demo_spy_qqq_tlt_gld.yaml
qre analyze --alpha 0.95 --alpha 0.99
qre stress --scenario configs/scenarios/equity_crash.yaml
qre stress --portfolio configs/portfolios/demo_spy_qqq_tlt_gld.yaml --scenario configs/scenarios/equity_crash.yaml
qre stress --scenario configs/scenarios/covid_window.yaml --alpha 0.95 --alpha 0.99
```

Parquet output lands under data/raw/{SYMBOL}/ohlcv.parquet.

Ingest and risk analysis arrive in later milestones.