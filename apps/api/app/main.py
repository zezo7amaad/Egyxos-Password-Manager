from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(
    title="EGYXOS API",
    version="1.0.0",
    description="Account and encrypted-vault synchronization API. Vault contents are never decrypted here.",
)


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


def require_session(authorization: Annotated[str | None, Header()] = None) -> str:
    """Authentication is intentionally separate from vault decryption.

    The production deployment will validate a short-lived session token here.
    This dependency never accepts a master password or a decrypted key.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return authorization.removeprefix("Bearer ").strip()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/sync/push", response_model=SyncResponse, status_code=status.HTTP_202_ACCEPTED)
async def push_changes(
    change: EncryptedItem,
    _session: Annotated[str, Depends(require_session)],
) -> SyncResponse:
    """Accept an opaque encrypted mutation.

    Persistence and revision conflict checks belong in the repository/service
    layer. Keeping this contract opaque prevents accidental plaintext columns
    or logging from being added to the API boundary.
    """
    del change
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Encrypted sync persistence is not configured in this foundation build",
    )


@app.get("/api/v1/sync/pull", response_model=SyncResponse)
async def pull_changes(
    _session: Annotated[str, Depends(require_session)],
    cursor: str | None = None,
) -> SyncResponse:
    del cursor
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Encrypted sync persistence is not configured in this foundation build",
    )


@app.post("/api/v1/devices", status_code=status.HTTP_201_CREATED)
async def register_device(_session: Annotated[str, Depends(require_session)]) -> dict[str, str]:
    del _session
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Device persistence is not configured in this foundation build",
    )
