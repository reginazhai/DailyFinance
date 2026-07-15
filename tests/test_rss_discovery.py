import httpx

from dailyfinance.collectors.news.discovery import discover_feed_urls


def test_discover_feed_urls_from_website_html(monkeypatch) -> None:
    html = """
<html>
  <head>
    <link rel="alternate" type="application/rss+xml" href="/feed.xml">
    <link rel="alternate" type="application/atom+xml" href="https://example.com/atom.xml">
    <link rel="stylesheet" href="/site.css">
  </head>
</html>
"""

    def fake_get(url: str, follow_redirects: bool, timeout: float) -> httpx.Response:
        assert url == "https://example.com"
        assert follow_redirects is True
        assert timeout == 10.0
        return httpx.Response(
            status_code=200,
            text=html,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    assert discover_feed_urls("https://example.com") == [
        "https://example.com/feed.xml",
        "https://example.com/atom.xml",
    ]


def test_discover_feed_urls_returns_empty_list_when_no_feed_links(monkeypatch) -> None:
    def fake_get(url: str, follow_redirects: bool, timeout: float) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            text="<html><head></head><body>No feeds here.</body></html>",
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    assert discover_feed_urls("https://example.com") == []
