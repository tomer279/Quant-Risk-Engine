"""Markdown writer for stress analysis results.

Exports
-------
MarkdownStressReport
    Render and write a stress risk memo.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from qre.domain.scenarios import (
    HistoricalEpisodeScenario,
    HypotheticalScenario,
    ScenarioSpec,
    StressAnalysisResult,
)

PCT_SCALE = 100.0
PCT_DECIMALS = 4


class MarkdownStressReport:
    """Stdlib Markdown report for M2 stress analysis.

    Methods
    -------
    render(result, weights, scenario)
        Build the Markdown body as a string.
    write(result, weights, scenario, output_path)
        Write the memo to disk.
    """

    def render(
            self,
            result: StressAnalysisResult,
            weights: Mapping[str, float],
            scenario: ScenarioSpec,
    ) -> str:
        """Render a Markdown stress memo.

        Parameters
        ----------
        result : StressAnalysisResult
            Stress payload.
        weights : mapping of str to float
            Portfolio weights.
        scenario : ScenarioSpec
            Scenario used (for parameter echo).

        Returns
        -------
        str
            Full Markdown document.
        """
        lines: list[str] = [
            "# Portfolio stress analysis",
            "",
            f"- Portfolio: `{result.portfolio_name}`",
            f"- Scenario: `{result.scenario_name}` ({result.scenario_kind})",
            "",
            "## Weights",
            "",
            "| Symbol | Weight |",
            "|--------|--------|",
        ]
        for ticker, weight in sorted(weights.items()):
            lines.append(f"| {ticker} | {weight:.4f} |")

        lines.extend(["", "## Scenario parameters", ""])
        lines.extend(_scenario_param_lines(scenario))

        lines.extend(
            [
                "",
                "## Asset contributions (linear P&L)",
                "",
                result.format_contribution_table(),
                "",
            ]
        )

        if result.instantaneous is not None:
            loss = result.instantaneous.portfolio_loss
            lines.extend(
                [
                    "## Instantaneous shock",
                    "",
                    f"- Portfolio loss: {_as_pct(loss)}",
                    f"- ({result.instantaneous.format_loss_line()})",
                    "",
                ]
            )

        if result.historical is not None:
            hist = result.historical
            lines.extend(
                [
                    "## Historical / stressed sample",
                    "",
                    f"- Notional: {hist.notional:,.0f}",
                    f"- Sample: {hist.start_date} → {hist.end_date}",
                    f"- Observations: {hist.n_obs}",
                    f"- Mean loss: {_as_pct(hist.summary.mean_loss)}",
                    "",
                ]
            )
            for alpha in hist.summary.alphas():
                var_pct = _as_pct(hist.summary.var_by_alpha[alpha])
                es_pct = _as_pct(hist.summary.es_by_alpha[alpha])
                level = alpha * PCT_SCALE
                lines.append(
                    f"- alpha={level:.2f}%: VaR={var_pct}, ES={es_pct}"
                )
            lines.append("")

        lines.extend(
            [
                "## Caveats",
                "",
                "- Hypothetical shocks are not forecasts.",
                "- Correlation stress uses PSD projection before recoloring.",
                "- Horizon is 1-day; no sqrt(h) scaling.",
                "- Linear contributions (L_i = -w_i R_i) are not Euler VaR.",
                "",
            ]
        )
        return "\n".join(lines)

    def write(
            self,
            result: StressAnalysisResult,
            weights: Mapping[str, float],
            scenario: ScenarioSpec,
            output_path: Path,
    ) -> Path:
        """Write the Markdown memo to ``output_path``."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            self.render(result, weights, scenario),
            encoding="utf-8",
        )
        return output_path


def _scenario_param_lines(scenario: ScenarioSpec) -> list[str]:
    """Echo key scenario fields as Markdown bullets."""
    if isinstance(scenario, HistoricalEpisodeScenario):
        start_iso, end_iso = scenario.window.to_iso_pair()
        return [
            f"- Kind: `{scenario.kind().value}`",
            f"- Window: {start_iso} → {end_iso}",
            f"- Description: {scenario.description}",
        ]
    if isinstance(scenario, HypotheticalScenario):
        shock_bits = ", ".join(
            f"{ticker}={value:.4f}"
            for ticker, value in sorted(scenario.asset_shocks.items())
        )
        return [
            f"- Kind: `{scenario.kind().value}`",
            f"- Asset shocks: {shock_bits}",
            f"- Vol multiplier: {scenario.vol_multiplier}",
            f"- Correlation inflation: {scenario.correlation_inflation}",
            f"- Apply to historical: {scenario.apply_to_historical}",
            f"- Description: {scenario.description}",
        ]
    return [f"- Kind: `{scenario}`"]


def _as_pct(value: float) -> str:
    """Format a decimal loss as a percentage string."""
    scaled = value * PCT_SCALE
    return f"{scaled:.{PCT_DECIMALS}f}%"
