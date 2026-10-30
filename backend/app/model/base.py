from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

EMBEDDING_DIM = 1536  # must match your embedding model


class Base(DeclarativeBase):
    pass


# --------------------------------------------------------------------------
# Enums (stored as VARCHAR + CHECK, so adding a value needs no ALTER TYPE)
# --------------------------------------------------------------------------
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"


class DocumentStatus(str, enum.Enum):
    QUEUED = "queued"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    READY = "ready"
    FAILED = "failed"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


def _enum(e: type[enum.Enum], name: str) -> SAEnum:
    return SAEnum(
        e,
        name=name,
        native_enum=False,
        create_constraint=True,
        values_callable=lambda x: [m.value for m in x],
    )


# --------------------------------------------------------------------------
# Mixins
# --------------------------------------------------------------------------
class UUIDPrimaryKey:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class CreatedAt:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
