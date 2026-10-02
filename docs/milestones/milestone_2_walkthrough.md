# Milestone 2 Walkthrough — Stress Testing + Asset Contribution

**Status:** DONE (2026-10-02)  
**Plan reference:** `plan.md` § Milestone 2 + §10 Flagship Demo  
**Depends on:** Milestone 1 DONE (aligned returns, historical losses, VaR/ES, `qre analyze`)  
**Rule:** Stress + linear P&L contributions only. No Monte Carlo, GARCH, Euler VaR, Streamlit, or VIP.

---

## 0. Goal and exit

### Goal
Answer: **what if markets crash / rates spike?**

Reuse the M1 historical engine. Apply (1) a **historical episode** window and/or
(2) a **hypothetical** shock (asset returns, vol multiplier, correlation
inflation with PSD-safe projection). Report stressed portfolio loss, per-asset
**linear** contributions, and (where a loss sample exists) empirical VaR/ES.

### Core formulas (locked)

Portfolio return / loss (unchanged from M1):

\[
R_{p,t} = w^\top R_t,\qquad L_t = -R_{p,t}
\]

**Linear asset contribution** (required for exit; not Euler VaR):

\[
L_{i,t} = - w_i R_{i,t},\qquad \sum_i L_{i,t} = L_t
\]

For an **instantaneous** hypothetical shock vector \(s\) (one return per asset):

\[
R_p^{\text{shock}} = w^\top s,\qquad
L^{\text{shock}} = -R_p^{\text{shock}},\qquad
L_i^{\text{shock}} = -w_i s_i
\]

**Historical episode:** restrict the aligned return matrix to
\([t_{\text{start}}, t_{\text{end}}]\), then reuse M1
`HistoricalSimulationModel` + `summarize_losses`. Contributions: time-series
\(L_{i,t}\) over the window; report **mean** and/or **sum** per asset
(document which; prefer **sum** for episode P&L and **mean** as optional).

**Vol / correlation stress** (on a lookback return matrix, before replay):

