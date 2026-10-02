Save as:
# Milestone 1 Walkthrough — Historical Portfolio Risk

**Status:** DONE (2026-10-02)  
**Plan reference:** `plan.md` § Milestone 1  
**Depends on:** Milestone 0 DONE (ingest → `data/raw/{SYMBOL}/ohlcv.parquet`)  
**Rule:** Historical risk only. No stress scenarios, Monte Carlo, GARCH, or Streamlit.

---

## 0. Goal and exit

### Goal
Answer: **historically, how bad were portfolio losses?**

Given a portfolio (weights + assets), load aligned historical returns, form
portfolio P&L / loss series, and report empirical risk measures (mean loss,
VaR, ES, optional exceedance probability). Emit a minimal Markdown (or HTML)
summary artifact.

### Core formulas (locked)

Simple returns from close prices:

\[
R_{i,t} = \frac{P_{i,t}}{P_{i,t-1}} - 1
\]

Aligned portfolio return:

\[
R_{p,t} = \sum_i w_i R_{i,t} = w^\top R_t
\]

Loss (positive = loss):

\[
L_t = - R_{p,t}
\]

For empirical sample \(\{L_t\}_{t=1}^T\) and level \(\alpha \in (0,1)\)
(e.g. \(0.95\), \(0.99\)):

- **VaR\(_\alpha\)** = empirical \(\alpha\)-quantile of \(L\)  
  (use a documented estimator; prefer NumPy `quantile` with a fixed method,
  e.g. `method="linear"`, and lock it in tests).
- **ES\(_\alpha\)** (Expected Shortfall / CVaR) =
  \(\mathbb{E}[L \mid L \ge \mathrm{VaR}_\alpha]\) estimated as the mean of
  losses strictly at or above the VaR threshold (document tie handling).
