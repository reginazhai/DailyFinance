from dailyfinance.config import load_rss_sources


def test_load_rss_sources_from_yaml(tmp_path) -> None:
    config_path = tmp_path / "rss_sources.yaml"
    config_path.write_text(
        """
rss_sources:
  - source_name: source_one
    feed_url: https://example.com/feed.xml
  - source_name: source_two
    feed_url: https://example.com/rss.xml
""",
        encoding="utf-8",
    )

    sources = load_rss_sources(config_path)

    assert len(sources) == 2
    assert sources[0].source_name == "source_one"
    assert sources[0].feed_url == "https://example.com/feed.xml"
    assert sources[1].source_name == "source_two"
    assert sources[1].feed_url == "https://example.com/rss.xml"
