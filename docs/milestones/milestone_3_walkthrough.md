# Milestone 3 Walkthrough — Gaussian Monte Carlo + Analytic Validation

**Status:** DONE (2026-10-03)
**Plan reference:** `plan.md` § Milestone 3  
**Depends on:** Milestone 2 DONE (aligned returns, historical losses, VaR/ES, stress)  
**Rule:** Gaussian MC + closed-form checks only. No Student-t, GARCH, Streamlit, or Euler VaR.

---

## 0. Goal and exit

### Goal
Answer: **under a calibrated multivariate Gaussian, what is the forward loss distribution?**

Estimate \(\mu, \Sigma\) on a lookback return matrix, draw correlated returns via
Cholesky, form portfolio losses \(L = -w^\top R\), compute empirical VaR/ES on
the MC sample, and prove they match analytic Gaussian VaR/ES within tolerance.
Emit a thin Markdown report + a convergence table/plot artifact.

### Core formulas (locked)

Simple returns / portfolio loss (same sign convention as M1):

\[
R_p = w^\top R,\qquad L = -R_p
\]

**Calibration** (sample mean and covariance on lookback; document ddof):

\[
\hat\mu = \frac{1}{T}\sum_t R_t,\qquad
\hat\Sigma = \mathrm{Cov}(R)\ \text{(PSD-safe if needed)}
\]

**Cholesky MC** with seed \(s\), \(N\) paths, \(Z\sim\mathcal{N}(0,I)\):

\[
\hat\Sigma = LL^\top,\qquad
R^{(k)} = \hat\mu + L Z^{(k)}
\quad\text{(or } R = \hat\mu + Z L^\top\text{ with consistent layout)}
\]

Optional **antithetic:** for each draw \(Z\), also use \(-Z\) (count both toward \(N\);
require even \(N\) when antithetic is on).

Portfolio under \(R\sim\mathcal{N}(\mu,\Sigma)\):

\[
R_p\sim\mathcal{N}(\mu_p,\sigma_p^2),\quad
\mu_p=w^\top\mu,\quad
\sigma_p=\sqrt{w^\top\Sigma w}
\]

\[
L\sim\mathcal{N}(-\mu_p,\sigma_p^2)
\]

**Analytic** (loss convention, \(\alpha\in(0,1)\)):

\[
\mathrm{VaR}_\alpha = \mu_L + \sigma_L\,\Phi^{-1}(\alpha)
\]

\[
\mathrm{ES}_\alpha = \mu_L + \sigma_L\,\frac{\phi\bigl(\Phi^{-1}(\alpha)\bigr)}{1-\alpha}
\]

with \(\mu_L=-\mu_p\), \(\sigma_L=\sigma_p\).

**MC measures:** reuse `summarize_losses` / `var` / `expected_shortfall` on the
simulated loss vector (same quantile method as M1).

**Horizon:** **1-day** only for exit. Do not introduce \(\sqrt{h}\) / \(h\)-scaling
in M3 (document deferral). Reject `horizon_days != 1` if a flag is exposed.

**Scenario position:** if a shocked \((\mu',\Sigma')\) is supplied (e.g. from M2
vol/corr stress), apply it **before** sampling. The MC engine itself only
samples and maps returns → losses. Scenario+MC CLI wiring may be thin or
deferred as long as the engine accepts calibrated params as inputs.

### Exit checklist
- [x] `data/covariance.py` (or equivalent) — mean/cov + PSD guard
- [x] `models/gaussian.py` — calibrate \(\mu,\Sigma\) from return matrix
- [x] `engine/monte_carlo.py` — Cholesky sampling, seed, optional antithetic
- [x] `engine/portfolio_pnl.py` — \(L=-R w\) (shared with MC / analytic path)
- [x] `validation/gaussian_analytic.py` — closed-form VaR/ES
- [x] `validation/convergence.py` — helper + test (table or running VaR/ES vs \(N\))
- [x] Unit test: MC VaR/ES within tolerance of analytic (fixed seed, large \(N\))
- [x] Unit test: same seed → identical losses; antithetic shape/parity checks
- [x] Application + Markdown report + thin CLI (`qre mc` or `analyze --model gaussian`)
- [x] Demo portfolio end-to-end; convergence artifact written
- [x] `scipy` (or documented numpy-only equiv) in dependencies
- [x] `pytest -q` green; `ruff check src tests` clean
- [x] Flip M3 → DONE in `plan.md` with date; current focus → M4

### Proving experiment
1. Parquet for SPY/QQQ/TLT/GLD present.
2. Run Gaussian MC on `configs/portfolios/demo_spy_qqq_tlt_gld.yaml`
   (e.g. \(N=50{,}000\), seed fixed, alphas 0.95/0.99).
3. Inspect artifact: MC VaR/ES vs analytic, abs/rel error, seed, \(N\), antithetic flag.
4. Inspect convergence table/plot: VaR/ES stabilize as \(N\) grows.

---

## 1. Out of scope (do not build)

- Student-t / EWMA / GARCH (M4)
- Stochastic vol / SDEs (M5)
- Euler VaR/ES attribution (M6)
- Streamlit / FastAPI
- Multi-day horizon scaling
- VIP imports
- Rewriting M1/M2 paths — **call** existing measures and (optionally) scenario
  calibration helpers

