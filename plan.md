# Quant Risk Engine — Architecture & Roadmap

Living design document for humans and agents. **Read this before starting any
milestone.** Update status only when that milestone’s exit checklist is met
(`pytest` green + proving experiment inspected).

**Related product:** Volatility Intelligence Platform (VIP) answers *what is
happening to volatility and what predicts it?* This product answers *given a
portfolio and adverse conditions, how much can we lose, why, and how sensitive
is that estimate to modeling assumptions?*

**Do not rebuild VIP** (HAR/factor screens, walk-forward QLIKE horse-race,
forecast diary). Optionally *consume* VIP artifacts later as vol inputs.

---

## Status

| Milestone | Theme | Status |
|-----------|--------|--------|
| M0 | Foundations (package, domain, config, ingest spine) | DONE (2026-10-02) |
| M1 | Historical portfolio risk (VaR / ES) | DONE (2026-10-02) |
| M2 | Historical + hypothetical stress + asset contribution | DONE (2026-10-02) |
| M3 | Gaussian Monte Carlo + analytic validation | NOT STARTED |
| M4 | Student-t + EWMA/GARCH (thin) + model comparison | NOT STARTED |
| M5 | Thin stochastic / path model + numerics | NOT STARTED |
| M6 | Attribution + model-risk report (flagship demo) | NOT STARTED |
| M7 | Advanced extension (only if justified) | DEFERRED |

**Current focus:** Milestone 3.

**Operating mode:** Prefer Ask-mode design → user implements → Ask-mode review.
Agents must not expand scope beyond the active milestone’s locked section.

---

## 1. Overall Architecture

Layered clean architecture. The mathematical engine must run **without** any UI
framework imported.

```
┌─────────────────────────────────────────────────────────────┐
│  Interfaces (CLI · optional Streamlit later · notebooks)    │
├─────────────────────────────────────────────────────────────┤
│  Application / Orchestration (analyze portfolio use-cases)  │
├─────────────────────────────────────────────────────────────┤
│  Domain (Portfolio, Scenario, RiskReport, protocols, errors)│
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│  Data    │ Models   │ Scenarios│ Engine   │ Measures        │
│  ingest  │ hist/par │ hist/hyp │ MC / PnL │ VaR ES DD       │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│  Attribution · Validation · Reporting · Persistence · Config│
└─────────────────────────────────────────────────────────────┘
```

**Core risk question:**  
Given portfolio weights \(w\), horizon \(h\), model \(\mathcal M\), and optional
stress scenario \(s\), estimate the loss distribution of
\(L = -w^\top R\) (or pathwise analogue), report VaR/ES, attribute drivers, and
compare across models.

**Dependency rule:** Interfaces → Application → Domain ← Infrastructure
adapters. Domain has **no** imports from `qre` infrastructure modules.
Infrastructure implements Domain protocols.

---

## 2. Suggested Directory Structure

```text
quant-risk-engine/
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── plan.md                          # this file
├── configs/
│   ├── default.yaml
│   ├── portfolios/
│   │   └── demo_spy_qqq_tlt_gld.yaml
│   └── scenarios/
│       ├── equity_crash.yaml
│       └── covid_window.yaml
├── data/                            # gitignored
│   ├── raw/
│   ├── processed/
│   └── artifacts/
├── notebooks/                       # optional research only
├── docs/
│   ├── architecture.md              # optional mirror of §1–4
│   ├── methodology.md               # risk measure definitions
│   └── milestones/
│       └── milestone_0_walkthrough.md
├── src/
│   └── qre/
│       ├── __init__.py
│       ├── py.typed
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── entities.py          # Portfolio, Position, Scenario, ...
│       │   ├── enums.py             # Horizon, ModelKind, ScenarioKind
│       │   ├── protocols.py         # MarketDataSource, RiskModel, ...
│       │   ├── errors.py
│       │   └── value_objects.py     # Weights, DateRange, AnalysisId
│       ├── application/
│       │   ├── __init__.py
│       │   ├── ingest_market_data.py
│       │   ├── build_return_matrix.py
│       │   └── run_analysis.py      # flagship use-case (from M1+)
│       ├── data/
│       │   ├── __init__.py
│       │   ├── yfinance_source.py
│       │   ├── validators.py
│       │   ├── returns.py
│       │   └── covariance.py
│       ├── models/                   # populate from M1+
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── historical.py
│       │   ├── gaussian.py
│       │   └── registry.py
│       ├── scenarios/                # populate from M2+
│       │   ├── __init__.py
│       │   ├── historical_episode.py
│       │   ├── hypothetical.py
│       │   └── registry.py
│       ├── engine/                   # populate from M3+
│       │   ├── __init__.py
│       │   ├── monte_carlo.py
│       │   └── portfolio_pnl.py
│       ├── measures/                 # populate from M1+
│       │   ├── __init__.py
│       │   ├── var.py
│       │   ├── expected_shortfall.py
│       │   └── drawdown.py
│       ├── attribution/              # populate from M2 / M6
│       ├── validation/              # analytic checks, backtests
│       ├── reporting/
│       ├── persistence/
│       ├── config/
│       ├── orchestration/
│       └── cli/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── scripts/
└── .github/
    └── workflows/
        └── ci.yml
```

