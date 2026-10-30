from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base import Base, CreatedAt, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.model.user import User
    from app.model.document import Document


class Batch(UUIDPrimaryKey, CreatedAt, Base):
    """Groups files uploaded together so progress can be tracked per upload."""

    __tablename__ = "batches"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped[User | None] = relationship("User", back_populates="batches")
    documents: Mapped[list[Document]] = relationship("Document", back_populates="batch")
