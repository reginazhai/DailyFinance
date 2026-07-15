"""Shared data models for DailyFinance."""

from dailyfinance.models.documents import RawDocument
from dailyfinance.models.processed_documents import DocumentType, ProcessedDocument

__all__ = ["DocumentType", "ProcessedDocument", "RawDocument"]
