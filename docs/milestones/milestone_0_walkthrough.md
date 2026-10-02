# Milestone 0 Walkthrough — Foundations

**Status:** DONE (2026-10-02) 
**Plan reference:** `plan.md` § Milestone 0  
**Rule:** Implement only what is listed here. No VaR, ES, stress, Monte Carlo, or Streamlit.

---

## 0. Goal and exit

### Goal
Stand up an installable Python package with a clean domain layer, validated
config, Parquet persistence, yfinance OHLCV ingest, and a Typer CLI.

### Exit checklist
- [x] `pip install -e ".[dev]"` succeeds
- [x] `qre --help` shows the app
- [x] `qre ingest --symbol SPY` (and TLT) writes Parquet under `data/raw/`
- [x] Unit tests for weights + OHLCV validation are network-free and green
- [x] `pytest -q` green
- [x] Flip M0 to DONE in `plan.md` with the date

### Proving experiment
Ingest `SPY`, `QQQ`, `TLT`, `GLD` from `2015-01-01` and inspect Parquet schemas
(columns `open, high, low, close, volume`; datetime index; no NaNs in prices).

---

## 1. Out of scope (do not build)

- Returns matrices, covariance, VaR/ES
- Scenarios / stress
- Monte Carlo
- `models/`, `measures/`, `engine/`, `attribution/` logic beyond empty `__init__.py` placeholders (optional; prefer omit unused packages)
- Streamlit / FastAPI
- VIP imports or VIP package dependency
- Paid data vendors

Empty placeholder packages for later milestones are **optional**. Prefer creating
directories only when M1+ needs them.

---

## 2. Suggested implementation order

Do these in order; each step should leave tests (or CLI) runnable.

1. Repo root files (`pyproject.toml`, `.gitignore`, `README.md`)
2. Package skeleton (`src/qre/...`)
3. Domain: errors → enums → value objects → entities → protocols
4. Config: schema + loader + `configs/default.yaml`
5. Persistence: Parquet store
6. Orchestration: logging
7. Data: validators → yfinance source → ingest use-case
8. CLI: `qre --help`, `qre ingest`
9. Tests + optional CI workflow
10. Proving experiment + mark DONE

---

## 3. Files to create

### Root
```text
pyproject.toml
README.md
.gitignore
configs/default.yaml
configs/portfolios/demo_spy_qqq_tlt_gld.yaml   # portfolio YAML ok in M0; unused by CLI until M1
.github/workflows/ci.yml                        # optional but recommended
```

### Package
```text
src/qre/__init__.py                 # __version__
src/qre/py.typed
src/qre/domain/__init__.py
src/qre/domain/errors.py
src/qre/domain/enums.py
src/qre/domain/value_objects.py
src/qre/domain/entities.py
src/qre/domain/protocols.py
src/qre/config/__init__.py
src/qre/config/schema.py
src/qre/config/loader.py
src/qre/persistence/__init__.py
src/qre/persistence/parquet_store.py
src/qre/orchestration/__init__.py
src/qre/orchestration/logging.py
src/qre/data/__init__.py
src/qre/data/validators.py
src/qre/data/yfinance_source.py
src/qre/application/__init__.py
src/qre/application/ingest_market_data.py
src/qre/cli/__init__.py
src/qre/cli/main.py
src/qre/cli/commands/__init__.py
src/qre/cli/commands/ingest.py
```

### Tests
```text
tests/unit/domain/test_weights.py
tests/unit/domain/test_date_range.py
tests/unit/data/test_validators.py
tests/unit/config/test_loader.py
tests/unit/persistence/test_parquet_store.py
tests/unit/application/test_ingest_market_data.py   # fake source; no network
tests/fixtures/ohlcv_spy_sample.csv                 # tiny synthetic OHLCV
```

Optional later: `tests/integration/test_yfinance_smoke.py` marked `@pytest.mark.integration`.

---

## 4. `pyproject.toml` contract

Mirror VIP’s packaging style:

- build: hatchling
- project name: `quant-risk-engine`
- package dir: `src/qre`
- Python: `>=3.11`
- runtime deps (M0): `pandas`, `pyarrow`, `pydantic`, `pydantic-settings`,
  `pyyaml`, `typer`, `yfinance`
- **do not** add scikit-learn / statsmodels / jinja2 yet (M1+ / reporting)
- optional `dev`: `pytest`, `ruff`, `mypy`, `pandas-stubs`, `types-PyYAML`
- script entry: `qre = "qre.cli.main:app"`
- `[tool.pytest.ini_options]`: `testpaths = ["tests"]`, `pythonpath = ["src"]`
- ruff / mypy configured similarly to VIP

