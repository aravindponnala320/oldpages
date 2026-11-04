from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.business.exceptions import (
    AlreadyStaffError,
    BusinessLocationNotFoundError,
    BusinessProfileNotFoundError,
    BusinessValidationError,
    ForbiddenBusinessActionError,
    StaffAccountNotFoundError,
)
from oldpages_api.business.models import (
    BusinessLocation,
    BusinessProfile,
    InventoryImport,
    StaffAccount,
)
from oldpages_api.business.permissions import require_business_permission
from oldpages_api.business.repository import BusinessRepository
from oldpages_api.business.schemas import (
    ApprovalActionRequest,
    BusinessLocationCreateRequest,
    BusinessLocationResponse,
    BusinessProfileCreateRequest,
    BusinessProfileResponse,
    BusinessProfileUpdateRequest,
    InventoryImportCreateRequest,
    InventoryImportResponse,
    StaffAccountResponse,
    StaffInviteRequest,
)
from oldpages_api.identity.models import User
from oldpages_api.identity.security import utc_now

BUSINESS_PERMISSIONS = {
    "edit_profile",
    "manage_inventory",
    "manage_locations",
    "manage_staff",
}
ROLE_DEFAULT_PERMISSIONS = {
    "manager": ["edit_profile", "manage_inventory", "manage_locations"],
    "owner": sorted(BUSINESS_PERMISSIONS),
    "staff": ["manage_inventory"],
}
IMPORT_CONDITIONS = {"new", "like_new", "good", "fair", "poor"}


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    return slug


