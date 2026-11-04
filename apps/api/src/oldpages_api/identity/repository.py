from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.identity.models import (
    AuditLog,
    ConsentRecord,
    SocialAccount,
    User,
    UserBlock,
    UserDevice,
    UserPreference,
    UserProfile,
    UserSession,
    UserVerification,
)


class IdentityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_public_id(self, public_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.public_id == public_id))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_profile_by_user_id(self, user_id: int) -> UserProfile | None:
        result = await self.session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_preferences_by_user_id(self, user_id: int) -> UserPreference | None:
        result = await self.session.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_profile_by_username(self, username: str) -> UserProfile | None:
        result = await self.session.execute(
            select(UserProfile).where(func.lower(UserProfile.username) == username.lower())
        )
        return result.scalar_one_or_none()

    async def get_session_by_public_id(self, public_id: str) -> UserSession | None:
        result = await self.session.execute(
            select(UserSession).where(UserSession.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_session_for_user(
        self, user_id: int, session_public_id: str
    ) -> UserSession | None:
        result = await self.session.execute(
            select(UserSession).where(
                UserSession.public_id == session_public_id,
                UserSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_active_sessions(self, user_id: int) -> list[UserSession]:
        result = await self.session.execute(
            select(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            .order_by(UserSession.last_used_at.desc())
        )
        return list(result.scalars().all())

    async def list_devices(self, user_id: int) -> list[UserDevice]:
        result = await self.session.execute(
            select(UserDevice)
            .where(UserDevice.user_id == user_id)
            .order_by(UserDevice.last_seen_at.desc(), UserDevice.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_device_by_fingerprint(self, user_id: int, fingerprint: str) -> UserDevice | None:
        result = await self.session.execute(
            select(UserDevice).where(
                UserDevice.user_id == user_id,
                UserDevice.device_fingerprint == fingerprint,
            )
        )
        return result.scalar_one_or_none()

    async def get_social_account(
        self, provider: str, provider_account_id: str
    ) -> SocialAccount | None:
        result = await self.session.execute(
            select(SocialAccount).where(
                SocialAccount.provider == provider,
                SocialAccount.provider_account_id == provider_account_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_verification_by_token_hash(self, token_hash: str) -> UserVerification | None:
        result = await self.session.execute(
            select(UserVerification).where(UserVerification.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_sessions(
        self,
        *,
        user_id: int,
        now: datetime,
        reason: str,
        except_session_id: int | None = None,
    ) -> None:
        sessions = await self.list_active_sessions(user_id)
        for session in sessions:
            if except_session_id is not None and session.id == except_session_id:
                continue
            session.revoked_at = now
            session.revoked_reason = reason

    async def has_block_between(self, first_user_id: int, second_user_id: int) -> bool:
        result = await self.session.execute(
            select(UserBlock.id).where(
                or_(
                    (
                        (UserBlock.blocker_user_id == first_user_id)
                        & (UserBlock.blocked_user_id == second_user_id)
                    ),
                    (
                        (UserBlock.blocker_user_id == second_user_id)
                        & (UserBlock.blocked_user_id == first_user_id)
                    ),
                )
            )
        )
        return result.first() is not None

    async def get_block(self, blocker_user_id: int, blocked_user_id: int) -> UserBlock | None:
        result = await self.session.execute(
            select(UserBlock).where(
                UserBlock.blocker_user_id == blocker_user_id,
                UserBlock.blocked_user_id == blocked_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_block(self, blocker_user_id: int, blocked_user_id: int) -> None:
        await self.session.execute(
            delete(UserBlock).where(
                UserBlock.blocker_user_id == blocker_user_id,
                UserBlock.blocked_user_id == blocked_user_id,
            )
        )

    def add(self, instance: object) -> None:
        self.session.add(instance)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


__all__ = [
    "AuditLog",
    "ConsentRecord",
    "IdentityRepository",
    "SocialAccount",
    "User",
    "UserBlock",
    "UserDevice",
    "UserPreference",
    "UserProfile",
    "UserSession",
    "UserVerification",
]
