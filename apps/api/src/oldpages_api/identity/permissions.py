from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.identity.service import IdentityService


async def can_initiate_chat(
    *,
    actor_user_id: int,
    target_user_id: int,
    session: AsyncSession,
    service: IdentityService,
) -> bool:
    _ = session
    return await service.can_initiate_chat(actor_user_id, target_user_id)