---

## 2. Design principles

1. **Sampler is dumb:** inputs are \(\mu,\Sigma,w,N,\mathrm{seed},\mathrm{antithetic}\);
   output is loss samples (and optionally return paths).
2. **Calibrate outside the engine:** `GaussianReturnModel.calibrate(returns)`.
3. **One measure stack:** MC losses → existing empirical VaR/ES.
4. **Validation is first-class:** analytic match is an exit criterion, not a demo nicety.
5. **≤5 params / function:** pack MC knobs into a frozen `MonteCarloSpec`
   (n_paths, seed, antithetic).

---

## 3. Suggested implementation order

1. Domain: `ModelCalibrationError`; thin result types (`MonteCarloRiskResult`)
2. `data/covariance.py` — sample mean/cov + reuse `nearest_psd` if needed
3. `models/gaussian.py` — calibrate; expose \(\mu,\Sigma\)
4. `engine/portfolio_pnl.py` — weights × returns → losses
5. `engine/monte_carlo.py` — Cholesky + seed + antithetic
6. `validation/gaussian_analytic.py` + convergence helper
7. Unit tests (analytic match, seed, antithetic, degenerate Σ)
8. `application/run_monte_carlo_analysis.py` + Markdown report
9. CLI command
10. Proving experiment → mark DONE; draft M4 walkthrough stub note

---

## 4. Files to create / edit

### New
```text
src/qre/data/covariance.py
src/qre/models/gaussian.py
src/qre/engine/__init__.py
src/qre/engine/monte_carlo.py
src/qre/engine/portfolio_pnl.py
src/qre/validation/__init__.py
src/qre/validation/gaussian_analytic.py
src/qre/validation/convergence.py
src/qre/application/run_monte_carlo_analysis.py
src/qre/reporting/monte_carlo_markdown.py
src/qre/cli/commands/monte_carlo.py   # or extend analyze
tests/unit/data/test_covariance.py
tests/unit/models/test_gaussian.py
tests/unit/engine/test_monte_carlo.py
tests/unit/engine/test_portfolio_pnl.py
tests/unit/validation/test_gaussian_analytic.py
tests/unit/validation/test_convergence.py
tests/unit/application/test_run_monte_carlo_analysis.py
docs/milestones/milestone_3_walkthrough.md
```

### Edit
```text
pyproject.toml                         # add scipy
src/qre/domain/errors.py               # ModelCalibrationError
src/qre/domain/risk.py                 # MonteCarloRiskResult (or new module)
src/qre/domain/protocols.py            # optional MonteCarloEngine / ReturnModel
src/qre/models/__init__.py
src/qre/cli/main.py
src/qre/cli/commands/__init__.py
README.md                              # short MC section
plan.md                                # status flip only when exit met
```

---

## 5. API sketches (contracts)

```python
@dataclass(frozen=True, slots=True)
class GaussianParams:
    mu: np.ndarray          # shape (N,)
    cov: np.ndarray         # shape (N, N), PSD
    symbols: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class MonteCarloSpec:
    n_paths: int
    seed: int
    antithetic: bool = False

class GaussianReturnModel:
    def calibrate(self, return_matrix: pd.DataFrame) -> GaussianParams: ...
    def params(self) -> GaussianParams: ...  # second public method

class GaussianMonteCarloEngine:
    def sample_returns(self, params: GaussianParams, spec: MonteCarloSpec) -> np.ndarray: ...
    def sample_losses(
        self,
        params: GaussianParams,
        weights: np.ndarray,
        spec: MonteCarloSpec,
    ) -> np.ndarray: ...
```

Analytic:

```python
def gaussian_var(mu_l: float, sigma_l: float, alpha: float) -> float: ...
def gaussian_es(mu_l: float, sigma_l: float, alpha: float) -> float: ...
def portfolio_loss_moments(mu: np.ndarray, cov: np.ndarray, weights: np.ndarray) -> tuple[float, float]: ...
```

Tolerance guidance for tests (lock in walkthrough when implementing):
relative error on VaR/ES \(\lesssim 1\%\) at \(N \ge 100{,}000\), fixed seed;
or absolute tolerance scaled to \(\sigma_L / \sqrt{N}\). Document the choice in the test.

---

## 6. Agent / Ask-mode batches

| Batch | Scope |
|-------|--------|
| B1 | Errors + result types + covariance + Gaussian calibrate + tests |
| B2 | `portfolio_pnl` + MC engine (seed, antithetic) + tests |
| B3 | Analytic VaR/ES + MC-vs-analytic test + convergence helper |
| B4 | `run_monte_carlo_analysis` + Markdown + CLI |
| B5 | Proving experiment + `plan.md` DONE + README |

Do **not** start B4 before B1–B3 contracts and the analytic match test exist.

---

## 7. After M3

1. Mark M3 DONE in `plan.md`; current focus → M4  
2. Draft `docs/milestones/milestone_4_walkthrough.md` (Student-t + thin EWMA/GARCH)  
3. Keep model registry ready: config name → factory (`historical` / `gaussian` / …)