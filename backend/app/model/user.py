from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base import Base, CreatedAt, UUIDPrimaryKey, UserRole, _enum

if TYPE_CHECKING:
    from app.model.tenant import Tenant
    from app.model.session import Session
    from app.model.conversation import Conversation
    from app.model.batch import Batch


class User(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    pass_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        _enum(UserRole, "user_role"), default=UserRole.MEMBER, nullable=False
    )

    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="users")
    sessions: Mapped[list[Session]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    conversations: Mapped[list[Conversation]] = relationship("Conversation", back_populates="user")
    batches: Mapped[list[Batch]] = relationship("Batch", back_populates="user")
