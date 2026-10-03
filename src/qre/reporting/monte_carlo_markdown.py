"""Minimal Markdown writer for Gaussian Monte Carlo results.

Exports
-------
MonteCarloReportInput
    Bundle of result, weights, and convergence points.
MarkdownMonteCarloReport
    Render and write a Monte Carlo risk memo.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from qre.domain.risk import MonteCarloRiskResult
from qre.validation import ConvergencePoint

PCT_SCALE = 100.0
PCT_DECIMALS = 4


@dataclass(frozen=True, slots=True)
class MonteCarloReportInput:
    """Inputs required to render a Monte Carlo Markdown report.

    Parameters
    ----------
    result : MonteCarloRiskResult
        Analysis payload.
    weights : mapping of str to float
        Portfolio weights for the weights table.
    convergence : tuple of ConvergencePoint
        Prefix-based convergence rows.

    Methods
    -------
    alphas()
        Confidence levels from the MC summary.
    as_dict()
        JSON-friendly snapshot of report inputs.
    """

    result: MonteCarloRiskResult
    weights: Mapping[str, float]
    convergence: tuple[ConvergencePoint, ...]

    def alphas(self) -> tuple[float, ...]:
        """Return confidence levels used in the report."""
        return self.result.mc_summary.alphas()

    def as_dict(self) -> dict[str, object]:
        """Return a plain dict suitable for JSON."""
        return {
            "result": self.result.as_dict(),
            "weights": dict(self.weights),
            "convergence": [point.as_dict() for point in self.convergence],
        }


class MarkdownMonteCarloReport:
    """Stdlib Markdown report for Gaussian Monte Carlo analysis.

    Methods
    -------
    render(payload)
        Build the Markdown body as a string.
    write(payload, output_path)
        Write the memo to disk.
    """

    def render(self, payload: MonteCarloReportInput) -> str:
        """Render a Markdown risk memo.

        Parameters
        ----------
        payload : MonteCarloReportInput
            Result, weights, and convergence table.

        Returns
        -------
        str
            Full Markdown document.
        """
        result = payload.result
        lines: list[str] = [
            "# Gaussian Monte Carlo portfolio risk",
            "",
            f"- Portfolio: `{result.portfolio_name}`",
            f"- Notional: {result.notional:,.0f}",
            f"- Calibration: {result.calibration.format_span()}",
            f"- Run: {result.run.format_line()}",
            "",
            "## Weights",
            "",
            "| Symbol | Weight |",
            "|--------|--------|",
        ]
        for ticker, weight in sorted(payload.weights.items()):
            lines.append(f"| {ticker} | {weight:.4f} |")

        lines.extend(
            [
                "",
                "## MC vs analytic (1-day loss units)",
                "",
                f"- MC mean loss: {_as_pct(result.mc_summary.mean_loss)}",
                f"- Analytic mean loss: "
                f"{_as_pct(result.analytic_summary.mean_loss)}",
                "",
            ]
        )
        for alpha in payload.alphas():
            level = alpha * PCT_SCALE
            lines.append(
                f"- alpha={level:.2f}%: "
                f"MC_VaR={_as_pct(result.mc_summary.var_by_alpha[alpha])}, "
                f"AN_VaR="
                f"{_as_pct(result.analytic_summary.var_by_alpha[alpha])}, "
                f"MC_ES={_as_pct(result.mc_summary.es_by_alpha[alpha])}, "
                f"AN_ES="
                f"{_as_pct(result.analytic_summary.es_by_alpha[alpha])}"
            )

        lines.extend(_convergence_section(payload))
        lines.extend(
            [
                "",
                "## Caveats",
                "",
                "- Multivariate Gaussian MC with Cholesky; 1-day horizon only.",
                "- Analytic VaR/ES assume the same Gaussian loss law.",
                "- Calibration uses historical lookback; past ≠ future.",
                "- No Student-t / GARCH / scenario overlay in this report.",
                "",
            ]
        )
        return "\n".join(lines)

    def write(
            self,
            payload: MonteCarloReportInput,
            output_path: Path,
    ) -> Path:
        """Write the Markdown memo to ``output_path``."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.render(payload), encoding="utf-8")
        return output_path


def _convergence_section(payload: MonteCarloReportInput) -> list[str]:
    """Build Markdown lines for the convergence table."""
    alphas = payload.alphas()
    if not payload.convergence or not alphas:
        return []

    header = ["n_paths"]
    for alpha in alphas:
        level = alpha * PCT_SCALE
        header.append(f"VaR@{level:.0f}%")
        header.append(f"ES@{level:.0f}%")

    lines = [
        "",
        "## Convergence (MC prefixes)",
        "",
        "| " + " | ".join(header) + " |",
        "|" + "|".join(["--------"] * len(header)) + "|",
    ]
    for point in payload.convergence:
        row = [str(point.n_paths)]
        for alpha in alphas:
            row.append(_as_pct(point.var_by_alpha[alpha]))
            row.append(_as_pct(point.es_by_alpha[alpha]))
        lines.append("| " + " | ".join(row) + " |")
    return lines


def _as_pct(value: float) -> str:
    """Format a decimal loss as a percentage string."""
    scaled = value * PCT_SCALE
    return f"{scaled:.{PCT_DECIMALS}f}%"
