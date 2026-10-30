from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base import Base, CreatedAt, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.model.user import User
    from app.model.document import Document
    from app.model.conversation import Conversation


class Tenant(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="free", nullable=False)

    users: Mapped[list[User]] = relationship("User", back_populates="tenant")
    documents: Mapped[list[Document]] = relationship("Document", back_populates="tenant")
    conversations: Mapped[list[Conversation]] = relationship("Conversation", back_populates="tenant")