Package import root: `qre` (`from qre.domain import Portfolio`).  
Product name: **Quant Risk Engine** (or “Financial Stress Testing & Risk Engine”
in README prose).

---

## 3. Modules and Responsibilities

### Domain (`qre.domain`)
- Entities: `Portfolio`, `Position`, `Scenario`, `LossDistribution`, `RiskReport`
- Protocols: `MarketDataSource`, `ReturnModel`, `ScenarioApplicator`,
  `MonteCarloEngine`, `RiskMeasure`, `ArtifactStore`
- Value objects: validated weights (sum ≈ 1), horizons, analysis IDs
- Typed errors: `DataValidationError`, `PortfolioError`, `ConfigError`,
  `ModelCalibrationError`
- Keep protocols small; avoid god-interfaces

### Data (`qre.data`)
- Fetch OHLCV via yfinance adapter
- Validate gaps/duplicates/timezone
- Build aligned simple/log return matrix
- Estimate covariance / correlation (methods grow by milestone)
- Persist raw/processed Parquet

### Models (`qre.models`)
- Historical simulation (M1)
- Gaussian / Student-t parametric (M3–M4)
- EWMA or GARCH(1,1)+CCC thin stack (M4)
- Optional factor SV / OU-vol (M5)
- Registry: config name → model factory

### Scenarios (`qre.scenarios`)
- Historical episode windows (date ranges)
- Hypothetical shocks (asset returns, vol multiplier, corr stress)
- User/custom dict scenarios
- Must document how shocks propagate into P&L (no ad-hoc magic)

### Engine (`qre.engine`)
- Portfolio P&L from returns / paths
- Monte Carlo sampling with correlated innovations
- Seed control + optional antithetic variates

### Measures (`qre.measures`)
- Expected loss, VaR, ES/CVaR, max drawdown, exceedance probability
- Always report VaR **and** ES; prefer ES in interpretive prose

### Attribution (`qre.attribution`)
- Asset contributions (linear P&L; Euler for parametric VaR/ES)
- Later: factor buckets + OFAT vol/corr sensitivities

### Validation (`qre.validation`)
- Analytic Gaussian benchmarks
- MC convergence helpers
- Stress sanity checks
- Later: VaR coverage / Kupiec

### Reporting / Persistence / Config / CLI
- HTML (or Markdown) risk memo + JSON metrics
- Parquet + artifact lineage: `config_hash` + `data_version` + `code_version`
- Pydantic settings from YAML
- Typer CLI; Streamlit only after M3 engine API is stable

---

## 4. Data Flow

```text
Config (portfolio, dates, horizon, model, scenario)
        │
        ▼
┌───────────────┐   raw Parquet    ┌────────────────┐
│  Ingestion    │ ───────────────► │ Persistence    │
└───────────────┘                  └───────┬────────┘
        │                                  │
        ▼                                  ▼
┌───────────────┐  aligned returns  ┌────────────────┐
│ Return matrix │ ◄─────────────────│  Load cache    │
└───────┬───────┘                   └────────────────┘
        ▼
┌───────────────┐
│ Calibrate     │  μ, Σ and/or model params on lookback
│ model M       │
└───────┬───────┘
        ▼
┌───────────────┐
│ Apply scenario│  optional mean/vol/corr shocks or episode replay
└───────┬───────┘
        ▼
┌───────────────┐
│ Loss samples  │  historical window and/or Monte Carlo paths
└───────┬───────┘
        ▼
┌───────────────┐
│ Measures +    │  VaR, ES, contrib, model comparison
│ Attribution   │
└───────┬───────┘
        ▼
┌───────────────┐   JSON + HTML
│ Report        │ ──────────────► data/artifacts/<analysis_id>/
└───────────────┘
```

**Non-negotiable correctness rules:**

1. Portfolio weights must be validated (finite, sum to 1 within tolerance).
2. Return matrix columns must align to portfolio assets; no silent reordering.
3. Horizon scaling assumptions must be documented (do not blindly use
   \(\sqrt{h}\) outside i.i.d. Gaussian contexts).
4. Correlation stress must end in a symmetric positive-semidefinite matrix
   (nearest-PSD if needed).
5. Every risk number in a report must be reproducible from config + cached data
   + seed (when stochastic).

---

## 5. External Libraries

