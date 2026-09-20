import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Device, Session, User, VaultItem


class RevisionConflict(Exception):
    def __init__(self, current: VaultItem):
        self.current = current


async def find_user(session: AsyncSession, email: str) -> User | None:
    return await session.scalar(select(User).where(User.email == email.lower()))


async def create_session(session: AsyncSession, user_id: uuid.UUID) -> tuple[str, Session]:
    from .security import new_session_token, token_expiry

    token, digest = new_session_token()
    record = Session(user_id=user_id, token_hash=digest, expires_at=token_expiry())
    session.add(record)
    await session.commit()
    return token, record


async def authenticate_token(session: AsyncSession, token: str) -> Session | None:
    from .security import token_hash

    record = await session.scalar(select(Session).where(Session.token_hash == token_hash(token)))
    if not record or record.expires_at <= datetime.now(timezone.utc):
        return None
    return record


async def push_item(session: AsyncSession, user_id: uuid.UUID, item) -> VaultItem:
    current = await session.scalar(
        select(VaultItem).where(VaultItem.owner_id == user_id, VaultItem.id == item.item_id).with_for_update()
    )
    if current and item.revision != current.revision + 1:
        raise RevisionConflict(current)
    if not current and item.revision != 1:
        raise RevisionConflict(VaultItem(id=item.item_id, revision=0))
    if current:
        current.encrypted_payload = item.encrypted_payload
        current.encrypted_metadata = item.encrypted_metadata
        current.revision = item.revision
        current.device_id = item.device_id
        current.deleted_at = datetime.now(timezone.utc) if item.operation == "delete" else None
    else:
        current = VaultItem(
            id=item.item_id, owner_id=user_id, encrypted_payload=item.encrypted_payload,
            encrypted_metadata=item.encrypted_metadata, revision=item.revision,
            device_id=item.device_id,
            deleted_at=datetime.now(timezone.utc) if item.operation == "delete" else None,
        )
        session.add(current)
    await session.commit()
    await session.refresh(current)
    return current
