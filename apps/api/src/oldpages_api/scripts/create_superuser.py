from __future__ import annotations

import argparse
import asyncio
import getpass

from sqlalchemy import select

from oldpages_api.identity.models import User, UserPreference, UserProfile
from oldpages_api.identity.security import hash_password, utc_now
from oldpages_api.shared.db.database import get_session_factory
from oldpages_api.shared.db.ids import new_ulid



# docker compose exec api python -m oldpages_api.scripts.create_superuser --email admin@oldpages.in --display-name Admin --username admin --password Admin1234!


async def run(email: str, password: str, display_name: str, username: str) -> None:
    async with get_session_factory()() as session:
        existing = await session.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none() is not None:
            print(f"User already exists: {email}")
            return

        user = User(
            public_id=new_ulid(),
            email=email,
            password_hash=hash_password(password),
            status="active",
            is_superuser=True,
            email_verified_at=utc_now(),
        )
        session.add(user)
        await session.flush()

        session.add(
            UserProfile(
                public_id=new_ulid(),
                user_id=user.id,
                display_name=display_name,
                username=username,
            )
        )
        session.add(UserPreference(public_id=new_ulid(), user_id=user.id))
        await session.commit()
        print(f"Superuser created: {email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a superuser account")
    parser.add_argument("--email", required=True, help="Superuser email address")
    parser.add_argument("--display-name", required=True, help="Display name")
    parser.add_argument("--username", required=True, help="Unique username")
    parser.add_argument("--password", help="Password (prompted if not provided)")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Password: ")
    if len(password) < 8:
        print("Error: password must be at least 8 characters")
        return

    asyncio.run(run(args.email, password, args.display_name, args.username))


if __name__ == "__main__":
    main()