| Area        | Library                                      | Role                |
|-------------|----------------------------------------------|---------------------|
| Packaging   | hatchling / setuptools + `pyproject.toml`    | installable `qre`   |
| Config      | pydantic v2, pyyaml                          | validated settings  |
| Data        | pandas, numpy, pyarrow                       | frames + Parquet    |
| Market data | yfinance (MVP)                               | OHLCV               |
| Stats       | scipy, statsmodels (as needed)               | t-dist, GARCH later |
| Viz         | matplotlib (Plotly optional)                 | research plots      |
| Reporting   | jinja2                                       | HTML memos          |
| CLI         | typer                                        | operator interface  |
| Testing     | pytest                                       | unit/integration    |
| Quality     | ruff, mypy                                   | lint/types          |

**Avoid early:** Dash/React, Airflow, paid market-data APIs, full Heston stacks,
FastAPI-first designs, Streamlit before M3.

---

## 6. What Should Be Configurable

| Category    | Examples |
|-------------|----------|
| Portfolio   | assets, weights, notional |
| Sample      | start/end, adjust prices |
| Horizon     | 1 / 10 / 21 / 63 trading days |
| Model       | historical, gaussian, student_t, ewma, garch, … |
| Scenario    | none, episode id, hypothetical YAML, custom shocks |
| MC          | n_paths, seed, antithetic on/off |
| Risk        | VaR/ES levels (e.g. 0.95, 0.99) |
| Paths       | raw/processed/artifact roots |
| Runtime     | log level, cache refresh |

Secrets only via environment. Experiment/portfolio YAMLs are git-friendly.

---

## 7. Design Patterns

| Pattern | Where | Why |
|---------|-------|-----|
| Protocol / Strategy | data source, models, measures | swap implementations |
| Registry | models, scenarios, measures | config string → object |
| Use-case | `application/run_analysis.py` | one orchestration path |
| Adapter | yfinance → domain bars | isolate vendor |
| Value Object | Weights, DateRange | fail fast |
| Artifact bundle | one analysis_id folder | reproducible demos |

**Coding conventions (agents must follow user rules):**
- NumPy-style docstrings on modules, classes, and public functions
- Module docstrings list exported objects (PEP 257)
- ≤ 5 parameters per function; ≤ 15 locals
- ≥ 2 public methods per class (avoid R0903)
- No broad `except Exception`
- No unused typing imports; no f-strings without interpolation
- Avoid magic numbers in array indexing (named constants)
- 4-space indent

---

## 8. Distinction from VIP (agents: do not blur)

| VIP | QRE |
|-----|-----|
| Symbol-centric RV forecasting | Weight-centric portfolio loss |
| QLIKE / walk-forward skill | VaR / ES / stress P&L |
| Factor screening research memo | Risk + stress + model-risk memo |
| Optional MC as forecast appendix | MC as core loss engine |

Shared ideas OK: yfinance → Parquet, Typer, Pydantic, HTML artifacts, layered
package layout. Shared *product claims* are not OK.

---

## 9. Development Roadmap

### Milestone 0 — Foundations — DONE (2026-10-02)

**Motivation.** Installable package and data spine before any risk math.

**Scope (locked):**
- `pyproject.toml`, package `qre`, ruff/mypy/pytest/CI skeleton
- Domain entities/protocols/errors/value objects for portfolio + market bars
- Config schema + `configs/default.yaml`
- Parquet persistence + logging
- yfinance adapter + OHLCV validators
- CLI `qre --help` and `qre ingest`
- Unit tests for weights validation and ingest schema (network-free fixtures
  preferred; one optional integration smoke)

**Out of scope:** VaR/ES, scenarios, Monte Carlo, Streamlit, GARCH, VIP coupling.

**Exit:**
- [ ] `pip install -e ".[dev]"` works
- [ ] `qre --help` works
- [ ] Ingest writes Parquet for at least SPY and TLT
- [ ] `pytest -q` green
- [ ] `plan.md` status → DONE with date

**Proving experiment:** ingest SPY, QQQ, TLT, GLD from a fixed start date;
inspect Parquet schemas.

---

### Milestone 1 — Historical portfolio risk — DONE (2026-10-02)
**Completed:** historical VaR/ES via `qre analyze`; demo SPY/QQQ/TLT/GLD proving run inspected.

**Motivation.** Answer: historically, how bad were portfolio losses?

**Scope (locked):**
- Build aligned return matrix for portfolio assets
- Portfolio returns \(R_{p,t}=w^\top R_t\)
- Empirical VaR / ES / mean loss / exceedance helper
- `qre analyze` (or equivalent) for historical model, no stress
- Analytic unit tests on synthetic series with known quantiles
- Minimal HTML or Markdown summary artifact

**Out of scope:** hypothetical shocks, MC, GARCH, attribution beyond raw
per-asset P&L time series (optional stretch).