`.gitignore` must include `data/`, `.venv/`, `__pycache__/`, `.pytest_cache/`,
`.mypy_cache/`, `dist/`, `*.egg-info/`.

---

## 5. Domain layer (detail)

### 5.1 `errors.py`
Typed exceptions (subclasses of `Exception`, not bare `Exception` catches later):

- `QreError` (base)
- `DataValidationError`
- `PortfolioError`
- `ConfigError`

Each: short docstring; optional `message` attribute if useful.

### 5.2 `enums.py`
Keep minimal for M0:

- `PriceField` or just document column names as constants in validators
- Optional: `AssetClass` (`EQUITY`, `RATES_PROXY`, `COMMODITY`, `OTHER`) — only if used

Do **not** invent ModelKind/ScenarioKind until M1/M2 unless you want stubs;
prefer adding when used.

### 5.3 `value_objects.py`

**`Symbol`**
- Normalize ticker: strip, upper-case
- Reject empty
- Methods: e.g. `as_yahoo_ticker()` using a small alias map (`VIX`→`^VIX`,
  `TNX`→`^TNX`) **or** keep aliases only in the yfinance adapter (VIP style).
  Prefer aliases in `yfinance_source.py` to keep domain vendor-free.

**`DateRange`**
- `start: date`, `end: date`
- Validate `start <= end`
- Methods: `contains(day)`, `to_iso_pair()` (or similar) — need ≥2 public methods

**`Weights`**
- Mapping symbol → float weight
- Validate: finite, sum within tolerance of 1.0 (e.g. `abs(sum-1) <= 1e-8`)
- Reject empty / negative weights for M0 long-only (document; simplify)
- Methods: `symbols()`, `as_series()` or `normalized()` — ≥2 public methods

**`AnalysisId`** (optional stub)
- Opaque string id for later artifacts; can wait until M1

### 5.4 `entities.py`

**`Position`**
- `symbol: Symbol`, `weight: float`
- Methods: `is_long()`, `notional(total: float)` or similar

**`Portfolio`**
- Name + tuple/list of `Position`, or construct from `Weights`
- Validate unique symbols; weights sum ≈ 1 via `Weights`
- Methods: `symbols()`, `weight_vector()` / `to_weights()`
- This is the flagship domain object for later milestones — get validation right

**`Instrument`** (optional, VIP-like)
- symbol + currency; useful but not mandatory if `Symbol` + portfolio suffice

**`DatasetRef`**
- symbol + relative path + optional content hash — used by persistence lineage

Do **not** define `RiskReport` / `Scenario` fully unless skinny stubs; better wait
for M1/M2 so protocols stay honest.

### 5.5 `protocols.py`

```text
MarketDataSource
    fetch(symbol, date_range) -> DataFrame
    source_name() -> str

MarketDataStore
    save(symbol, frame) -> None
    load(symbol) -> DataFrame
    exists(symbol) -> bool
```

Use `@runtime_checkable` + `Protocol`.  
Pandas at the boundary is OK (same as VIP).

---

## 6. Config

### `configs/default.yaml`
```yaml
universe:
  symbols:
    - SPY
    - QQQ
    - TLT
    - GLD

date_range:
  start: "2015-01-01"
  end: null

paths:
  raw_dir: data/raw
  processed_dir: data/processed
  artifacts_dir: data/artifacts

logging:
  level: INFO
```

`end: null` means “through latest available” at ingest time (resolve to
`date.today()` in code when building `DateRange`).

### `schema.py`
Pydantic models: `DateRangeConfig`, `PathsConfig`, `LoggingConfig`,
`UniverseConfig`, `AppConfig`.

### `loader.py`
- `load_config(path: Path | str | None = None) -> AppConfig`
- Default path: `configs/default.yaml` relative to cwd (document this)
- Raise `ConfigError` on missing file / validation failure

### Portfolio YAML (present, unused by M0 CLI)
`configs/portfolios/demo_spy_qqq_tlt_gld.yaml`:
```yaml
name: demo_spy_qqq_tlt_gld
notional: 1_000_000
positions:
  SPY: 0.40
  QQQ: 0.20
  TLT: 0.25
  GLD: 0.15
```
Parse helpers can wait for M1; file exists so the demo portfolio is versioned.

---

## 7. Persistence

### Canonical OHLCV schema
After validation, every saved frame must have:

| Column | Dtype expectations |
|--------|--------------------|
| index  | tz-naive datetime, unique, sorted ascending, name e.g. `date` |
| open, high, low, close | float, finite, `> 0` |
| volume | float or int, finite, `>= 0` |