class BusinessService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = BusinessRepository(session)

    async def create_profile(
        self,
        payload: BusinessProfileCreateRequest,
        actor: User,
    ) -> BusinessProfileResponse:
        existing = await self.repo.get_profile_by_owner(actor.id)
        if existing is not None:
            raise BusinessValidationError("User already has a business profile.")
        base_slug = slugify(payload.name)
        slug = base_slug
        attempt = 0
        while await self.repo.get_profile_by_slug(slug) is not None:
            attempt += 1
            slug = f"{base_slug}-{attempt}"
        profile = BusinessProfile(
            owner_user_id=actor.id,
            name=payload.name,
            slug=slug,
            type=payload.type,
            description=payload.description,
            website=payload.website,
            status="pending",
        )
        self.repo.add(profile)
        await self.repo.flush()
        staff = StaffAccount(
            business_profile_id=profile.id,
            user_id=actor.id,
            role="owner",
            permissions_json=ROLE_DEFAULT_PERMISSIONS["owner"],
            status="active",
            invited_at=utc_now(),
            accepted_at=utc_now(),
        )
        self.repo.add(staff)
        await self.repo.commit()
        reloaded = await self.repo.get_profile_by_public_id(profile.public_id)
        if reloaded is None:
            raise BusinessValidationError("Profile could not be loaded.")
        return profile_response(reloaded)

    async def get_profile(self, profile_id_or_slug: str) -> BusinessProfileResponse:
        profile = await self.repo.get_profile_by_public_id(profile_id_or_slug)
        if profile is None:
            profile = await self.repo.get_profile_by_slug(profile_id_or_slug)
        if profile is None:
            raise BusinessProfileNotFoundError()
        return profile_response(profile)

    async def list_profiles(
        self,
        filters: dict[str, str] | None = None,
        limit: int = 20,
        cursor: str | None = None,
    ) -> list[BusinessProfileResponse]:
        profiles = await self.repo.list_profiles(filters, limit, cursor)
        return [profile_response(p) for p in profiles]

    async def update_profile(
        self,
        profile_id: str,
        payload: BusinessProfileUpdateRequest,
        actor: User,
    ) -> BusinessProfileResponse:
        profile = await self.repo.get_profile_by_public_id(profile_id)
        if profile is None:
            raise BusinessProfileNotFoundError()
        require_business_permission(profile, actor, "edit_profile")
        if payload.name is not None:
            profile.name = payload.name
        if payload.description is not None:
            profile.description = payload.description
        if payload.website is not None:
            profile.website = payload.website
        if payload.logo_url is not None:
            profile.logo_url = payload.logo_url
        if payload.cover_url is not None:
            profile.cover_url = payload.cover_url
        if payload.gstin is not None:
            profile.gstin = payload.gstin
        await self.repo.commit()
        reloaded = await self.repo.get_profile_by_public_id(profile.public_id)
        if reloaded is None:
            raise BusinessValidationError("Profile could not be loaded.")
        return profile_response(reloaded)

    async def add_location(
        self,
        profile_id: str,
        payload: BusinessLocationCreateRequest,
        actor: User,
    ) -> BusinessLocationResponse:
        profile = await self.repo.get_profile_by_public_id(profile_id)
        if profile is None:
            raise BusinessProfileNotFoundError()
        require_business_permission(profile, actor, "manage_locations")
        location = BusinessLocation(
            business_profile_id=profile.id,
            name=payload.name,
            address=payload.address,
            city=payload.city,
            state=payload.state,
            pincode=payload.pincode,
            is_primary=payload.is_primary,
        )
        self.repo.add(location)
        await self.repo.commit()
        reloaded = await self.repo.get_location_by_public_id(location.public_id)
        if reloaded is None:
            raise BusinessValidationError("Location could not be loaded.")
        return location_response(reloaded)

    async def update_location(
        self,
        location_id: str,
        payload: BusinessLocationCreateRequest,
        actor: User,
    ) -> BusinessLocationResponse:
        location = await self.repo.get_location_by_public_id(location_id)
        if location is None:
            raise BusinessLocationNotFoundError()
        profile = await self.repo.get_profile_by_id(location.business_profile_id)
        if profile is None:
            raise BusinessProfileNotFoundError()
        require_business_permission(profile, actor, "manage_locations")
        location.name = payload.name
        location.address = payload.address
        location.city = payload.city
        location.state = payload.state
        location.pincode = payload.pincode
        location.is_primary = payload.is_primary
        await self.repo.commit()
        reloaded = await self.repo.get_location_by_public_id(location.public_id)
        if reloaded is None:
            raise BusinessValidationError("Location could not be loaded.")
        return location_response(reloaded)

    async def remove_location(self, location_id: str, actor: User) -> None:
        location = await self.repo.get_location_by_public_id(location_id)
        if location is None:
            raise BusinessLocationNotFoundError()
        profile = await self.repo.get_profile_by_id(location.business_profile_id)
        if profile is None:
            raise BusinessProfileNotFoundError()
        require_business_permission(profile, actor, "manage_locations")
        await self.repo.delete(location)
        await self.repo.commit()

    async def invite_staff(
        self,
        profile_id: str,
        payload: StaffInviteRequest,
        actor: User,
    ) -> StaffAccountResponse:
        profile = await self.repo.get_profile_by_public_id(profile_id)
        if profile is None:
            raise BusinessProfileNotFoundError()
        require_business_permission(profile, actor, "manage_staff")
        from sqlalchemy import select as sa_select

        from oldpages_api.identity.models import User as UserModel

        result = await self.repo.session.execute(
            sa_select(UserModel).where(UserModel.public_id == payload.user_id)
        )
        target_user = result.scalar_one_or_none()
        if target_user is None:
            raise BusinessValidationError("User not found.")
        existing = await self.repo.get_staff(profile.id, target_user.id)
        if existing is not None:
            raise AlreadyStaffError()
        permissions = payload.permissions or ROLE_DEFAULT_PERMISSIONS[payload.role]
        unknown_permissions = sorted(set(permissions) - BUSINESS_PERMISSIONS)
        if unknown_permissions:
            raise BusinessValidationError(
                f"Unknown staff permissions: {', '.join(unknown_permissions)}"
            )
        staff = StaffAccount(
            business_profile_id=profile.id,
            permissions_json=permissions,
            user_id=target_user.id,
            role=payload.role,
            status="active",
            invited_at=utc_now(),
        )
        self.repo.add(staff)
        await self.repo.commit()
        reloaded = await self.repo.get_staff_by_public_id(staff.public_id)
        if reloaded is None:
            raise BusinessValidationError("Staff account could not be loaded.")
        return staff_response(reloaded)

    async def remove_staff(
        self,
        profile_id: str,
        user_public_id: str,
        actor: User,
    ) -> None:
        profile = await self.repo.get_profile_by_public_id(profile_id)
        if profile is None:
            raise BusinessProfileNotFoundError()
        require_business_permission(profile, actor, "manage_staff")
        from sqlalchemy import select as sa_select

        from oldpages_api.identity.models import User as UserModel

        result = await self.repo.session.execute(
            sa_select(UserModel).where(UserModel.public_id == user_public_id)
        )
        target_user = result.scalar_one_or_none()
        if target_user is None:
            raise BusinessValidationError("User not found.")
        staff = await self.repo.get_staff(profile.id, target_user.id)
        if staff is None:
            raise StaffAccountNotFoundError()
        if staff.role == "owner":
            raise ForbiddenBusinessActionError("Cannot remove the owner from staff.")
        await self.repo.delete(staff)
        await self.repo.commit()

    async def create_import(
        self,
        profile_id: str,
        payload: InventoryImportCreateRequest,
        actor: User,
    ) -> InventoryImportResponse:
        profile = await self.repo.get_profile_by_public_id(profile_id)
        if profile is None:
            raise BusinessProfileNotFoundError()
        require_business_permission(profile, actor, "manage_inventory")
        payload_hash = import_payload_hash(payload)
        existing_import = await self.repo.get_import_by_payload_hash(profile.id, payload_hash)
        if existing_import is not None:
            return import_response(existing_import)
        now = utc_now()
        error_rows = validate_import_rows(payload.rows)
        success_rows = len(payload.rows) - len(error_rows)
        status = "completed" if success_rows > 0 or not error_rows else "failed"
        inv_import = InventoryImport(
            business_profile_id=profile.id,
            completed_at=now,
            error_rows=len(error_rows),
            error_rows_json=error_rows,
            imported_by_user_id=actor.id,
            filename=payload.filename,
            payload_hash=payload_hash,
            started_at=now,
            status=status,
            success_rows=success_rows,
            total_rows=len(payload.rows),
        )
        self.repo.add(inv_import)
        await self.repo.flush()
        if error_rows:
            inv_import.error_report_url = (
                f"/api/v1/business/{profile.public_id}/imports/{inv_import.public_id}/errors.csv"
            )
        await self.repo.commit()
        reloaded = await self.repo.get_import_by_public_id(inv_import.public_id)
        if reloaded is None:
            raise BusinessValidationError("Import could not be loaded.")
        return import_response(reloaded)

    async def get_import_status(
        self,
        profile_id: str,
        import_id: str,
        actor: User,
    ) -> InventoryImportResponse:
        inv_import = await self.repo.get_import_by_public_id(import_id)
        if inv_import is None:
            raise BusinessValidationError("Import not found.")
        profile = await self.repo.get_profile_by_id(inv_import.business_profile_id)
        if profile is None:
            raise BusinessProfileNotFoundError()
        if profile.public_id != profile_id:
            raise BusinessValidationError("Import does not belong to this business profile.")
        require_business_permission(profile, actor, "manage_inventory")
        return import_response(inv_import)

    async def approve_profile(
        self,
        profile_id: str,
        actor: User,
    ) -> BusinessProfileResponse:
        profile = await self.repo.get_profile_by_public_id(profile_id)
        if profile is None:
            raise BusinessProfileNotFoundError()
        if profile.status == "active":
            return profile_response(profile)
        profile.status = "active"
        profile.rejected_reason = None
        profile.reviewed_by_user_id = actor.id
        profile.reviewed_at = utc_now()
        await self.repo.commit()
        reloaded = await self.repo.get_profile_by_public_id(profile.public_id)
        if reloaded is None:
            raise BusinessValidationError("Profile could not be loaded.")
        return profile_response(reloaded)

    async def reject_profile(
        self,
        profile_id: str,
        payload: ApprovalActionRequest,
        actor: User,
    ) -> BusinessProfileResponse:
        profile = await self.repo.get_profile_by_public_id(profile_id)
        if profile is None:
            raise BusinessProfileNotFoundError()
        profile.status = "rejected"
        profile.rejected_reason = payload.reason
        profile.reviewed_by_user_id = actor.id
        profile.reviewed_at = utc_now()
        await self.repo.commit()
        reloaded = await self.repo.get_profile_by_public_id(profile.public_id)
        if reloaded is None:
            raise BusinessValidationError("Profile could not be loaded.")
        return profile_response(reloaded)

    async def list_pending_profiles(
        self,
        limit: int = 50,
        cursor: str | None = None,
    ) -> list[BusinessProfileResponse]:
        profiles = await self.repo.list_profiles({"status": "pending"}, limit, cursor)
        return [profile_response(p) for p in profiles]

    async def get_my_profile(self, actor: User) -> BusinessProfileResponse | None:
        profile = await self.repo.get_profile_by_owner(actor.id)
        if profile is None:
            return None
        return profile_response(profile)

    async def get_import_error_report(
        self,
        profile_id: str,
        import_id: str,
        actor: User,
    ) -> str:
        inv_import = await self.repo.get_import_by_public_id(import_id)
        if inv_import is None:
            raise BusinessValidationError("Import not found.")
        profile = await self.repo.get_profile_by_id(inv_import.business_profile_id)
        if profile is None:
            raise BusinessProfileNotFoundError()
        if profile.public_id != profile_id:
            raise BusinessValidationError("Import does not belong to this business profile.")
        require_business_permission(profile, actor, "manage_inventory")
        return import_errors_csv(inv_import.error_rows_json)


