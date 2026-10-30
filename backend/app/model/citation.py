from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base import Base, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.model.message import Message
    from app.model.chunk import Chunk


class Citation(UUIDPrimaryKey, Base):
    """Links an assistant message to the chunks that support it."""

    __tablename__ = "citations"
    __table_args__ = (
        CheckConstraint("score IS NULL OR (score >= 0 AND score <= 1)", name="ck_citations_score"),
    )

    message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # SET NULL keeps the answer's citation history if a source document is deleted
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chunks.id", ondelete="SET NULL"), index=True
    )
    score: Mapped[float | None] = mapped_column(Float)

    message: Mapped[Message] = relationship("Message", back_populates="citations")
    chunk: Mapped[Chunk | None] = relationship("Chunk", back_populates="citations")
