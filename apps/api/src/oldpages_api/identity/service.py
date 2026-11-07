from __future__ import annotations

import hashlib
import hmac
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.core.config import Settings
from oldpages_api.email import EmailClient, build_email_client
from oldpages_api.identity.exceptions import (
    DuplicateAccountError,
    ForbiddenIdentityActionError,
    InvalidCredentialsError,
    InvalidTokenError,
    RefreshTokenReuseError,
    UserNotFoundError,
)
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
from oldpages_api.identity.oauth import OAuthProvider, oauth_verifier
from oldpages_api.identity.repository import IdentityRepository
from oldpages_api.identity.schemas import (
    AuthenticatedRequestContext,
    AuthResponse,
    AuthUser,
    DevelopmentToken,
    LoginRequest,
    OAuthRequest,
    RegisterRequest,
    RequestAcceptedResponse,
    TokenPair,
    UpdateMeRequest,
    UserPrivateResponse,
    UserPublicResponse,
)
from oldpages_api.identity.security import (
    create_access_token,
    create_refresh_token,
    create_verification_token,
    decode_access_token,
    hash_password,
    hash_secret,
    normalize_email,
    utc_now,
    verify_password,
)
from oldpages_api.shared.db.ids import new_ulid


@dataclass(slots=True)
class SessionIssueResult:
    response: AuthResponse
    session: UserSession