- **Mean loss** = \(\frac{1}{T}\sum_t L_t\)
- **Exceedance** = \(\frac{1}{T}\#\{t : L_t > x\}\) for a user threshold \(x\)

**Horizon (M1):** work in **1-day** returns only. Do **not** scale by
\(\sqrt{h}\) yet. Optional CLI flag `--horizon-days` may be accepted but must
either reject `h != 1` or clearly document that multi-day aggregation is
deferred to a later milestone (prefer reject / ignore with message).

### Exit checklist
- [x] Aligned return matrix from Parquet closes for portfolio symbols
- [x] Portfolio loss series \(L_t = -w^\top R_t\)
- [x] Empirical mean loss, VaR, ES, exceedance helpers with unit tests
- [x] Synthetic fixture: VaR/ES match hand / closed-form known values
- [x] 2-asset spreadsheet-style fixture test green
- [x] `qre analyze` (historical) writes a Markdown (or HTML) artifact
- [x] Demo portfolio `configs/portfolios/demo_spy_qqq_tlt_gld.yaml` runs end-to-end
      using ingested Parquet (or a checked-in tiny fixture for CI)
- [x] `pytest -q` green; `ruff check src tests` clean
- [x] Flip M1 → DONE in `plan.md` with date; set current focus to M2

### Proving experiment
1. Ensure SPY/QQQ/TLT/GLD Parquet exist (`qre ingest --all-universe --start 2015-01-01`).
2. Run analyze on the demo portfolio at 95% and 99%.
3. Inspect artifact: portfolio VaR/ES, sample size, date span, weights.
4. Manually spot-check a 2-asset toy case against Excel/Sheets.

---

## 1. Out of scope (do not build)

- Hypothetical / historical stress scenarios (M2)
- Monte Carlo (M3)
- Student-t / GARCH / EWMA risk models (M4)
- Stochastic vol / SDEs (M5)
- Euler VaR attribution, factor attribution (M2/M6) — optional stretch only:
  per-asset contribution time series \(L_{i,t} = -w_i R_{i,t}\) may be stored
  for diagnostics, but **not** required for exit
- Streamlit / FastAPI
- Multi-day horizon scaling via \(\sqrt{h}\)
- VIP imports

---

## 2. Suggested implementation order

1. Domain/result types for a historical risk report (thin)
2. `data/returns.py` — closes → return matrix (aligned, inner join)
3. Portfolio YAML loader (config helper)
4. `measures/` — VaR, ES, mean loss, exceedance
5. `models/historical.py` — historical simulation adapter
6. `application/run_historical_analysis.py` — orchestration
7. Minimal Markdown report writer
8. CLI `qre analyze`
9. Tests (synthetic + 2-asset fixture + optional smoke)
10. Docs touch (`plan.md`, short methodology note optional)
11. Proving experiment → mark DONE

---

## 3. Files to create / edit

### New
```text
src/qre/data/returns.py
src/qre/measures/__init__.py
src/qre/measures/empirical.py
src/qre/models/__init__.py
src/qre/models/historical.py
src/qre/application/run_historical_analysis.py
src/qre/application/load_portfolio.py          # or under config/
src/qre/reporting/__init__.py
src/qre/reporting/markdown_report.py
src/qre/cli/commands/analyze.py
src/qre/domain/risk.py                         # LossSeries / HistoricalRiskResult
tests/fixtures/returns_two_asset.csv           # or parquet + weights yaml
tests/unit/data/test_returns.py
tests/unit/measures/test_empirical.py
tests/unit/models/test_historical.py
tests/unit/application/test_run_historical_analysis.py
docs/methodology.md                            # optional short M1 section
```

### Edit
```text
src/qre/cli/main.py                  # register analyze_command
src/qre/cli/commands/__init__.py
src/qre/application/__init__.py
src/qre/data/__init__.py
src/qre/config/schema.py             # optional: risk levels defaults
configs/default.yaml                 # optional: risk.alphas: [0.95, 0.99]
plan.md                              # status when DONE
README.md                            # document qre analyze
```

---

## 4. Mathematical / API contracts

### 4.1 Returns (`data/returns.py`)

```text
load_close_prices(store, symbols) -> DataFrame
    # columns = ticker strings, index = dates, values = close

compute_simple_returns(prices) -> DataFrame
    # pct_change; drop first NA row

align_return_matrix(returns_by_symbol) -> DataFrame
    # inner-join on dates; drop rows with any NA
```

Rules:
- Read from `ParquetMarketDataStore.load(symbol)` (already validated OHLCV).
- Use `close` only for M1.
- Column order should match portfolio symbol order when building \(R_t\).
- Raise `DataValidationError` if a symbol is missing from the store or has
  insufficient rows (< 2 price rows).

Keep ≤5 params per function; use a small deps object if needed.

### 4.2 Portfolio loading

Parse `configs/portfolios/*.yaml`:

```yaml
name: demo_spy_qqq_tlt_gld
notional: 1000000
positions:
  SPY: 0.40
  ...
```

→ `Portfolio.from_weights(name, Weights.from_mapping(positions))`  
Notional may be stored on a small `PortfolioSpec` wrapper if you do not want to
extend the frozen `Portfolio` entity yet:

```text
PortfolioSpec(portfolio: Portfolio, notional: float)
```

M1 risk measures on **returns/losses in decimal** do not require notional for
VaR/ES in percent terms; report notional in the artifact for context only.
Optional: also report VaR in currency = `VaR * notional`.

### 4.3 Empirical measures (`measures/empirical.py`)

```text
mean_loss(losses: ndarray | Series) -> float
var(losses, alpha: float) -> float
expected_shortfall(losses, alpha: float) -> float
exceedance_probability(losses, threshold: float) -> float
summarize_losses(losses, alphas: sequence[float]) -> RiskSummary
```

Lock conventions in docstrings + tests:

| Item | M1 choice |
|------|-----------|
| Loss sign | \(L = -R_p\) (positive = loss) |
| VaR estimator | `numpy.quantile(losses, alpha, method="linear")` |
| ES | mean of `{L : L >= VaR}` ; if empty (degenerate), raise or return VaR |
| Alpha | require `0 < alpha < 1` |
| Empty sample | raise `DataValidationError` |

**Product stance (from plan):** always compute VaR **and** ES; prose should
prefer ES as the severity measure.

### 4.4 Historical model (`models/historical.py`)

Thin adapter (registry-ready for M3+):

```text
class HistoricalSimulationModel:
    def generate_losses(self, portfolio, return_matrix) -> ndarray
        # L_t = - return_matrix.values @ weights_vector
```

No calibration beyond using the empirical window as-is.

### 4.5 Result types (`domain/risk.py`)

```text
HistoricalRiskResult
    portfolio_name: str
    n_obs: int
    start_date: str
    end_date: str
    alphas: tuple[float, ...]
    mean_loss: float
    var_by_alpha: dict[float, float]
    es_by_alpha: dict[float, float]
    # optional: exceedance_by_threshold
```

≥2 public methods, e.g. `as_dict()`, `format_var_line(alpha)`.

### 4.6 Application use-case

```text
run_historical_analysis(spec, store, alphas, artifact_dir) -> HistoricalRiskResult
```

Steps:
1. Load portfolio spec  
2. Load closes → returns → align  
3. Historical losses  
4. Summarize measures  
5. Write Markdown artifact under `data/artifacts/historical/<analysis_id>/`  
6. Return result  

`analysis_id`: timestamp + portfolio name slug is enough for M1
(e.g. `demo_spy_qqq_tlt_gld_20261002T120000`).

Use `IngestDeps`-style `AnalysisDeps(store=...)` if it helps param limits.

---

## 5. Reporting (minimal)

`reporting/markdown_report.py`:

Write `report.md` containing:
- Portfolio name, weights table, notional
- Sample period and \(N\)
- Mean loss
- VaR / ES for each alpha (as %, 2–4 decimal places)
- Caveats: historical simulation; 1-day; past ≠ future; no stress overlay

No Jinja required if an f-string / `str` template is clearer; Jinja2 may be
added when you introduce it as a dependency (not in M0). Prefer **stdlib-only**
Markdown writer in M1 unless you already added jinja2.

Optional: also write `metrics.json` for reproducibility (nice, not required).

---

## 6. CLI — `qre analyze`

Register like ingest (`Annotated` + `typer.Option` to avoid Ruff B008).

Suggested options (≤5 parameters on the command function):

| Option | Role |
|--------|------|
| `--portfolio` | Path to portfolio YAML (default: demo path) |
| `--alpha` | Repeatable confidence level (default 0.95, 0.99) |
| `--config` | Optional app config (paths) |
| `--start` / `--end` | Optional date filter on the return sample |

If five slots are tight, fold dates into config-only for M1 and only expose
`--portfolio`, `--alpha`, `--config`.

Behavior:
1. Resolve `raw_dir` like ingest  
2. Run historical analysis  
3. Echo key metrics + artifact path  

Example:

```bash
qre analyze --portfolio configs/portfolios/demo_spy_qqq_tlt_gld.yaml
qre analyze --portfolio configs/portfolios/demo_spy_qqq_tlt_gld.yaml --alpha 0.95 --alpha 0.99
```

---

## 7. Tests (required)

### `test_empirical.py` (synthetic, known answers)

Construct a tiny loss vector with a hand-computed VaR/ES.

Example approach:
- losses = `[0.01, 0.02, 0.03, 0.04, 0.10]`
- Pick alpha and assert VaR equals `numpy.quantile(..., method="linear")`
- Assert ES equals mean of losses `>= VaR`

Also test:
- invalid alpha → error  
- empty losses → error  

### `test_returns.py`
- Two price series → correct simple returns  
- Misaligned dates → inner join length  
- Missing symbol / short history → `DataValidationError`

### `test_historical.py`
- Weights `[0.5, 0.5]`, known return matrix → known \(L_t\)

### `test_run_historical_analysis.py` (network-free)
- Write tiny OHLCV Parquet for 2 symbols into `tmp_path` via `ParquetMarketDataStore`
- Portfolio 50/50  
- Run analysis → check result fields + `report.md` exists  

### Spreadsheet / hand check (exit)
Document in the test docstring the Excel formula check for the 2-asset fixture
so an interviewer can reproduce it.

---

## 8. Config defaults (optional)

In `configs/default.yaml`:

```yaml
risk:
  alphas:
    - 0.95
    - 0.99
```

Add `RiskConfig` to `schema.py` if you do this; otherwise hardcode defaults in
CLI (`[0.95, 0.99]`).

---

## 9. Coding conventions (same as M0)

- NumPy docstrings; module export lists  
- ≤5 parameters; ≤15 locals  
- ≥2 public methods per class  
- No broad `except Exception`  
- No unused typing imports; no f-string without interpolation  
- Named constants instead of magic indices  
- Prefer protocols already defined; add new ones only if needed
  (`ReturnModel` can wait until M3)

---

## 10. Agent split (optional)

| Agent | Scope |
|-------|--------|
| B1 | `returns.py` + portfolio YAML loader + tests |
| B2 | `measures/empirical.py` + `domain/risk.py` + tests |
| B3 | historical model + `run_historical_analysis` + markdown report |
| B4 | CLI `analyze` + README + proving experiment |

Or file-by-file Ask mode in one chat (recommended for learning).

Do **not** parallelize B3 before B1/B2 contracts exist.

---

## 11. After M1

1. Mark M1 DONE in `plan.md`; current focus → M2  
2. Draft `docs/milestones/milestone_2_walkthrough.md` (stress + asset contrib)  
3. Keep historical engine stable — M2 should **call** it under shocked returns /
   windows, not fork a second risk stack  

---

## 12. Challenge filter

> Would a risk analyst use this next week on a 5-ETF book?

M1 yes: empirical VaR/ES on a real book from prices.  
Skip: five quantile estimators, Plotly dashboards, currency VaR without clear
units, multi-horizon \(\sqrt{h}\) without documentation.

---