**Exit:** demo portfolio VaR/ES matches a hand spreadsheet for a 2-asset fixture;
pytest green.

---

### Milestone 2 — Stress testing + asset contribution — DONE (2026-10-02)

**Completed:** historical episode + hypothetical stress via `qre stress`;
demo SPY/QQQ/TLT/GLD + equity-crash proving run inspected
(instantaneous loss 0.1145; COVID window N=41).

**Motivation.** Answer: what if markets crash / rates spike?

**Scope (locked):**
- Historical episode replay (named windows in config)
- Hypothetical shocks: asset returns, vol multiplier, correlation inflation
  with PSD projection
- Stressed P&L + asset contribution decomposition for linear P&L
- Sanity tests (100% SPY, −20% equity shock ≈ −20%)

**Out of scope:** full factor model, Euler VaR allocation (can be stretch), MC.

**Exit:** flagship demo `SPY/QQQ/TLT/GLD` + equity-crash scenario produces
stress loss + contributions report.

---

### Milestone 3 — Monte Carlo engine — NOT STARTED

**Motivation.** Forward-looking loss distribution under a calibrated Gaussian
model.

**Scope (locked):**
- Multivariate Gaussian MC with Cholesky
- Seeded reproducibility; optional antithetic variates
- VaR/ES from simulated losses
- Analytic Gaussian VaR/ES match within tolerance
- Convergence diagnostic helper/tests

**Out of scope:** Student-t, GARCH, Heston, Streamlit (thin CLI/report only).

**Exit:** MC vs closed form test passes; convergence plot or table in artifact.

---

### Milestone 4 — Heavier tails + conditional vol — NOT STARTED

**Scope (locked):** Student-t and one conditional-vol path (EWMA cov and/or
univariate GARCH + constant corr). Model comparison table for same portfolio /
horizon / scenario overlay.

**Out of scope:** DCC zoo, ranking models as universally best.

**Exit:** same book shows materially different ES across models in a crisis-like
window; documentation states assumptions.

---

### Milestone 5 — Thin stochastic model + numerics — NOT STARTED

**Scope (locked):** one justified SDE/path model (e.g. GBM multi-asset or
single-factor OU/SV on equity factor + residuals). Discretization bias /
stability experiment vs analytic benchmark where available.

**Out of scope:** full Heston multi-asset production calibration; Malliavin.

**Exit:** numerics section in methodology + tests.

---

### Milestone 6 — Attribution + model-risk productization — NOT STARTED

**Scope (locked):** Euler or equivalent asset VaR/ES contributions; OFAT
vol/corr sensitivity; polished HTML risk memo; flagship one-command demo.

**Out of scope:** live desk, auth, multi-user app.

**Exit:** one command reproduces the flagship stress + model-comparison memo.

---

### Milestone 7 — Advanced extension — DEFERRED

Only start if M6 surfaces a concrete need. Candidates (pick **one**):
- EVT for ES tails
- Robust correlation uncertainty sets
- Pathwise / LR sensitivities for ES (finite differences first)
- Bayesian parameter uncertainty → risk bands

**Malliavin calculus:** not default. Recommend only if FD/pathwise/LR are
demonstrably inadequate for a defined sensitivity problem on this engine.

---

## 10. Flagship Demo (target from M2 onward)

Portfolio:

```text
SPY  40%
QQQ  20%
TLT  25%
GLD  15%
```

Scenario sketch — Equity crash:
- equities −20%
- volatility ×1.5
- correlations increased (PSD-safe)
- rates proxy shock via TLT (config-defined)

Outputs: stress loss, asset contributions, VaR/ES, and (from M4+) model
comparison bars with caveats.

---

## 11. Agent Handoff Protocol

When an agent works on milestone \(N\):

1. Read **this file** + `docs/milestones/milestone_N_walkthrough.md` if present.
2. Implement **only** locked scope for milestone \(N\).
3. Do not mark DONE until exit checklist items are actually verified.
4. Prefer extending registries/protocols over rewriting orchestration.
5. After completion, update the Status table and milestone section with date.
6. If blocked by design ambiguity, stop and ask—do not invent a second product
   direction (no options pricing lab, no VIP clone, no Bloomberg UI).

**Challenge filter for new features:**  
Would a risk analyst use this next week on a 5-ETF book, or is it portfolio
ornament?

---

## 12. Later Backlog (not committed)

- Streamlit scenario lab (post-M3)
- Consume VIP RV forecasts as conditional vol inputs
- Kupiec / Christoffersen VaR backtests
- Factor-based stress (equity / rates / vol betas)
- Robust optimization / capital allocation under ES
- Optional FastAPI read-only artifact browser

---

## 13. Most Important Product Rule

Prefer a **small, correct risk engine with excellent validation** over a large
set of superficial models. Model diversity exists to expose **model risk**, not
to impress by count.