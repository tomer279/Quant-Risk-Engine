"""Application use-cases for the Quant Risk Engine.

Exports
-------
IngestDeps
    Source/store dependency pair.
ingest_symbol
    Ingest a single symbol.
ingest_universe
    Ingest a symbol list.
PortfolioSpec
    Portfolio specification data class.
load_portfolio_yaml
    Parse a portfolio YAML into ``PortfolioSpec``.
load_scenario_yaml
    Parse a scenario YAML into a ``Scenario``.
AnalysisDeps
    Store dependency for historical analysis.
run_historical_analysis
    Build returns, losses, measures, and a Markdown artifact.
StressAnalysisOutcome
    Result plus artifact path from a stress run.   
run_stress_analysis
    Build losses, measures, and a Markdown artifact for a stress scenario.
MonteCarloAnalysisOutcome
    Result, report path, and convergence table from one MC run.
run_monte_carlo_analysis
    Calibrate, simulate, compare to analytic VaR/ES, write Markdown.
"""

from qre.application.ingest_market_data import (
    IngestDeps,
    ingest_symbol,
    ingest_universe,
)
from qre.application.load_portfolio import PortfolioSpec, load_portfolio_yaml
from qre.application.load_scenario import load_scenario_yaml
from qre.application.run_historical_analysis import (
    AnalysisDeps,
    run_historical_analysis,
)
from qre.application.run_monte_carlo_analysis import (
    MonteCarloAnalysisOutcome,
    run_monte_carlo_analysis,
)
from qre.application.run_stress_analysis import (
    StressAnalysisOutcome,
    run_stress_analysis,
)

__all__ = [
    "IngestDeps",
    "ingest_symbol",
    "ingest_universe",
    "PortfolioSpec",
    "load_portfolio_yaml",
    "load_scenario_yaml",
    "AnalysisDeps",
    "run_historical_analysis",
    "StressAnalysisOutcome",
    "run_stress_analysis",
    "MonteCarloAnalysisOutcome",
    "run_monte_carlo_analysis",
]
