"""Domain and platform error types.

Exports
-------
QreError
    Base error for all Quant Risk Engine failures.
ConfigError
    Invalid or missing configuration.
DataValidationError
    Invalid market or domain data.
PortfolioError
    Invalid portfolio or weight definitions.
"""


class QreError(Exception):
    """Base error for Quant Risk Engine failures."""


class ConfigError(QreError):
    """Raised when configuration is missing, unreadable, or invalid."""


class DataValidationError(QreError):
    """Raised when market or domain data fails validation checks."""


class PortfolioError(QreError):
    """Raised when a portfolio or its weights are invalid."""

class PersistenceError(QreError):
    """Raised when loading or saving data or artifacts fails."""
