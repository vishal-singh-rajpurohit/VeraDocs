from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.db.database import get_db
from app.model.base import UserRole
from app.model.session import Session as DbSession
from app.model.tenant import Tenant
from app.model.user import User

logger = logging.getLogger("veradocs.auth")

router = APIRouter(prefix="/auth", tags=["Authentication & Tenancy"])


# --------------------------------------------------------------------------
# Password Hashing & JWT Helpers
# --------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Hash password using direct bcrypt."""
    pw_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception as exc:
        logger.error(f"Password verification error: {exc}")
        return False


def create_access_token(
    data: dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Encode a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        return jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# --------------------------------------------------------------------------
# Request & Response Schemas
# --------------------------------------------------------------------------
class SignUpRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    org_name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if "@" not in clean or "." not in clean:
            raise ValueError("Invalid email address format")
        return clean


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if "@" not in clean or "." not in clean:
            raise ValueError("Invalid email address format")
        return clean


class DetailsRequest(BaseModel):
    org_name: str
    workspace_slug: Optional[str] = None
    industry: Optional[str] = None
    role: Optional[str] = None
    document_types: Optional[List[str]] = None
    user_email: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    tenant_id: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    tenant_id: str


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------
@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignUpRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user and provision their initial tenant organization."""
    email_clean = request.email.lower().strip()

    # Check if a user with this email already exists
    existing = await db.execute(select(User).where(User.email == email_clean))
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # 1. Provision Tenant
    tenant_name = request.org_name or f"{request.first_name}'s Workspace"
    new_tenant = Tenant(name=tenant_name, plan="free")
    db.add(new_tenant)
    await db.flush()  # Populates new_tenant.id

    # 2. Create User
    new_user = User(
        tenant_id=new_tenant.id,
        email=email_clean,
        first_name=request.first_name.strip(),
        last_name=request.last_name.strip(),
        pass_hash=hash_password(request.password),
        role=UserRole.ADMIN,
    )
    db.add(new_user)
    await db.flush()  # Populates new_user.id

    # 3. Create Session Record
    token_payload = {
        "sub": str(new_user.id),
        "email": new_user.email,
        "tenant_id": str(new_tenant.id),
        "role": new_user.role.value,
    }
    access_token = create_access_token(token_payload)
    token_hash = hashlib.sha256(access_token.encode("utf-8")).hexdigest()[:64]

    new_session = DbSession(
        user_id=new_user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        device="web",
    )
    db.add(new_session)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=str(new_user.id),
            email=new_user.email,
            first_name=new_user.first_name,
            last_name=new_user.last_name,
            role=new_user.role.value,
            tenant_id=str(new_tenant.id),
        ),
        tenant_id=str(new_tenant.id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user with email and password."""
    email_clean = request.email.lower().strip()

    stmt = select(User).where(User.email == email_clean)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not verify_password(request.password, user.pass_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "tenant_id": str(user.tenant_id),
        "role": user.role.value,
    }
    access_token = create_access_token(token_payload)
    token_hash = hashlib.sha256(access_token.encode("utf-8")).hexdigest()[:64]

    new_session = DbSession(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        device="web",
    )
    db.add(new_session)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role.value,
            tenant_id=str(user.tenant_id),
        ),
        tenant_id=str(user.tenant_id),
    )


@router.post("/details")
async def update_details(
    request: DetailsRequest,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Onboarding endpoint to configure workspace / organization tenant details.
    Accepts Authorization: Bearer <token> or user_email fallback.
    """
    user: Optional[User] = None

    # Try decoding JWT if header present
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if user_id:
                stmt = select(User).where(User.id == uuid.UUID(user_id))
                res = await db.execute(stmt)
                user = res.scalars().first()
        except Exception:
            logger.info("Bearer token not verified in details; falling back to email")

    # Fallback lookup by email
    if not user and request.user_email:
        email_clean = request.user_email.lower().strip()
        stmt = select(User).where(User.email == email_clean)
        res = await db.execute(stmt)
        user = res.scalars().first()

    if user:
        # Update user's existing tenant
        tenant_stmt = select(Tenant).where(Tenant.id == user.tenant_id)
        tenant_res = await db.execute(tenant_stmt)
        tenant = tenant_res.scalars().first()
        if tenant:
            tenant.name = request.org_name
            await db.commit()
            return {
                "success": True,
                "tenant_id": str(tenant.id),
                "tenant_name": tenant.name,
                "user_id": str(user.id),
            }

    # If no existing user found (e.g. Google OAuth new user direct onboarding), provision a tenant
    new_tenant = Tenant(name=request.org_name, plan="free")
    db.add(new_tenant)
    await db.commit()
    await db.refresh(new_tenant)

    return {
        "success": True,
        "tenant_id": str(new_tenant.id),
        "tenant_name": new_tenant.name,
    }


@router.get("/me")
async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve currently authenticated user and tenant info."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    stmt = select(User).where(User.id == uuid.UUID(user_id))
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    tenant_stmt = select(Tenant).where(Tenant.id == user.tenant_id)
    t_res = await db.execute(tenant_stmt)
    tenant = t_res.scalars().first()

    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role.value,
        "tenant": {
            "id": str(tenant.id) if tenant else None,
            "name": tenant.name if tenant else None,
            "plan": tenant.plan if tenant else None,
        },
    }
