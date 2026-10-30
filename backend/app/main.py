import logging
import uuid
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.db.database import get_db, init_db, check_pgvector_status
from app.model import Base, Tenant, User, Document, Chunk, Conversation, Message, Citation
from app.routes.auth import router as auth_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("veradocs.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown events."""
    logger.info("Starting VeraDocs Backend Service...")
    await init_db()
    yield
    logger.info("Shutting down VeraDocs Backend Service...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="VeraDocs AI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://client:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.API_V1_STR)

class VectorInsertRequest(BaseModel):
    tenant_id: Optional[str] = None
    document_id: Optional[str] = None
    content: str
    embedding: List[float]
    chunk_index: Optional[int] = 0
    page_number: Optional[int] = None


@app.get("/")
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "version": "1.0.0",
        "documentation": "/docs",
        "tables": list(Base.metadata.tables.keys()),
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}


@app.get("/health/db")
async def database_health():
    status = await check_pgvector_status()
    if not status["connected"]:
        raise HTTPException(status_code=503, detail=status)
    return status


@app.get(f"{settings.API_V1_STR}/vectors/status")
async def pgvector_status():
    return await check_pgvector_status()


@app.post(f"{settings.API_V1_STR}/vectors/test")
async def insert_test_vector(
    request: VectorInsertRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        t_id = uuid.UUID(request.tenant_id) if request.tenant_id else uuid.uuid4()
        d_id = uuid.UUID(request.document_id) if request.document_id else uuid.uuid4()

        new_chunk = Chunk(
            tenant_id=t_id,
            document_id=d_id,
            content=request.content,
            chunk_index=request.chunk_index or 0,
            page_number=request.page_number,
            embedding=request.embedding,
        )
        db.add(new_chunk)
        await db.commit()
        await db.refresh(new_chunk)
        return {
            "success": True,
            "id": str(new_chunk.id),
            "tenant_id": str(new_chunk.tenant_id),
            "document_id": str(new_chunk.document_id),
            "content": new_chunk.content,
            "embedding_length": len(request.embedding),
        }
    except Exception as exc:
        logger.error(f"Failed to insert test vector: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get(f"{settings.API_V1_STR}/vectors/similarity-search")
async def similarity_search(
    tenant_id: Optional[str] = Query(None),
    limit: int = Query(5, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    try:
        query_sql = "SELECT id, tenant_id, document_id, chunk_index, content FROM chunks"
        params = {}
        if tenant_id:
            query_sql += " WHERE tenant_id = :tenant_id"
            params["tenant_id"] = tenant_id
        query_sql += " LIMIT :limit"
        params["limit"] = limit

        result = await db.execute(text(query_sql), params)
        rows = result.mappings().all()
        return {
            "count": len(rows),
            "results": [dict(row) for row in rows],
        }
    except Exception as exc:
        logger.error(f"Similarity search failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
