from __future__ import annotations

from oldpages_api.identity.models import User
from oldpages_api.listings.exceptions import ForbiddenListingActionError
from oldpages_api.listings.models import Listing, MediaAsset


def require_listing_owner(user: User, listing: Listing) -> None:
    if listing.seller_user_id != user.id:
        raise ForbiddenListingActionError()


def require_media_owner(user: User, media_asset: MediaAsset) -> None:
    if media_asset.user_id != user.id:
        raise ForbiddenListingActionError("This media asset does not belong to the current user.")
