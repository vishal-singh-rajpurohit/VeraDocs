from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base import Base, CreatedAt, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.model.tenant import Tenant
    from app.model.user import User
    from app.model.message import Message


class Conversation(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "conversations"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), default="New conversation", nullable=False)

    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="conversations")
    user: Mapped[User] = relationship("User", back_populates="conversations")
    messages: Mapped[list[Message]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Message.created_at",
    )
