from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base import Base, CreatedAt, DocumentStatus, UUIDPrimaryKey, _enum

if TYPE_CHECKING:
    from app.model.tenant import Tenant
    from app.model.batch import Batch
    from app.model.chunk import Chunk


class Document(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "documents"
    __table_args__ = (
        # Duplicate detection: same file content once per tenant
        UniqueConstraint("tenant_id", "sha256", name="uq_documents_tenant_sha256"),
        Index("ix_documents_tenant_status", "tenant_id", "status"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("batches.id", ondelete="SET NULL"), index=True
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(127), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)  # S3/MinIO key
    status: Mapped[DocumentStatus] = mapped_column(
        _enum(DocumentStatus, "document_status"),
        default=DocumentStatus.QUEUED,
        nullable=False,
    )
    error: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="documents")
    batch: Mapped[Batch | None] = relationship("Batch", back_populates="documents")
    chunks: Mapped[list[Chunk]] = relationship(
        "Chunk", back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )
