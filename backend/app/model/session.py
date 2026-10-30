from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base import Base, CreatedAt, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.model.user import User


class Session(UUIDPrimaryKey, CreatedAt, Base):
    """One row per login/device. Replaces refresh_token on the user row."""

    __tablename__ = "sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    device: Mapped[str | None] = mapped_column(String(255))

    user: Mapped[User] = relationship("User", back_populates="sessions")
