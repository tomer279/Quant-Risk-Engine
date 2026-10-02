"""CLI command for market data ingestion.

Exports
-------
ingest_command
    Register the ``qre ingest`` command on a Typer app.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Annotated

import typer

from qre.application import IngestDeps, ingest_universe
from qre.config import load_config, resolve_project_root
from qre.data import YFinanceMarketDataSource
from qre.domain.value_objects import DateRange, Symbol
from qre.persistence import ParquetMarketDataStore


def _parse_iso_date(value: str, option_name: str) -> date:
    """Parse an ISO date string from a CLI option.

    Parameters
    ----------
    value : str
        Date text in ``YYYY-MM-DD`` form.
    option_name : str
        CLI option name used in error messages.

    Returns
    -------
    datetime.date
        Parsed calendar date.

    Raises
    ------
    typer.BadParameter
        If ``value`` is not a valid ISO date.
    """
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise typer.BadParameter(
            f"{option_name} must be YYYY-MM-DD, got: {value!r}"
        ) from exc


def _resolve_symbols(
    requested: list[str] | None,
    all_universe: bool,
    universe: list[str],
) -> list[Symbol]:
    """Choose tickers from CLI flags or config universe.

    Parameters
    ----------
    requested : list of str or None
        Tickers passed via repeated ``--symbol``.
    all_universe : bool
        If True, ignore ``requested`` and use ``universe``.
    universe : list of str
        Default tickers from config.

    Returns
    -------
    list of Symbol
        Symbols to ingest.

    Raises
    ------
    typer.BadParameter
        If the resolved list is empty.
    """
    if all_universe or not requested:
        tickers = universe
    else:
        tickers = requested

    if not tickers:
        raise typer.BadParameter(
            "No symbols to ingest; pass --symbol or configure universe."
        )
    return [Symbol(ticker) for ticker in tickers]


def _resolve_date_range(
    start: str | None,
    end: str | None,
    config_start: date,
    config_end: date | None,
) -> DateRange:
    """Build an inclusive DateRange from CLI overrides and config.

    Parameters
    ----------
    start : str or None
        Optional ``YYYY-MM-DD`` start override.
    end : str or None
        Optional ``YYYY-MM-DD`` end override.
    config_start : datetime.date
        Config default start.
    config_end : datetime.date or None
        Config default end; ``None`` means today.

    Returns
    -------
    DateRange
        Inclusive fetch window.
    """
    start_date = (
        _parse_iso_date(start, "--start")
        if start is not None
        else config_start
    )
    if end is not None:
        end_date = _parse_iso_date(end, "--end")
    elif config_end is not None:
        end_date = config_end
    else:
        end_date = date.today()
    return DateRange(start=start_date, end=end_date)


def ingest_command(app: typer.Typer) -> None:
    """Register the market data ingestion command.

    Parameters
    ----------
    app : typer.Typer
        Target CLI app instance.
    """

    @app.command("ingest")
    def ingest(
        symbols: Annotated[
            list[str] | None,
            typer.Option("--symbol", help="Ticker to ingest (repeatable)."),
        ] = None,
        all_universe: Annotated[
            bool,
            typer.Option(
                "--all-universe",
                help="Ingest every symbol in the config universe.",
            ),
        ] = False,
        start: Annotated[
            str | None,
            typer.Option("--start", help="Start date override (YYYY-MM-DD)."),
        ] = None,
        end: Annotated[
            str | None,
            typer.Option("--end", help="End date override (YYYY-MM-DD)."),
        ] = None,
        config_path: Annotated[
            Path | None,
            typer.Option(
                "--config",
                help="Optional path to a YAML config file.",
            ),
        ] = None,
    ) -> None:
        """Fetch, validate, and persist daily OHLCV market data."""
        config = load_config(config_path)
        resolved = _resolve_symbols(
            symbols,
            all_universe,
            config.universe.symbols,
        )
        date_range = _resolve_date_range(
            start,
            end,
            config.date_range.start,
            config.date_range.end,
        )

        raw_dir = Path(config.paths.raw_dir)
        if not raw_dir.is_absolute():
            raw_dir = resolve_project_root() / raw_dir

        deps = IngestDeps(
            source=YFinanceMarketDataSource(),
            store=ParquetMarketDataStore(root_dir=raw_dir),
        )
        refs = ingest_universe(deps, resolved, date_range)

        typer.echo("Ingestion completed.")
        typer.echo(f"source: {deps.source_name()}")
        for ref in refs:
            output = raw_dir / ref.relative_path
            typer.echo(f"symbol: {ref.symbol.value}")
            typer.echo(f"output: {output}")