1. Estimate sample covariance \(\Sigma\) (or corr \(C\) + vols \(\sigma\)).
2. Apply vol multiplier: \(\sigma_i \leftarrow m \cdot \sigma_i\) (config \(m\)).
3. Inflate correlations toward 1 (or a configured target), e.g.
   \(C' = (1-\lambda) C + \lambda\, \mathbf{1}\mathbf{1}^\top\) with
   diagonal forced to 1; clamp \(\lambda \in [0,1]\).
4. Rebuild \(\Sigma'\) from \(C'\) and \(\sigma'\); project to nearest
   symmetric PSD if needed (eigenvalue clip: set \(\lambda_j \leftarrow
   \max(\lambda_j, \varepsilon)\)).
5. **Recolor** demeaned historical returns with Cholesky (or eig) of
   \(\Sigma'\) vs \(\Sigma\) so the stressed sample has the stressed
   second-moment structure; then run historical losses/VaR/ES as in M1.

Document the recoloring map in code docstrings (no silent magic).

**Horizon:** still **1-day** units. No \(\sqrt{h}\).

### Exit checklist
- [x] Scenario YAML schema + loaders (episode + hypothetical)
- [x] Historical episode replay → VaR/ES on window + contributions
- [x] Hypothetical asset-return shocks → portfolio loss + contributions
- [x] Vol multiplier + correlation inflation with PSD projection + tests
- [x] Sanity: 100% SPY, equity shock \(-0.20\) → loss \(\approx 0.20\)
- [x] Flagship: demo portfolio + equity-crash scenario → Markdown report
      with stress loss + asset contributions (+ VaR/ES when applicable)
- [x] Network-free unit tests; `pytest -q` green; `ruff check src tests` clean
- [x] Flip M2 → DONE in `plan.md` with date; current focus → M3

### Proving experiment
1. Parquet for SPY/QQQ/TLT/GLD present (from M1 ingest).
2. Run stress on `configs/portfolios/demo_spy_qqq_tlt_gld.yaml` with
   `configs/scenarios/equity_crash.yaml`.
3. Inspect artifact: shocked loss, per-asset contributions (sum to total),
   optional stressed historical VaR/ES, caveats.
4. Run COVID (or similar) episode YAML; confirm window dates and \(N\).

---

## 1. Out of scope (do not build)

- Monte Carlo (M3)
- Student-t / EWMA / GARCH (M4)
- Euler allocation of VaR/ES (stretch only; not exit)
- Full factor / macro scenario engine
- Streamlit / FastAPI
- Multi-day \(\sqrt{h}\) scaling
- VIP imports
- Rewriting M1 historical VaR path — **call** it on filtered/stressed returns

---

## 2. Design principles

1. **One loss engine:** stressed or windowed return matrices feed
   `HistoricalSimulationModel.generate_losses` and `summarize_losses`.
2. **Scenarios are data + transforms**, not a second risk stack.
3. **Contributions are linear P&L only** in M2 (`L_i = -w_i R_i`).
4. **PSD is non-negotiable** after correlation stress (plan §4 rule 4).
5. Same coding rules as M0/M1 (NumPy docstrings, ≤5 params, ≤15 locals,
   ≥2 public methods/class, no bare `except Exception`, no unused typing,
   no f-string without interpolation, named constants, 4-space indent).

---

## 3. Suggested implementation order

1. Domain: `ScenarioKind`, thin `Scenario` / result types (stress + contributions)
2. Scenario YAML loaders (`configs/scenarios/*.yaml`)
3. `scenarios/historical_episode.py` — date-filter return matrix
4. `scenarios/hypothetical.py` — asset shocks; vol/corr stress + PSD + recolor
5. `attribution/linear.py` — contribution helpers (from returns or shock vector)
6. `application/run_stress_analysis.py` — orchestration
7. Extend Markdown report (stress section) or `reporting/stress_markdown.py`
8. CLI `qre stress` (preferred) or `qre analyze --scenario`
9. Tests (sanity SPY −20%, PSD, contributions sum, episode window)
10. Flagship proving experiment → mark DONE

---

## 4. Files to create / edit

### New
```text
configs/scenarios/equity_crash.yaml
configs/scenarios/covid_window.yaml
src/qre/domain/enums.py                 # if missing: ScenarioKind
src/qre/domain/scenarios.py             # Scenario specs / StressResult types
src/qre/scenarios/__init__.py
src/qre/scenarios/historical_episode.py
src/qre/scenarios/hypothetical.py
src/qre/scenarios/psd.py                # nearest PSD helper (small)
src/qre/scenarios/registry.py           # optional: name → loader
src/qre/attribution/__init__.py
src/qre/attribution/linear.py
src/qre/application/load_scenario.py
src/qre/application/run_stress_analysis.py
src/qre/reporting/stress_markdown.py    # or extend markdown_report.py
src/qre/cli/commands/stress.py
tests/unit/scenarios/test_historical_episode.py
tests/unit/scenarios/test_hypothetical.py
tests/unit/scenarios/test_psd.py
tests/unit/attribution/test_linear.py
tests/unit/application/test_run_stress_analysis.py
```

### Edit
```text
src/qre/domain/__init__.py
src/qre/domain/errors.py                # optional ScenarioError
src/qre/application/__init__.py
src/qre/cli/commands/__init__.py
src/qre/cli/main.py
README.md
plan.md                                 # status when DONE
docs/methodology.md                     # optional stress/contribution section
```

---

## 5. Scenario YAML contracts

### 5.1 Historical episode — `configs/scenarios/covid_window.yaml`

```yaml
name: covid_window
kind: historical_episode
start: "2020-02-15"
end: "2020-04-15"
description: "COVID crash window (illustrative)."
```

### 5.2 Hypothetical equity crash — `configs/scenarios/equity_crash.yaml`

Align with plan §10 (tune TLT/GLD in config, not in code):

```yaml
name: equity_crash
kind: hypothetical
description: "Equities down, vol up, correlations up; TLT/GLD config shocks."
asset_shocks:
  SPY: -0.20
  QQQ: -0.25
  TLT: 0.05
  GLD: 0.02
vol_multiplier: 1.5
correlation_inflation: 0.30    # λ toward all-ones corr; 0 = off
# Optional: also replay historical sample under vol/corr stress
apply_to_historical: true
```

**Semantics**
- `asset_shocks`: instantaneous simple-return shocks \(s_i\) for assets present
  in the portfolio (missing keys → 0; extra keys → `ConfigError` or ignore
  with warning — prefer **error** if not in portfolio).
- `vol_multiplier`: \(m > 0\); default `1.0` = no vol stress.
- `correlation_inflation`: \(\lambda \in [0, 1]\); default `0.0`.
- `apply_to_historical`: if true, recolor full (or lookback) return matrix and
  report stressed historical VaR/ES **in addition to** instantaneous shock P&L.

---

## 6. API contracts

### 6.1 Domain results (keep attribute count ≤7 via nesting)

```text
AssetContributions
    by_symbol: dict[str, float]
    total: float
    as_dict()
    symbols()                         # or items()

StressAnalysisResult
    portfolio_name: str
    scenario_name: str
    scenario_kind: str
    instantaneous: ...                # optional nested shock P&L + contrib
    episode_or_stressed_hist: ...     # optional nested HistoricalRiskResult-like
    contributions: AssetContributions
    as_dict()
    format_contribution_table()
```

Prefer composing with M1 `RiskSummary` / `HistoricalRiskResult` rather than
duplicating VaR/ES fields.

### 6.2 Episode filter

```text
filter_returns_by_episode(returns, start, end) -> DataFrame
```

Raise `DataValidationError` if the window is empty after filtering.

### 6.3 Hypothetical + cov stress

```text
apply_asset_shocks(weights_or_portfolio, shocks) -> (loss, AssetContributions)

estimate_covariance(returns) -> ndarray
inflate_correlation(corr, lambda_) -> ndarray
apply_vol_multiplier(cov, multiplier) -> ndarray
nearest_psd(matrix, epsilon) -> ndarray
recolor_returns(returns, cov_base, cov_stressed) -> DataFrame
```

Keep ≤5 params; bundle cov options in a small frozen `HypoStressParams`
if needed.

### 6.4 Attribution

```text
contributions_from_returns(portfolio, return_matrix) -> DataFrame
    # columns = tickers, values = L_{i,t} = -w_i R_{i,t}

aggregate_contributions(contrib_frame, how="sum"|"mean") -> AssetContributions
```

**Invariant (test):** `contrib_frame.sum(axis=1)` ≈ portfolio losses.

### 6.5 Application

```text
run_stress_analysis(deps, portfolio_spec, scenario, alphas, artifact_dir)
    -> StressAnalysisOutcome  # result + report_path
```

Steps:
1. Load aligned returns (M1 `build_aligned_return_matrix`).
2. Branch on `scenario.kind`.
3. Instantaneous shocks (if hypothetical) → loss + contributions.
4. Episode filter and/or recolor → `generate_losses` + `summarize_losses`.
5. Write Markdown artifact under `data/artifacts/stress/<analysis_id>/`.
6. Return outcome.

---

## 7. Reporting

Markdown must include:
- Portfolio name, weights, notional
- Scenario name/kind + key parameters
- Instantaneous stress loss (if any) and contribution table (must sum to total)
- If historical/episode/recolored sample present: \(N\), dates, mean loss, VaR/ES
- Caveats: hypothetical ≠ forecast; corr stress uses PSD projection; 1-day;
  linear contributions ≠ Euler VaR

Stdlib string template is fine (same as M1).

---

## 8. CLI — `qre stress`

Register like ingest/analyze (`Annotated` + `typer.Option`, avoid Ruff B008).

Suggested options (≤5 on the command):

| Option | Role |
|--------|------|
| `--portfolio` | Portfolio YAML (default: demo) |
| `--scenario` | Scenario YAML (required) |
| `--alpha` | Repeatable; default 0.95, 0.99 |
| `--config` | App config for paths |

Example:

```bash
qre stress --portfolio configs/portfolios/demo_spy_qqq_tlt_gld.yaml --scenario configs/scenarios/equity_crash.yaml
qre stress --scenario configs/scenarios/covid_window.yaml --alpha 0.95 --alpha 0.99
```

---

## 9. Tests (required)

### Sanity (exit)
- Portfolio 100% SPY, shock `SPY: -0.20` → loss ≈ `0.20`, contribution SPY ≈ `0.20`.

### Contributions
- Two-asset equal weight, known returns → \(L_i\) and \(\sum L_i = L_p\).

### Episode
- Synthetic dated returns; window keeps expected rows only; empty window errors.

### PSD / corr
- Inflated corr is symmetric, unit diagonal, eigenvalues ≥ 0 after projection.
- Vol multiplier scales variances by \(m^2\) (if applied via vol on diag).

### Application
- `tmp_path` Parquet + equity-like YAML → `report.md` exists; contribution
  total matches portfolio shock loss within tolerance.

Network-free only for unit tests.

---

## 10. Coding conventions (same as M1)

- NumPy docstrings; module export lists
- ≤5 parameters; ≤15 locals
- ≥2 public methods per class
- No broad `except Exception`
- No unused typing imports; no f-string without interpolation
- Named constants instead of magic indices
- Prefer protocols; add `ScenarioApplicator` only if it clarifies design

---

## 11. Agent / Ask-mode batches (recommended)

| Batch | Scope |
|-------|--------|
| B1 | Domain enums/results + scenario YAML loader + tests |
| B2 | Episode filter + linear attribution + tests |
| B3 | Hypothetical shocks + vol/corr/PSD/recolor + tests |
| B4 | `run_stress_analysis` + Markdown + tests |
| B5 | CLI `qre stress` + README + proving experiment |

Do **not** start B4 before B1–B3 contracts exist.

---

## 12. After M2

1. Mark M2 DONE in `plan.md`; current focus → M3  
2. Draft `docs/milestones/milestone_3_walkthrough.md` (Gaussian MC)  
3. Keep scenario application **in front of** the loss engine — M3 should
   consume the same contribution helpers where linear P&L still applies  

---

## 13. Challenge filter

> Would a risk analyst use this next week on a 5-ETF book?

M2 yes: named crash window + explicit shock table + contribution breakdown.  
Skip: fancy UI, Euler VaR theater, factor zoo, multiple corr-stress recipes without tests.
