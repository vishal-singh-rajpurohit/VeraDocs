"""SQLAlchemy 2.0 multi-tenant RAG engine database models.

Modular export aggregating all separate domain models.
"""
from sqlalchemy.orm import configure_mappers

from app.model.base import (
    Base,
    CreatedAt,
    DocumentStatus,
    EMBEDDING_DIM,
    MessageRole,
    UUIDPrimaryKey,
    UserRole,
    _enum,
)
from app.model.tenant import Tenant
from app.model.user import User
from app.model.session import Session
from app.model.batch import Batch
from app.model.document import Document
from app.model.chunk import Chunk
from app.model.conversation import Conversation
from app.model.message import Message
from app.model.citation import Citation

# Explicitly configure all mappers across separate model files
configure_mappers()

__all__ = [
    "Base",
    "EMBEDDING_DIM",
    "UserRole",
    "DocumentStatus",
    "MessageRole",
    "UUIDPrimaryKey",
    "CreatedAt",
    "_enum",
    "Tenant",
    "User",
    "Session",
    "Batch",
    "Document",
    "Chunk",
    "Conversation",
    "Message",
    "Citation",
]
