"""Domain enumerations.

Exports
-------
ScenarioKind
    Discriminator for historical episode vs hypothetical stress.
"""

from __future__ import annotations

from enum import StrEnum


class ScenarioKind(StrEnum):
    """Kind of stress scenario loaded from YAML.

    Members
    -------
    HISTORICAL_EPISODE
        Restrict returns to a named date window.
    HYPOTHETICAL
        Instantaneous asset shocks and optional vol/corr stress.
    """

    HISTORICAL_EPISODE = "historical_episode"
    HYPOTHETICAL = "hypothetical"

    def is_episode(self) -> bool:
        """Return whether this kind is a historical episode."""
        return self is ScenarioKind.HISTORICAL_EPISODE

    def is_hypothetical(self) -> bool:
        """Return whether this kind is hypothetical stress."""
        return self is ScenarioKind.HYPOTHETICAL