class IdentityService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        email_client: EmailClient | None = None,
    ) -> None:
        self.repo = IdentityRepository(session)
        self.session = session
        self.settings = settings
        self.email_client = email_client or build_email_client(settings)

    async def register(
        self,
        payload: RegisterRequest,
        context: AuthenticatedRequestContext,
    ) -> AuthResponse:
        existing = await self.repo.get_user_by_email(payload.email)
        if existing is not None:
            raise DuplicateAccountError()

        if payload.username and await self.repo.get_profile_by_username(payload.username):
            raise DuplicateAccountError()

        now = utc_now()
        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            status="active",
        )
        self.repo.add(user)
        await self.repo.flush()

        profile = UserProfile(
            user_id=user.id,
            display_name=payload.display_name,
            username=payload.username,
        )
        preferences = UserPreference(user_id=user.id)
        consent = ConsentRecord(
            user_id=user.id,
            terms_version="2026-06-23",
            privacy_version="2026-06-23",
            accepted_at=now,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
        )
        self.repo.add(profile)
        self.repo.add(preferences)
        self.repo.add(consent)

        verification_token = await self._create_verification(
            user=user,
            verification_type="email",
            destination=user.email,
            expires_delta=timedelta(hours=self.settings.email_verification_token_hours),
        )
        await self._audit(
            action="USER_REGISTERED",
            actor_user_id=user.id,
            target_user_id=user.id,
            context={"email": user.email},
            request_context=context,
        )

        issue = await self._issue_session(
            user=user,
            context=context,
            device_fingerprint=None,
            device_name=None,
            device_type=None,
        )
        issue.response.email_verification = self._development_token(verification_token)
        await self.repo.commit()
        await self._send_verification_email(user.email, verification_token)
        return issue.response

    async def register_superuser(
        self,
        payload: RegisterRequest,
        context: AuthenticatedRequestContext,
    ) -> AuthResponse:
        existing = await self.repo.get_user_by_email(payload.email)
        if existing is not None:
            raise DuplicateAccountError()

        if payload.username and await self.repo.get_profile_by_username(payload.username):
            raise DuplicateAccountError()

        now = utc_now()
        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            status="active",
            is_superuser=True,
        )
        self.repo.add(user)
        await self.repo.flush()

        profile = UserProfile(
            user_id=user.id,
            display_name=payload.display_name,
            username=payload.username,
        )
        preferences = UserPreference(user_id=user.id)
        consent = ConsentRecord(
            user_id=user.id,
            terms_version="2026-06-23",
            privacy_version="2026-06-23",
            accepted_at=now,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
        )
        self.repo.add(profile)
        self.repo.add(preferences)
        self.repo.add(consent)

        verification_token = await self._create_verification(
            user=user,
            verification_type="email",
            destination=user.email,
            expires_delta=timedelta(hours=self.settings.email_verification_token_hours),
        )
        await self._audit(
            action="SUPERUSER_REGISTERED",
            actor_user_id=user.id,
            target_user_id=user.id,
            context={"email": user.email},
            request_context=context,
        )

        issue = await self._issue_session(
            user=user,
            context=context,
            device_fingerprint=None,
            device_name=None,
            device_type=None,
        )
        issue.response.email_verification = self._development_token(verification_token)
        await self.repo.commit()
        await self._send_verification_email(user.email, verification_token)
        return issue.response

    async def login(
        self, payload: LoginRequest, context: AuthenticatedRequestContext
    ) -> AuthResponse:
        user = await self.repo.get_user_by_email(payload.email)
        if (
            user is None
            or user.status != "active"
            or not verify_password(payload.password, user.password_hash)
        ):
            raise InvalidCredentialsError()

        issue = await self._issue_session(
            user=user,
            context=context,
            device_fingerprint=payload.device_fingerprint,
            device_name=payload.device_name,
            device_type=payload.device_type,
        )
        await self._audit(
            action="USER_LOGIN",
            actor_user_id=user.id,
            target_user_id=user.id,
            context={"session_id": issue.session.public_id},
            request_context=context,
        )
        await self.repo.commit()
        return issue.response

    async def refresh(
        self, refresh_token: str, context: AuthenticatedRequestContext
    ) -> AuthResponse:
        session_public_id = self._session_public_id_from_refresh(refresh_token)
        user_session = await self.repo.get_session_by_public_id(session_public_id)
        now = utc_now()
        if user_session is None:
            raise InvalidTokenError()
        user = await self.repo.get_user_by_id(user_session.user_id)
        if user is None or user.status != "active":
            raise InvalidTokenError()
        if (
            user_session.revoked_at is not None
            or as_utc(user_session.refresh_token_expires_at) <= now
        ):
            raise InvalidTokenError()

        supplied_hash = hash_secret(refresh_token, self.settings)
        if not hmac_compare(supplied_hash, user_session.refresh_token_hash):
            user_session.revoked_at = now
            user_session.revoked_reason = "refresh_reuse"
            user_session.reuse_detected_at = now
            await self._audit(
                action="REFRESH_TOKEN_REUSE_DETECTED",
                actor_user_id=user.id,
                target_user_id=user.id,
                context={"session_id": user_session.public_id},
                request_context=context,
            )
            await self.repo.commit()
            raise RefreshTokenReuseError()

        new_refresh_token, new_hash = create_refresh_token(user_session.public_id, self.settings)
        user_session.refresh_token_hash = new_hash
        user_session.refresh_token_expires_at = now + timedelta(
            days=self.settings.refresh_token_expire_days
        )
        user_session.last_used_at = now
        user_session.ip_address = context.ip_address
        user_session.user_agent = context.user_agent
        access_token = create_access_token(
            user_public_id=user.public_id,
            session_public_id=user_session.public_id,
            settings=self.settings,
            now=now,
        )
        await self.repo.commit()
        return self._auth_response(user, access_token, new_refresh_token)

    async def logout(self, refresh_token: str, context: AuthenticatedRequestContext) -> None:
        session_public_id = self._session_public_id_from_refresh(refresh_token)
        user_session = await self.repo.get_session_by_public_id(session_public_id)
        if user_session is None:
            return
        now = utc_now()
        user_session.revoked_at = now
        user_session.revoked_reason = "logout"
        await self._audit(
            action="USER_LOGOUT",
            actor_user_id=user_session.user_id,
            target_user_id=user_session.user_id,
            context={"session_id": user_session.public_id},
            request_context=context,
        )
        await self.repo.commit()

    async def logout_all(self, user: User, context: AuthenticatedRequestContext) -> None:
        await self.repo.revoke_sessions(user_id=user.id, now=utc_now(), reason="logout_all")
        await self._audit(
            action="USER_LOGOUT_ALL",
            actor_user_id=user.id,
            target_user_id=user.id,
            context={},
            request_context=context,
        )
        await self.repo.commit()

    async def verify_email(self, token: str, context: AuthenticatedRequestContext) -> None:
        verification = await self._consume_verification(token, "email")
        user = await self.repo.get_user_by_id(verification.user_id)
        if user is None:
            raise InvalidTokenError()
        user.email_verified_at = utc_now()
        await self._audit(
            action="USER_VERIFIED",
            actor_user_id=user.id,
            target_user_id=user.id,
            context={"verification_type": "email"},
            request_context=context,
        )
        await self.repo.commit()

    async def forgot_password(
        self,
        email: str,
        context: AuthenticatedRequestContext,
    ) -> RequestAcceptedResponse:
        user = await self.repo.get_user_by_email(normalize_email(email))
        token: str | None = None
        if user is not None and user.status == "active":
            token = await self._create_verification(
                user=user,
                verification_type="password_reset",
                destination=user.email,
                expires_delta=timedelta(minutes=self.settings.password_reset_token_minutes),
            )
            await self._audit(
                action="PASSWORD_RESET_REQUESTED",
                actor_user_id=user.id,
                target_user_id=user.id,
                context={},
                request_context=context,
            )
            await self.repo.commit()
            await self._send_password_reset_email(user.email, token)
        return RequestAcceptedResponse(
            accepted=True, development_token=self._development_token(token)
        )

    async def reset_password(
        self,
        *,
        token: str,
        new_password: str,
        context: AuthenticatedRequestContext,
    ) -> None:
        verification = await self._consume_verification(token, "password_reset")
        user = await self.repo.get_user_by_id(verification.user_id)
        if user is None or user.status != "active":
            raise InvalidTokenError()
        user.password_hash = hash_password(new_password)
        await self.repo.revoke_sessions(user_id=user.id, now=utc_now(), reason="password_reset")
        await self._audit(
            action="PASSWORD_RESET_COMPLETED",
            actor_user_id=user.id,
            target_user_id=user.id,
            context={},
            request_context=context,
        )
        await self.repo.commit()

    async def oauth_login(
        self,
        provider: OAuthProvider,
        payload: OAuthRequest,
        context: AuthenticatedRequestContext,
    ) -> AuthResponse:
        oauth_identity = await oauth_verifier.verify(provider, payload.id_token, self.settings)
        if payload.expected_email and payload.expected_email != oauth_identity.email:
            raise ForbiddenIdentityActionError("OAuth email did not match the expected account.")

        social_account = await self.repo.get_social_account(
            oauth_identity.provider,
            oauth_identity.provider_account_id,
        )
        now = utc_now()
        if social_account is not None:
            user = await self.repo.get_user_by_id(social_account.user_id)
            if user is None or user.status != "active":
                raise InvalidCredentialsError()
        else:
            existing_user = await self.repo.get_user_by_email(oauth_identity.email)
            if existing_user is not None:
                raise ForbiddenIdentityActionError(
                    "Existing accounts must link OAuth providers from an authenticated session."
                )
            user = User(
                email=oauth_identity.email,
                email_verified_at=now,
                status="active",
            )
            self.repo.add(user)
            await self.repo.flush()
            self.repo.add(
                UserProfile(
                    user_id=user.id,
                    display_name=oauth_identity.email.split("@", maxsplit=1)[0],
                )
            )
            self.repo.add(UserPreference(user_id=user.id))
            self.repo.add(
                SocialAccount(
                    user_id=user.id,
                    provider=oauth_identity.provider,
                    provider_account_id=oauth_identity.provider_account_id,
                    email=oauth_identity.email,
                    linked_at=now,
                )
            )

        issue = await self._issue_session(
            user=user,
            context=context,
            device_fingerprint=payload.device_fingerprint,
            device_name=payload.device_name,
            device_type=payload.device_type,
        )
        await self._audit(
            action="OAUTH_LOGIN",
            actor_user_id=user.id,
            target_user_id=user.id,
            context={"provider": provider, "session_id": issue.session.public_id},
            request_context=context,
        )
        await self.repo.commit()
        return issue.response

    async def get_user_from_access_token(self, access_token: str) -> tuple[User, str]:
        try:
            payload = decode_access_token(access_token, self.settings)
        except jwt.PyJWTError as exc:
            raise InvalidTokenError() from exc

        user_public_id = str(payload.get("sub") or "")
        session_public_id = str(payload.get("session_id") or "")
        if not user_public_id or not session_public_id:
            raise InvalidTokenError()
        user = await self.repo.get_user_by_public_id(user_public_id)
        if user is None or user.status != "active":
            raise InvalidTokenError()
        user_session = await self.repo.get_session_by_public_id(session_public_id)
        if (
            user_session is None
            or user_session.user_id != user.id
            or user_session.revoked_at is not None
        ):
            raise InvalidTokenError()
        return user, session_public_id

    async def private_user_response(self, user: User) -> UserPrivateResponse:
        profile = await self._profile_or_raise(user.id)
        preferences = await self._preferences_or_default(user.id)
        return UserPrivateResponse(
            bio=profile.bio,
            course_department=profile.course_department,
            display_name=profile.display_name,
            email=user.email,
            email_verified=user.email_verified_at is not None,
            favorite_authors=profile.favorite_authors,
            favorite_books=profile.favorite_books,
            favorite_genres=profile.favorite_genres,
            id=user.public_id,
            institution=profile.institution,
            languages=profile.languages,
            mobile_verified=user.mobile_verified_at is not None,
            preferences={
                "currency": preferences.currency,
                "locale": preferences.locale,
                "notifications_enabled": preferences.notifications_enabled,
                "timezone": preferences.timezone,
            },
            privacy={
                "allow_messages_from": profile.allow_messages_from,
                "hide_followers": profile.hide_followers,
                "hide_institution": profile.hide_institution,
                "hide_location": profile.hide_location,
                "hide_shelves": profile.hide_shelves,
                "privacy_level": profile.privacy_level,
                "show_online_status": profile.show_online_status,
                "show_read_receipts": profile.show_read_receipts,
            },
            profile_image_url=profile.profile_image_url,
            reading_interests=profile.reading_interests,
            status=user.status,
            username=profile.username,
        )

    async def public_user_response(self, public_id: str) -> UserPublicResponse:
        user = await self.repo.get_user_by_public_id(public_id)
        if user is None or user.status not in {"active", "pending_deletion"}:
            raise UserNotFoundError()
        profile = await self._profile_or_raise(user.id)
        location_visible = (
            profile.privacy_level == "public"
            and not profile.hide_location
            and user.status == "active"
        )
        institution_visible = (
            profile.privacy_level == "public"
            and not profile.hide_institution
            and user.status == "active"
        )
        public_bio = profile.bio if profile.privacy_level == "public" else None
        return UserPublicResponse(
            approximate_location=profile.approximate_location if location_visible else None,
            bio=public_bio,
            display_name=profile.display_name,
            id=user.public_id,
            institution=profile.institution if institution_visible else None,
            privacy_level=profile.privacy_level,
            profile_image_url=profile.profile_image_url
            if profile.privacy_level == "public"
            else None,
            username=profile.username,
            verification_badges=["email"] if user.email_verified_at is not None else [],
        )

    async def update_me(
        self,
        user: User,
        payload: UpdateMeRequest,
        context: AuthenticatedRequestContext,
    ) -> UserPrivateResponse:
        profile = await self._profile_or_raise(user.id)
        updates = payload.model_dump(exclude_unset=True)
        if "username" in updates and updates["username"]:
            existing = await self.repo.get_profile_by_username(updates["username"])
            if existing is not None and existing.user_id != user.id:
                raise DuplicateAccountError()
        for key, value in updates.items():
            setattr(profile, key, value)
        await self._audit(
            action="USER_PROFILE_UPDATED",
            actor_user_id=user.id,
            target_user_id=user.id,
            context={"fields": sorted(updates.keys())},
            request_context=context,
        )
        await self.repo.commit()
        return await self.private_user_response(user)

    async def block_user(
        self,
        *,
        actor: User,
        blocked_public_id: str,
        reason: str | None,
        context: AuthenticatedRequestContext,
    ) -> UserBlock:
        blocked_user = await self.repo.get_user_by_public_id(blocked_public_id)
        if blocked_user is None:
            raise UserNotFoundError()
        if blocked_user.id == actor.id:
            raise ForbiddenIdentityActionError("Users cannot block themselves.")
        existing = await self.repo.get_block(actor.id, blocked_user.id)
        if existing is not None:
            return existing
        block = UserBlock(blocker_user_id=actor.id, blocked_user_id=blocked_user.id, reason=reason)
        self.repo.add(block)
        await self._audit(
            action="USER_BLOCKED",
            actor_user_id=actor.id,
            target_user_id=blocked_user.id,
            context={},
            request_context=context,
        )
        await self.repo.commit()
        return block

    async def unblock_user(
        self,
        *,
        actor: User,
        blocked_public_id: str,
        context: AuthenticatedRequestContext,
    ) -> None:
        blocked_user = await self.repo.get_user_by_public_id(blocked_public_id)
        if blocked_user is None:
            raise UserNotFoundError()
        await self.repo.delete_block(actor.id, blocked_user.id)
        await self._audit(
            action="USER_UNBLOCKED",
            actor_user_id=actor.id,
            target_user_id=blocked_user.id,
            context={},
            request_context=context,
        )
        await self.repo.commit()

    async def request_account_deletion(
        self,
        user: User,
        context: AuthenticatedRequestContext,
    ) -> RequestAcceptedResponse:
        user.status = "pending_deletion"
        token = await self._create_verification(
            user=user,
            verification_type="account_deletion",
            destination=user.email,
            expires_delta=timedelta(hours=24),
        )
        await self._audit(
            action="ACCOUNT_DELETION_REQUESTED",
            actor_user_id=user.id,
            target_user_id=user.id,
            context={},
            request_context=context,
        )
        await self.repo.commit()
        return RequestAcceptedResponse(
            accepted=True, development_token=self._development_token(token)
        )

    async def request_data_export(
        self,
        user: User,
        context: AuthenticatedRequestContext,
    ) -> RequestAcceptedResponse:
        token = await self._create_verification(
            user=user,
            verification_type="data_export",
            destination=user.email,
            expires_delta=timedelta(hours=24),
        )
        await self._audit(
            action="DATA_EXPORT_REQUESTED",
            actor_user_id=user.id,
            target_user_id=user.id,
            context={},
            request_context=context,
        )
        await self.repo.commit()
        return RequestAcceptedResponse(
            accepted=True, development_token=self._development_token(token)
        )

    async def can_initiate_chat(self, actor_user_id: int, target_user_id: int) -> bool:
        return not await self.repo.has_block_between(actor_user_id, target_user_id)

    async def list_sessions(
        self,
        user: User,
        current_session_public_id: str | None,
    ) -> list[UserSession]:
        sessions = await self.repo.list_active_sessions(user.id)
        for item in sessions:
            item._current = item.public_id == current_session_public_id  # type: ignore[attr-defined]
        return sessions

    async def revoke_session(
        self,
        user: User,
        session_public_id: str,
        context: AuthenticatedRequestContext,
    ) -> None:
        user_session = await self.repo.get_session_for_user(user.id, session_public_id)
        if user_session is None:
            raise UserNotFoundError()
        user_session.revoked_at = utc_now()
        user_session.revoked_reason = "session_deleted"
        await self._audit(
            action="USER_SESSION_REVOKED",
            actor_user_id=user.id,
            target_user_id=user.id,
            context={"session_id": session_public_id},
            request_context=context,
        )
        await self.repo.commit()

    async def list_devices(self, user: User) -> list[UserDevice]:
        return await self.repo.list_devices(user.id)

    async def request_mobile_verification(
        self,
        user: User,
        mobile_number: str,
        context: AuthenticatedRequestContext,
    ) -> RequestAcceptedResponse:
        token = await self._create_verification(
            user=user,
            verification_type="mobile",
            destination=mobile_number,
            expires_delta=timedelta(minutes=10),
        )
        await self._audit(
            action="MOBILE_VERIFICATION_REQUESTED",
            actor_user_id=user.id,
            target_user_id=user.id,
            context={},
            request_context=context,
        )
        await self.repo.commit()
        return RequestAcceptedResponse(
            accepted=True, development_token=self._development_token(token)
        )

    async def _issue_session(
        self,
        *,
        user: User,
        context: AuthenticatedRequestContext,
        device_fingerprint: str | None,
        device_name: str | None,
        device_type: str | None,
    ) -> SessionIssueResult:
        now = utc_now()
        fingerprint = device_fingerprint or self._fingerprint(context.user_agent)
        device = await self.repo.get_device_by_fingerprint(user.id, fingerprint)
        if device is None:
            device = UserDevice(
                user_id=user.id,
                device_fingerprint=fingerprint,
                device_name=device_name,
                device_type=device_type,
                last_seen_at=now,
                created_from_user_agent=context.user_agent,
            )
            self.repo.add(device)
            await self.repo.flush()
        else:
            device.last_seen_at = now
            if device_name:
                device.device_name = device_name
            if device_type:
                device.device_type = device_type

        session_public_id = new_ulid()
        refresh_token, refresh_hash = create_refresh_token(session_public_id, self.settings)
        user_session = UserSession(
            public_id=session_public_id,
            user_id=user.id,
            device_id=device.id,
            refresh_token_hash=refresh_hash,
            refresh_token_expires_at=now + timedelta(days=self.settings.refresh_token_expire_days),
            last_used_at=now,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
        )
        self.repo.add(user_session)
        access_token = create_access_token(
            user_public_id=user.public_id,
            session_public_id=session_public_id,
            settings=self.settings,
            now=now,
        )
        return SessionIssueResult(
            response=self._auth_response(user, access_token, refresh_token),
            session=user_session,
        )

    async def _create_verification(
        self,
        *,
        user: User,
        verification_type: str,
        destination: str,
        expires_delta: timedelta,
    ) -> str:
        raw_token, token_hash = create_verification_token(self.settings)
        verification = UserVerification(
            user_id=user.id,
            verification_type=verification_type,
            token_hash=token_hash,
            destination=destination,
            expires_at=utc_now() + expires_delta,
        )
        self.repo.add(verification)
        return raw_token

    async def _consume_verification(self, token: str, verification_type: str) -> UserVerification:
        token_hash = hash_secret(token, self.settings)
        verification = await self.repo.get_verification_by_token_hash(token_hash)
        now = utc_now()
        if (
            verification is None
            or verification.verification_type != verification_type
            or verification.consumed_at is not None
            or as_utc(verification.expires_at) <= now
        ):
            raise InvalidTokenError()
        verification.consumed_at = now
        return verification

    async def _profile_or_raise(self, user_id: int) -> UserProfile:
        profile = await self.repo.get_profile_by_user_id(user_id)
        if profile is None:
            raise UserNotFoundError()
        return profile

    async def _preferences_or_default(self, user_id: int) -> UserPreference:
        result = await self.repo.get_preferences_by_user_id(user_id)
        if result is not None:
            return result
        preferences = UserPreference(user_id=user_id)
        self.repo.add(preferences)
        await self.repo.flush()
        return preferences

    def _auth_response(self, user: User, access_token: str, refresh_token: str) -> AuthResponse:
        return AuthResponse(
            tokens=TokenPair(
                access_token=access_token,
                expires_in_seconds=self.settings.access_token_expire_minutes * 60,
                refresh_token=refresh_token,
            ),
            user=AuthUser(
                email=user.email,
                email_verified=user.email_verified_at is not None,
                id=user.public_id,
                status=user.status,
            ),
        )

    def _development_token(self, token: str | None) -> DevelopmentToken | None:
        if token is None:
            return None
        if (
            self.settings.environment == "production"
            or not self.settings.expose_development_auth_tokens
        ):
            return DevelopmentToken(delivery="out_of_band", token=None)
        return DevelopmentToken(delivery="development", token=token)

    async def _send_verification_email(self, email: str, token: str | None) -> None:
        if token is None:
            return
        try:
            await self.email_client.send_verification(to=email, token=token)
        except Exception:
            # Email failures must not prevent account creation; log and continue.
            logging.getLogger(__name__).exception(
                "email_verification_send_failed", extra={"email": email}
            )

    async def _send_password_reset_email(self, email: str, token: str | None) -> None:
        if token is None:
            return
        try:
            await self.email_client.send_password_reset(to=email, token=token)
        except Exception:
            logging.getLogger(__name__).exception(
                "email_password_reset_send_failed", extra={"email": email}
            )

    def _session_public_id_from_refresh(self, refresh_token: str) -> str:
        if "." not in refresh_token:
            raise InvalidTokenError()
        session_public_id, _ = refresh_token.split(".", maxsplit=1)
        if not session_public_id:
            raise InvalidTokenError()
        return session_public_id

    async def _audit(
        self,
        *,
        action: str,
        actor_user_id: int | None,
        target_user_id: int | None,
        context: dict[str, object],
        request_context: AuthenticatedRequestContext,
    ) -> None:
        self.repo.add(
            AuditLog(
                actor_user_id=actor_user_id,
                target_user_id=target_user_id,
                action=action,
                context_json=context,
                ip_address=request_context.ip_address,
                user_agent=request_context.user_agent,
            )
        )

    @staticmethod
    def _fingerprint(user_agent: str | None) -> str:
        source = user_agent or "unknown-device"
        return hashlib.sha256(source.encode("utf-8")).hexdigest()


def hmac_compare(left: str, right: str) -> bool:
    return hmac.compare_digest(left, right)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