def profile_response(profile: BusinessProfile) -> BusinessProfileResponse:
    return BusinessProfileResponse(
        id=profile.public_id,
        owner_user_id=profile.owner.public_id,
        name=profile.name,
        slug=profile.slug,
        type=profile.type,  # type: ignore[arg-type]
        description=profile.description,
        logo_url=profile.logo_url,
        cover_url=profile.cover_url,
        website=profile.website,
        gstin=profile.gstin,
        status=profile.status,  # type: ignore[arg-type]
        rejected_reason=profile.rejected_reason,
        is_verified=profile.is_verified,
        verified_at=profile.verified_at,
        listing_count=profile.listing_count,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def location_response(location: BusinessLocation) -> BusinessLocationResponse:
    return BusinessLocationResponse(
        id=location.public_id,
        business_profile_id=location.business_profile.public_id
        if location.business_profile
        else str(location.business_profile_id),
        name=location.name,
        address=location.address,
        city=location.city,
        state=location.state,
        country=location.country,
        pincode=location.pincode,
        latitude=location.latitude,
        longitude=location.longitude,
        is_primary=location.is_primary,
        created_at=location.created_at,
        updated_at=location.updated_at,
    )


def staff_response(staff: StaffAccount) -> StaffAccountResponse:
    return StaffAccountResponse(
        id=staff.public_id,
        user_id=staff.user.public_id if staff.user else str(staff.user_id),
        business_profile_id=staff.business_profile.public_id
        if staff.business_profile
        else str(staff.business_profile_id),
        role=staff.role,  # type: ignore[arg-type]
        permissions=staff.permissions_json,
        status=staff.status,  # type: ignore[arg-type]
        invited_at=staff.invited_at,
        accepted_at=staff.accepted_at,
        created_at=staff.created_at,
        updated_at=staff.updated_at,
    )


def import_payload_hash(payload: InventoryImportCreateRequest) -> str:
    if payload.idempotency_key is not None:
        return hashlib.sha256(payload.idempotency_key.encode("utf-8")).hexdigest()
    canonical = json.dumps(
        {"filename": payload.filename, "rows": payload.rows},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_import_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    error_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        errors: list[str] = []
        title = row.get("title")
        if not isinstance(title, str) or not title.strip():
            errors.append("title is required")
        price = row.get("price_amount_cents")
        if not isinstance(price, int) or price < 0:
            errors.append("price_amount_cents must be a non-negative integer")
        quantity = row.get("quantity", 1)
        if not isinstance(quantity, int) or quantity < 1:
            errors.append("quantity must be a positive integer")
        condition = row.get("condition", "good")
        if not isinstance(condition, str) or condition not in IMPORT_CONDITIONS:
            errors.append("condition must be one of fair, good, like_new, new, poor")
        if errors:
            error_rows.append(
                {
                    "errors": errors,
                    "row": row,
                    "row_number": index,
                }
            )
    return error_rows


def import_errors_csv(error_rows: list[Any]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["row_number", "errors", "row"])
    writer.writeheader()
    for error_row in error_rows:
        if not isinstance(error_row, dict):
            continue
        writer.writerow(
            {
                "errors": "; ".join(error_row.get("errors", [])),
                "row": json.dumps(error_row.get("row", {}), sort_keys=True),
                "row_number": error_row.get("row_number", ""),
            }
        )
    return buffer.getvalue()


def import_response(inv_import: InventoryImport) -> InventoryImportResponse:
    return InventoryImportResponse(
        id=inv_import.public_id,
        business_profile_id=inv_import.business_profile.public_id
        if inv_import.business_profile
        else str(inv_import.business_profile_id),
        filename=inv_import.filename,
        status=inv_import.status,  # type: ignore[arg-type]
        total_rows=inv_import.total_rows,
        success_rows=inv_import.success_rows,
        error_rows=inv_import.error_rows,
        error_report_url=inv_import.error_report_url,
        started_at=inv_import.started_at,
        completed_at=inv_import.completed_at,
        created_at=inv_import.created_at,
        updated_at=inv_import.updated_at,
    )
