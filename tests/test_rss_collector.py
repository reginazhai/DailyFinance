import feedparser

from dailyfinance.collectors import RssCollector
from dailyfinance.models import RawDocument


RSS_FEED_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>Example Finance</title>
    <link>https://example.com</link>
    <description>Example finance feed</description>
    <item>
      <guid>article-1</guid>
      <title>Markets rise as investors assess inflation data</title>
      <link>https://example.com/news/markets-inflation</link>
      <pubDate>Wed, 01 Jul 2026 13:30:00 GMT</pubDate>
      <description>Stocks climbed after inflation data came in near expectations.</description>
    </item>
    <item>
      <guid>article-2</guid>
      <title>Treasury yields edge lower before jobs report</title>
      <link>https://example.com/news/treasury-yields</link>
      <pubDate>Wed, 01 Jul 2026 15:00:00 GMT</pubDate>
      <description>Bond yields slipped as traders waited for jobs data.</description>
    </item>
  </channel>
</rss>
"""

ATOM_FEED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Example Atom Finance</title>
  <link href="https://example.com/atom.xml" rel="self"/>
  <entry>
    <id>tag:example.com,2026:oil-prices</id>
    <title>Oil prices move higher</title>
    <link href="https://example.com/news/oil-prices"/>
    <updated>2026-07-01T16:00:00Z</updated>
    <summary>Oil prices rose as inventories tightened.</summary>
  </entry>
</feed>
"""


def test_rss_collector_returns_raw_documents_from_static_rss_xml(monkeypatch) -> None:
    original_parse = feedparser.parse
    parsed_urls: list[str] = []

    def fake_parse(url: str):
        parsed_urls.append(url)
        return original_parse(RSS_FEED_XML)

    monkeypatch.setattr(feedparser, "parse", fake_parse)
    collector = RssCollector(
        source_name="example_rss",
        feed_url="https://example.com/feed.xml",
    )

    documents = collector.collect()

    assert parsed_urls == ["https://example.com/feed.xml"]
    assert len(documents) == 2
    assert all(isinstance(document, RawDocument) for document in documents)
    assert all(document.source_name == "example_rss" for document in documents)
    assert documents[0].external_id == "article-1"
    assert documents[0].title == "Markets rise as investors assess inflation data"
    assert str(documents[0].url) == "https://example.com/news/markets-inflation"
    assert documents[0].published_at is not None
    assert documents[0].content == "Stocks climbed after inflation data came in near expectations."
    assert documents[0].raw_payload["title"] == "Markets rise as investors assess inflation data"
    assert documents[0].metadata == {"feed_url": "https://example.com/feed.xml"}
    assert documents[1].external_id == "article-2"
    assert documents[1].content == "Bond yields slipped as traders waited for jobs data."


def test_rss_collector_parses_atom_feed_entries(monkeypatch) -> None:
    original_parse = feedparser.parse
    monkeypatch.setattr(feedparser, "parse", lambda url: original_parse(ATOM_FEED_XML))

    documents = RssCollector("example_rss", "https://example.com/feed.xml").collect()

    assert len(documents) == 1
    assert documents[0].external_id == "tag:example.com,2026:oil-prices"
    assert documents[0].title == "Oil prices move higher"
    assert str(documents[0].url) == "https://example.com/news/oil-prices"
    assert documents[0].published_at is not None
    assert documents[0].content == "Oil prices rose as inventories tightened."
