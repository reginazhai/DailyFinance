"""CLI for rebuilding the processed-document search index."""

from argparse import ArgumentParser, Namespace

from dailyfinance.storage import DatabaseDocumentStore


DEFAULT_DATABASE_URL = "sqlite:///data/dailyfinance.db"


def main() -> None:
    args = _parse_args()
    store = DatabaseDocumentStore(args.database_url)
    result = store.rebuild_search_index()
    print(
        "Search index rebuild complete: "
        f"indexed={result['indexed']} "
        f"skipped={result['skipped']} "
        f"failed={result['failed']}"
    )


def _parse_args() -> Namespace:
    parser = ArgumentParser(description="Rebuild the DailyFinance SQLite search index.")
    parser.add_argument(
        "--database-url",
        default=DEFAULT_DATABASE_URL,
        help=f"SQLite database URL. Defaults to {DEFAULT_DATABASE_URL}.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
