"""SQLAlchemy-backed document storage."""

from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    select,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)
from sqlalchemy.types import JSON

from dailyfinance.models import DocumentType, ProcessedDocument, RawDocument
from dailyfinance.processing.quality import is_valid_raw_document, normalize_raw_document
from dailyfinance.storage.base import DocumentStore, StorageWriteResult
from dailyfinance.utils import derive_document_id


class Base(DeclarativeBase):
    """Base class for database models."""


class SourceRecord(Base):
    """Collected data source."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    documents: Mapped[list["DocumentRecord"]] = relationship(back_populates="source")


class DocumentRecord(Base):
    """Collected raw document."""

    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("id", name="uq_documents_id"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    title: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    source: Mapped[SourceRecord] = relationship(back_populates="documents")
    processed_documents: Mapped[list["ProcessedDocumentRecord"]] = relationship(
        back_populates="raw_document"
    )


class ProcessedDocumentRecord(Base):
    """Processed representation of a raw document."""

    __tablename__ = "processed_documents"
    __table_args__ = (
        UniqueConstraint(
            "raw_document_id",
            "processing_version",
            name="uq_processed_documents_raw_version",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    raw_document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id"), nullable=False, index=True
    )
    document_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    normalized_title: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    normalized_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    companies: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processing_version: Mapped[str] = mapped_column(String(64), nullable=False)

    raw_document: Mapped[DocumentRecord] = relationship(back_populates="processed_documents")
    ticker_links: Mapped[list["ProcessedDocumentTickerRecord"]] = relationship(
        back_populates="processed_document",
        cascade="all, delete-orphan",
    )


class ProcessedDocumentTickerRecord(Base):
    """Queryable ticker association for processed documents."""

    __tablename__ = "processed_document_tickers"
    __table_args__ = (
        UniqueConstraint(
            "processed_document_id",
            "ticker",
            name="uq_processed_document_tickers_doc_ticker",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    processed_document_id: Mapped[str] = mapped_column(
        ForeignKey("processed_documents.id"), nullable=False, index=True
    )
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, index=True)

    processed_document: Mapped[ProcessedDocumentRecord] = relationship(
        back_populates="ticker_links"
    )


class DatabaseDocumentStore(DocumentStore):
    """SQLAlchemy document store for local SQLite and future PostgreSQL."""

    def __init__(
        self,
        database_url: str = "sqlite:///dailyfinance.db",
        *,
        create_tables: bool = True,
    ) -> None:
        self.database_url = database_url
        self.engine = _create_engine(database_url)
        self.session_factory = sessionmaker(self.engine, expire_on_commit=False)
        if create_tables:
            Base.metadata.create_all(self.engine)

    def save(self, document: RawDocument) -> StorageWriteResult:
        """Persist one raw document if it does not already exist."""
        return self.save_documents([document])

    def save_many(self, documents: Iterable[RawDocument]) -> StorageWriteResult:
        """Persist multiple raw documents if they do not already exist."""
        return self.save_documents(documents)

    def save_documents(self, documents: Iterable[RawDocument]) -> StorageWriteResult:
        """Persist raw documents with source and document deduplication."""
        inserted_count = 0
        skipped_duplicates_count = 0
        invalid_count = 0

        with self.session_factory() as session:
            for document in documents:
                write_status = self._save_document(session, document)
                if write_status == "inserted":
                    inserted_count += 1
                elif write_status == "duplicate":
                    skipped_duplicates_count += 1
                elif write_status == "invalid":
                    invalid_count += 1
            session.commit()
        return StorageWriteResult(
            inserted_count=inserted_count,
            skipped_duplicates_count=skipped_duplicates_count,
            invalid_count=invalid_count,
        )

    def load_all(self) -> list[RawDocument]:
        """Load all persisted raw documents."""
        return self.list_documents(limit=None)

    def list_documents(
        self,
        limit: int | None = 20,
        source_name: str | None = None,
    ) -> list[RawDocument]:
        """List recent raw documents."""
        with self.session_factory() as session:
            statement = select(DocumentRecord).join(DocumentRecord.source)
            if source_name:
                statement = statement.where(SourceRecord.name == source_name)
            statement = statement.order_by(DocumentRecord.created_at.desc())
            if limit is not None:
                statement = statement.limit(limit)
            records = session.scalars(statement).all()
            return [_record_to_document(record) for record in records]

    def get_document(self, document_id: str) -> RawDocument | None:
        """Return one document by stable document ID."""
        with self.session_factory() as session:
            record = session.get(DocumentRecord, document_id)
            if record is None:
                return None
            return _record_to_document(record)

    def has_document(self, document_id: str) -> bool:
        """Return whether a document ID already exists."""
        with self.session_factory() as session:
            return session.get(DocumentRecord, document_id) is not None

    def list_sources_with_counts(self) -> list[dict[str, Any]]:
        """List sources with persisted document counts."""
        with self.session_factory() as session:
            sources = session.scalars(select(SourceRecord).order_by(SourceRecord.name)).all()
            return [
                {
                    "source_name": source.name,
                    "source_type": source.source_type,
                    "url": source.url,
                    "document_count": len(source.documents),
                }
                for source in sources
            ]

    def save_processed_document(self, document: ProcessedDocument) -> bool:
        """Persist one processed document idempotently."""
        with self.session_factory() as session:
            if session.get(ProcessedDocumentRecord, document.id) is not None:
                return False
            if session.get(DocumentRecord, document.raw_document_id) is None:
                return False

            record = ProcessedDocumentRecord(
                id=document.id,
                raw_document_id=document.raw_document_id,
                document_type=document.document_type.value,
                normalized_title=document.normalized_title,
                normalized_content=document.normalized_content,
                source_type=document.source_type,
                companies=document.companies,
                published_at=document.published_at,
                processed_at=document.processed_at,
                processing_version=document.processing_version,
                ticker_links=[
                    ProcessedDocumentTickerRecord(ticker=ticker)
                    for ticker in document.tickers
                ],
            )
            session.add(record)
            session.commit()
            return True

    def has_processed_document(
        self,
        raw_document_id: str,
        processing_version: str,
    ) -> bool:
        """Return whether a raw document already has this processing version."""
        with self.session_factory() as session:
            statement = select(ProcessedDocumentRecord).where(
                ProcessedDocumentRecord.raw_document_id == raw_document_id,
                ProcessedDocumentRecord.processing_version == processing_version,
            )
            return session.scalar(statement) is not None

    def list_unprocessed_raw_documents(
        self,
        *,
        processing_version: str,
        limit: int | None = None,
    ) -> list[RawDocument]:
        """List raw documents that have not been processed with the version."""
        documents = self.list_documents(limit=None)
        unprocessed_documents: list[RawDocument] = []
        for document in documents:
            raw_document_id = derive_document_id(document)
            if not self.has_processed_document(raw_document_id, processing_version):
                unprocessed_documents.append(document)
            if limit is not None and len(unprocessed_documents) >= limit:
                break
        return unprocessed_documents

    def list_processed_documents(
        self,
        *,
        source_name: str | None = None,
        ticker: str | None = None,
        document_type: str | None = None,
        published_from: datetime | None = None,
        published_to: datetime | None = None,
        recent_cutoff: datetime | None = None,
        limit: int = 20,
    ) -> list[ProcessedDocument]:
        """List processed documents with simple filters."""
        with self.session_factory() as session:
            statement = select(ProcessedDocumentRecord).join(
                ProcessedDocumentRecord.raw_document
            ).join(DocumentRecord.source)
            if ticker:
                statement = statement.join(ProcessedDocumentRecord.ticker_links).where(
                    ProcessedDocumentTickerRecord.ticker == ticker.upper()
                )
            if source_name:
                statement = statement.where(SourceRecord.name == source_name)
            if document_type:
                statement = statement.where(ProcessedDocumentRecord.document_type == document_type)
            if recent_cutoff and published_from is None:
                statement = statement.where(ProcessedDocumentRecord.published_at >= recent_cutoff)
            if published_from:
                statement = statement.where(ProcessedDocumentRecord.published_at >= published_from)
            if published_to:
                statement = statement.where(ProcessedDocumentRecord.published_at <= published_to)
            statement = statement.order_by(ProcessedDocumentRecord.processed_at.desc()).limit(limit)
            records = session.scalars(statement).unique().all()
            return [_processed_record_to_document(record) for record in records]

    def get_processed_document(self, document_id: str) -> ProcessedDocument | None:
        """Return one processed document by ID."""
        with self.session_factory() as session:
            record = session.get(ProcessedDocumentRecord, document_id)
            if record is None:
                return None
            return _processed_record_to_document(record)

    def _save_document(self, session: Session, document: RawDocument) -> str:
        if not is_valid_raw_document(document):
            return "invalid"

        document = normalize_raw_document(document)
        document_id = derive_document_id(document)
        if session.get(DocumentRecord, document_id) is not None:
            return "duplicate"

        source = self._get_or_create_source(session, document)
        now = _utc_now()
        session.add(
            DocumentRecord(
                id=document_id,
                source_id=source.id,
                external_id=document.external_id,
                title=document.title,
                url=str(document.url) if document.url else None,
                published_at=document.published_at,
                content=document.content,
                raw_payload=document.raw_payload,
                metadata_=document.metadata,
                created_at=now,
                updated_at=now,
            )
        )
        return "inserted"

    def _get_or_create_source(self, session: Session, document: RawDocument) -> SourceRecord:
        source = session.scalar(
            select(SourceRecord).where(SourceRecord.name == document.source_name)
        )
        if source is not None:
            return source

        source = SourceRecord(
            name=document.source_name,
            source_type=_source_type_for(document),
            url=_source_url_for(document),
            created_at=_utc_now(),
        )
        session.add(source)
        session.flush()
        return source


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite:///"):
        database_path = database_url.removeprefix("sqlite:///")
        if database_path and database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(database_url)


def _record_to_document(record: DocumentRecord) -> RawDocument:
    return RawDocument(
        source_name=record.source.name,
        external_id=record.external_id,
        title=record.title,
        url=record.url,
        published_at=_ensure_utc(record.published_at),
        content=record.content,
        raw_payload=record.raw_payload,
        metadata=record.metadata_,
    )


def _processed_record_to_document(record: ProcessedDocumentRecord) -> ProcessedDocument:
    return ProcessedDocument(
        id=record.id,
        raw_document_id=record.raw_document_id,
        document_type=DocumentType(record.document_type),
        normalized_title=record.normalized_title,
        normalized_content=record.normalized_content,
        source_type=record.source_type,
        tickers=sorted(link.ticker for link in record.ticker_links),
        companies=record.companies,
        published_at=_ensure_utc(record.published_at),
        processed_at=_ensure_utc(record.processed_at) or record.processed_at,
        processing_version=record.processing_version,
    )


def _source_type_for(document: RawDocument) -> str:
    source_type = document.metadata.get("source_type")
    if isinstance(source_type, str) and source_type:
        return source_type
    if document.metadata.get("provider") == "yfinance" or "ticker" in document.raw_payload:
        return "market_data"
    if "feed_url" in document.metadata:
        return "rss"
    return "api"


def _source_url_for(document: RawDocument) -> str | None:
    feed_url = document.metadata.get("feed_url")
    if isinstance(feed_url, str):
        return feed_url
    return None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo:
        return value.astimezone(timezone.utc)
    return value.replace(tzinfo=timezone.utc)
