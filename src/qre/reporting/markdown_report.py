"""Minimal Markdown writer for historical risk results.

Exports
-------
MarkdownHistoricalReport
    Render and write a historical risk memo.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from qre.domain.risk import HistoricalRiskResult

PCT_SCALE = 100.0
PCT_DECIMALS = 4


class MarkdownHistoricalReport:
    """Stdlib Markdown report for M1 historical analysis.

    Methods
    -------
    render(result, weights)
        Build the Markdown body as a string.
    write(result, weights, output_path)
        Write ``report.md`` (or the given path) to disk.
    """

    def render(
            self,
            result: HistoricalRiskResult,
            weights: Mapping[str, float],
    ) -> str:
        """Render a Markdown risk memo.

        Parameters
        ----------
        result : HistoricalRiskResult
            Analysis output.
        weights : mapping of str to float
            Ticker → weight for the weights table.

        Returns
        -------
        str
            Full Markdown document.
        """
        lines: list[str] = [
            "# Historical portfolio risk",
            "",
            f"- Portfolio: `{result.portfolio_name}`",
            f"- Notional: {result.notional:,.0f}",
            f"- Sample: {result.start_date} → {result.end_date}",
            f"- Observations: {result.n_obs}",
            "",
            "## Weights",
            "",
            "| Symbol | Weight |",
            "|--------|--------|",
        ]
        for ticker, weight in sorted(weights.items()):
            lines.append(f"| {ticker} | {weight:.4f} |")

        lines.extend(
            [
                "",
                "## Risk measures (1-day loss units)",
                "",
                f"- Mean loss: {_as_pct(result.summary.mean_loss)}",
                "",
            ]
        )
        for alpha in result.summary.alphas():
            var_pct = _as_pct(result.summary.var_by_alpha[alpha])
            es_pct = _as_pct(result.summary.es_by_alpha[alpha])
            level = alpha * PCT_SCALE
            lines.append(
                f"- alpha={level:.2f}%: VaR={var_pct}, ES={es_pct}"
            )

        lines.extend(
            [
                "",
                "## Caveats",
                "",
                "- Historical simulation only (no stress overlay).",
                "- Horizon is 1-day; multi-day scaling is out of scope for M1.",
                "- Past losses are not a forecast of future risk.",
                "",
            ]
        )
        return "\n".join(lines)

    def write(
            self,
            result: HistoricalRiskResult,
            weights: Mapping[str, float],
            output_path: Path,
    ) -> Path:
        """Write the Markdown memo to ``output_path``.

        Parameters
        ----------
        result : HistoricalRiskResult
            Analysis output.
        weights : mapping of str to float
            Portfolio weights.
        output_path : pathlib.Path
            Destination file (parent dirs are created).

        Returns
        -------
        pathlib.Path
            Path written.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            self.render(result, weights),
            encoding="utf-8",
        )
        return output_path


def _as_pct(value: float) -> str:
    """Format a decimal loss as a percentage string."""
    scaled = value * PCT_SCALE
    return f"{scaled:.{PCT_DECIMALS}f}%"