### `ParquetMarketDataStore`
- Root: `paths.raw_dir`
- Path pattern: `{raw_dir}/{SYMBOL}/ohlcv.parquet` (VIP-like)
- `save` / `load` / `exists`
- On save, optionally write a tiny `{SYMBOL}/meta.json` with source name +
  date range (nice; not required for exit)

---

## 8. Validators (`data/validators.py`)

Port the VIP idea, QRE-owned copy (do not import VIP):

1. Normalize column names (`Adj Close` → decide policy: for M0 prefer using
   `Close` as `close` with `auto_adjust=False`, same as VIP)
2. Require `open, high, low, close, volume`
3. Normalize datetime index (UTC-normalized then tz-naive dates)
4. Reject duplicate index, unsorted index
5. Reject NaNs in required columns
6. Reject non-positive prices; negative volume
7. Optional sanity: `low <= min(open,close)` and `high >= max(open,close)`
   (soft or hard — pick hard for cleaner data)

Public API:

- `validate_and_normalize_ohlcv(frame) -> DataFrame`
- Helpers may be public if tested (`normalize_ohlcv_columns`, etc.)

Raise `DataValidationError` with clear messages.

---

## 9. YFinance adapter

`YFinanceMarketDataSource`:

- `fetch(symbol, date_range)`:
  - Map aliases `VIX`/`TNX` if you support them
  - `yf.download(..., interval="1d", auto_adjust=False, progress=False)`
  - Remember yfinance `end` is exclusive → add one day
  - Catch narrow exceptions (`ValueError`, `TypeError`, `RuntimeError`), wrap in
    `DataValidationError`
  - Run `validate_and_normalize_ohlcv`
- `source_name()` → `"yfinance"`

---

## 10. Application use-case

`ingest_market_data.py`:

```text
ingest_symbol(symbol, date_range, source, store) -> DatasetRef
ingest_universe(symbols, date_range, source, store) -> list[DatasetRef]
```

Keep ≤5 params per function (group deps in a small context dataclass if needed,
e.g. `IngestDeps(source, store)`).

Behavior:
1. `frame = source.fetch(...)`
2. `store.save(symbol, frame)`
3. Return `DatasetRef`

CLI calls this — no yfinance imports in CLI module.

---

## 11. CLI

`qre.cli.main:app`

- Typer app name `qre`, `no_args_is_help=True`
- Callback: `--log-level`
- Command `ingest`:
  - `--symbol` repeatable **or** `--all-universe` flag reading config
  - `--config` optional path
  - `--start` / `--end` optional overrides
- Print paths written (symbol + parquet path)

Minimum for exit: ingest one symbol from config defaults.

---

## 12. Logging

`configure_logging(level: str) -> None`  
stdlib logging is enough (structlog optional; skip for M0).

---

## 13. Tests (write these)

### `test_weights.py`
- Valid weights sum to 1 → OK
- Sum 0.9 → `PortfolioError`
- Empty → error
- Negative weight → error

### `test_date_range.py`
- `start > end` → error
- `contains` boundaries

### `test_validators.py`
- Load tiny fixture CSV → normalized schema
- Missing column → `DataValidationError`
- Duplicate dates → error
- NaN close → error
- Negative price → error

### `test_parquet_store.py`
- tmp_path: save → exists → load equals (use `pandas.testing.assert_frame_equal`)

### `test_loader.py`
- Load `configs/default.yaml` (path relative to repo root; use fixture path)
- Bad YAML / missing required field → `ConfigError`

### `test_ingest_market_data.py`
- Fake `MarketDataSource` returning a valid small frame
- In-memory or tmp Parquet store
- Assert `DatasetRef` and file/frame presence
- **No network**

---

## 14. Optional CI

`.github/workflows/ci.yml`: Python 3.11 (and optionally 3.12), `ruff check`,
`pytest -q`. Skip integration tests by default.

---

## 15. README (minimal)

- What QRE is (one paragraph) + link to VIP distinction
- Install: `pip install -e ".[dev]"`
- `qre ingest --symbol SPY`
- Point to `plan.md`

---

## 16. Coding checklist (every file)

- Module docstring lists exports (PEP 257)
- Class docstrings list public methods / attributes
- NumPy-style docstrings on public functions
- ≥2 public methods on classes
- ≤5 parameters; ≤15 locals
- No unused typing imports
- No f-string without interpolation
- Named constants instead of magic indices

---

## 17. After M0

1. Run proving experiment for four ETFs  
2. Update `plan.md` Status: M0 → DONE (YYYY-MM-DD)  
3. Ask-mode: draft **Milestone 1 walkthrough** (historical VaR/ES)

Do not start M1 until M0 exit checklist is complete.
