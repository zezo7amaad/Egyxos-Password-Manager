from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_db
from .models import Device, User, VaultItem
from .repository import RevisionConflict, authenticate_token, create_session, find_user, push_item
from .security import hash_password, verify_password

app = FastAPI(
    title="EGYXOS API",
    version="1.0.0",
    description="Account and encrypted-vault synchronization API. Vault contents are never decrypted here.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str = Field(min_length=12, max_length=256)


class SessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user_id: UUID


class EncryptedItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_id: UUID
    revision: int = Field(ge=1)
    operation: str = Field(pattern="^(upsert|delete)$")
    encrypted_payload: str = Field(min_length=1, max_length=2_000_000)
    encrypted_metadata: str | None = Field(default=None, max_length=100_000)
    device_id: UUID
    client_timestamp: datetime


class SyncResponse(BaseModel):
    changes: list[EncryptedItem]
    server_timestamp: datetime


class DeviceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    device_name: str = Field(min_length=1, max_length=200)
    device_type: str = Field(min_length=1, max_length=100)
    public_key: str | None = Field(default=None, max_length=10_000)


async def require_session(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization[7:].strip()
    if not token or len(token) > 256:
        raise HTTPException(status_code=401, detail="Authentication required")
    record = await authenticate_token(db, token)
    if not record:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    user = await db.get(User, record.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return user


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/auth/register", response_model=SessionResponse, status_code=201)
async def register(credentials: Credentials, db: AsyncSession = Depends(get_db)) -> SessionResponse:
    email = str(credentials.email).lower()
    if await find_user(db, email):
        raise HTTPException(status_code=409, detail="Account already exists")
    user = User(email=email, authentication_verifier=hash_password(credentials.password))
    db.add(user)
    await db.flush()
    token, record = await create_session(db, user.id)
    return SessionResponse(access_token=token, expires_at=record.expires_at, user_id=user.id)


@app.post("/api/v1/auth/login", response_model=SessionResponse)
async def login(credentials: Credentials, db: AsyncSession = Depends(get_db)) -> SessionResponse:
    user = await find_user(db, str(credentials.email).lower())
    if not user or not verify_password(credentials.password, user.authentication_verifier):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token, record = await create_session(db, user.id)
    return SessionResponse(access_token=token, expires_at=record.expires_at, user_id=user.id)


@app.post("/api/v1/sync/push", response_model=SyncResponse, status_code=status.HTTP_202_ACCEPTED)
async def push_changes(
    change: EncryptedItem,
    user: User = Depends(require_session),
    db: AsyncSession = Depends(get_db),
) -> SyncResponse:
    try:
        saved = await push_item(db, user.id, change)
    except RevisionConflict as conflict:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail={"code": "revision_conflict", "current_revision": conflict.current.revision},
        ) from None
    return SyncResponse(changes=[EncryptedItem(
        item_id=saved.id, revision=saved.revision,
        operation="delete" if saved.deleted_at else "upsert",
        encrypted_payload=saved.encrypted_payload, encrypted_metadata=saved.encrypted_metadata,
        device_id=saved.device_id, client_timestamp=saved.updated_at or datetime.now(timezone.utc),
    )], server_timestamp=datetime.now(timezone.utc))


@app.get("/api/v1/sync/pull", response_model=SyncResponse)
async def pull_changes(
    user: User = Depends(require_session),
    db: AsyncSession = Depends(get_db),
    cursor: int = Query(default=0, ge=0),
) -> SyncResponse:
    rows = (await db.scalars(
        select(VaultItem).where(VaultItem.owner_id == user.id, VaultItem.revision > cursor)
        .order_by(VaultItem.revision).limit(500)
    )).all()
    return SyncResponse(changes=[EncryptedItem(
        item_id=row.id, revision=row.revision, operation="delete" if row.deleted_at else "upsert",
        encrypted_payload=row.encrypted_payload, encrypted_metadata=row.encrypted_metadata,
        device_id=row.device_id, client_timestamp=row.updated_at or datetime.now(timezone.utc),
    ) for row in rows], server_timestamp=datetime.now(timezone.utc))


@app.post("/api/v1/devices", status_code=201)
async def register_device(
    request: DeviceRequest,
    user: User = Depends(require_session),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    device = Device(user_id=user.id, device_name=request.device_name, device_type=request.device_type, public_key=request.public_key)
    db.add(device)
    await db.commit()
    return {"device_id": str(device.id)}
