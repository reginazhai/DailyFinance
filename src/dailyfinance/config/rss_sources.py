"""RSS source configuration loading."""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class RssSourceConfig(BaseModel):
    """Configured RSS source."""

    source_name: str = Field(min_length=1)
    feed_url: str = Field(min_length=1)


class RssSourcesConfig(BaseModel):
    """Configured RSS sources file."""

    rss_sources: list[RssSourceConfig] = Field(default_factory=list)


def load_rss_sources(path: Path | str) -> list[RssSourceConfig]:
    """Load RSS sources from a YAML config file."""
    with Path(path).open("r", encoding="utf-8") as file:
        config_data = yaml.safe_load(file) or {}
    return RssSourcesConfig.model_validate(config_data).rss_sources
