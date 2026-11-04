from __future__ import annotations

from fastapi import APIRouter

from oldpages_api.business.router import business_router
from oldpages_api.catalog.router import (
    authors_router,
    books_router,
    categories_router,
    publishers_router,
)
from oldpages_api.chat.router import chat_requests_router, conversations_router
from oldpages_api.clubs.router import (
    buddy_reads_router,
    club_books_router,
    clubs_router,
    events_router,
    readalongs_router,
)
from oldpages_api.commerce.router import (
    offers_router,
    pickups_router,
    reviews_router,
    transactions_router,
)
from oldpages_api.communities.router import communities_router, posts_router
from oldpages_api.donations.router import campaigns_router, donations_router
from oldpages_api.example.router import router as example_router
from oldpages_api.geo.router import geo_router, me_location_router
from oldpages_api.identity.router import router as identity_router
from oldpages_api.institutions.router import institutions_router
from oldpages_api.listings.router import listings_router, media_router
from oldpages_api.notifications.router import (
    notification_preferences_router,
    notifications_router,
)
from oldpages_api.payments.router import (
    carts_router,
    disputes_router,
    orders_router,
    payments_router,
    shipments_router,
)
from oldpages_api.reading.router import public_reading_router, reading_router
from oldpages_api.recommendations.router import (
    listings_router as similar_listings_router,
)
from oldpages_api.recommendations.router import (
    recommendations_router,
)
from oldpages_api.search.router import (
    follows_router,
    listing_favorites_router,
    saved_searches_router,
    search_router,
    wishlists_router,
)
from oldpages_api.subscriptions.router import (
    coupons_router,
    plans_router,
    promotions_router,
    subscriptions_router,
)
from oldpages_api.trust.router import admin_moderation_router, reports_router
from oldpages_api.users.router import router as users_router

api_router = APIRouter()
api_router.include_router(example_router, prefix="/foundation", tags=["foundation"])
api_router.include_router(identity_router)
api_router.include_router(users_router)
api_router.include_router(books_router)
api_router.include_router(categories_router)
api_router.include_router(authors_router)
api_router.include_router(publishers_router)
api_router.include_router(listings_router)
api_router.include_router(media_router)
api_router.include_router(search_router)
api_router.include_router(saved_searches_router)
api_router.include_router(wishlists_router)
api_router.include_router(listing_favorites_router)
api_router.include_router(follows_router)
api_router.include_router(chat_requests_router)
api_router.include_router(conversations_router)
api_router.include_router(offers_router)
api_router.include_router(pickups_router)
api_router.include_router(transactions_router)
api_router.include_router(reviews_router)
api_router.include_router(notifications_router)
api_router.include_router(notification_preferences_router)
api_router.include_router(reports_router)
api_router.include_router(admin_moderation_router)
api_router.include_router(communities_router)
api_router.include_router(posts_router)
api_router.include_router(clubs_router)
api_router.include_router(club_books_router)
api_router.include_router(buddy_reads_router)
api_router.include_router(readalongs_router)
api_router.include_router(events_router)
api_router.include_router(reading_router)
api_router.include_router(public_reading_router)
api_router.include_router(carts_router)
api_router.include_router(orders_router)
api_router.include_router(payments_router)
api_router.include_router(shipments_router)
api_router.include_router(disputes_router)
api_router.include_router(institutions_router)
api_router.include_router(campaigns_router)
api_router.include_router(donations_router)
api_router.include_router(business_router)
api_router.include_router(plans_router)
api_router.include_router(subscriptions_router)
api_router.include_router(promotions_router)
api_router.include_router(coupons_router)
api_router.include_router(recommendations_router)
api_router.include_router(similar_listings_router)
api_router.include_router(geo_router)
api_router.include_router(me_location_router)
