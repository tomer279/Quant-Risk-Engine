"""Logging configuration helpers for QRE processes.

Exports
-------
configure_logging
    Configure the root logger once for a process.
get_logger
    Return a named logger.
"""

from __future__ import annotations

import logging


class _LoggingGate:
    """Process-wide gate so root logging is configured at most once.

    Methods
    -------
    configure(level)
        Apply ``basicConfig`` on the first call only.
    is_configured()
        Return whether configuration has already run.
    """

    def __init__(self) -> None:
        """Initialize an unconfigured gate."""
        self._configured = False

    def configure(self, level: str = "INFO") -> None:
        """Configure root logging if it has not been configured yet.

        Parameters
        ----------
        level : str, default ``'INFO'``
            Stdlib logging level name.
        """
        if self._configured:
            return

        logging.basicConfig(
            level=getattr(logging, level.upper(), logging.INFO),
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )
        self._configured = True

    def is_configured(self) -> bool:
        """Return whether ``configure`` has already succeeded.

        Returns
        -------
        bool
            True after the first successful configuration.
        """
        return self._configured


_LOGGING_GATE = _LoggingGate()


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging if it has not been configured yet.

    Parameters
    ----------
    level : str, default ``'INFO'``
        Stdlib logging level name.
    """
    _LOGGING_GATE.configure(level)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger.

    Parameters
    ----------
    name : str
        Logger name, typically ``__name__``.

    Returns
    -------
    logging.Logger
        Logger instance.
    """
    return logging.getLogger(name)
