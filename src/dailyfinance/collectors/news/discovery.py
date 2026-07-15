"""RSS feed discovery helpers."""

from html.parser import HTMLParser
from urllib.parse import urljoin

import httpx


RSS_MIME_TYPES = {
    "application/atom+xml",
    "application/rss+xml",
    "application/rdf+xml",
    "text/rss+xml",
    "text/xml",
}


class FeedLinkParser(HTMLParser):
    """Extract RSS/Atom feed links from HTML link tags."""

    def __init__(self, website_url: str) -> None:
        super().__init__()
        self.website_url = website_url
        self.feed_urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Capture alternate RSS/Atom links."""
        if tag.lower() != "link":
            return

        attributes = {key.lower(): value for key, value in attrs if value is not None}
        rel_values = set(attributes.get("rel", "").lower().split())
        feed_type = attributes.get("type", "").lower()
        href = attributes.get("href")

        if href and "alternate" in rel_values and feed_type in RSS_MIME_TYPES:
            self.feed_urls.append(urljoin(self.website_url, href))


def discover_feed_urls(website_url: str) -> list[str]:
    """Discover RSS/Atom feed URLs from a website homepage."""
    response = httpx.get(website_url, follow_redirects=True, timeout=10.0)
    response.raise_for_status()

    parser = FeedLinkParser(str(response.url))
    parser.feed(response.text)
    return list(dict.fromkeys(parser.feed_urls))
