from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base import Base, CreatedAt, MessageRole, UUIDPrimaryKey, _enum

if TYPE_CHECKING:
    from app.model.conversation import Conversation
    from app.model.citation import Citation


class Message(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[MessageRole] = mapped_column(_enum(MessageRole, "message_role"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Set by the hallucination-auditor agent; NULL for user messages
    verified: Mapped[bool | None] = mapped_column(Boolean)

    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="messages")
    citations: Mapped[list[Citation]] = relationship(
        "Citation", back_populates="message", cascade="all, delete-orphan", passive_deletes=True
    )
