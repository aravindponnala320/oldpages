from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from conftest import RegisterUser
from helpers import auth
from oldpages_api.identity.models import User
from oldpages_api.recommendations.models import Recommendation


@pytest.mark.asyncio
async def test_recommendation_surfaces_are_safe_without_training_data(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    user = await register_user(
        client,
        email="recommendations-user@example.com",
        username="recommendations-user",
    )
    token = user["tokens"]["access_token"]

    list_response = await client.get("/api/v1/recommendations", headers=auth(token))
    assert list_response.status_code == 200, list_response.text
    assert list_response.json() == {"items": [], "next_cursor": None}

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.public_id == user["user"]["id"]))
        user_model = result.scalar_one()
        session.add(
            Recommendation(
                confidence=0.73,
                entity_id=123,
                entity_type="listing",
                model="oldpages-rule-engine",
                model_version="1",
                provider="rules",
                reason="Trending in your city",
                score=0.73,
                source="trending",
                user_id=user_model.id,
            )
        )
        await session.commit()

    populated_response = await client.get("/api/v1/recommendations", headers=auth(token))
    assert populated_response.status_code == 200, populated_response.text
    recommendation = populated_response.json()["items"][0]
    assert recommendation["confidence"] == 0.73
    assert recommendation["model"] == "oldpages-rule-engine"
    assert recommendation["model_version"] == "1"
    assert recommendation["provider"] == "rules"

    refresh_response = await client.post("/api/v1/recommendations/refresh", headers=auth(token))
    assert refresh_response.status_code == 204, refresh_response.text

    category_response = await client.get(
        "/api/v1/recommendations/category-suggestions",
        params={
            "description": "A textbook for algebra and calculus exam preparation.",
            "title": "Mathematics Workbook",
        },
    )
    assert category_response.status_code == 200, category_response.text
    assert "mathematics" in category_response.json()["categories"]
    assert "education" in category_response.json()["categories"]

    price_response = await client.get(
        "/api/v1/recommendations/price-suggestion",
        params={"book_id": 1, "condition": "good"},
    )
    assert price_response.status_code == 200, price_response.text
    assert price_response.json()["basis"] == "no_data"

    condition_response = await client.get(
        "/api/v1/recommendations/condition-suggestion",
        params={
            "description": "Unopened sealed copy with original wrap.",
            "title": "Physics Guide",
        },
    )
    assert condition_response.status_code == 200, condition_response.text
    assert condition_response.json()["suggested_condition"] == "new_sealed"
    assert condition_response.json()["human_confirmation_required"] is True

    description_response = await client.get(
        "/api/v1/recommendations/listing-description",
        params={
            "condition": "good",
            "notes": "Light highlighting on two chapters.",
            "title": "Physics Guide",
        },
    )
    assert description_response.status_code == 200, description_response.text
    assert description_response.json()["editable"] is True
    assert description_response.json()["unsupported_metadata_warning"] is not None

    fraud_response = await client.get(
        "/api/v1/recommendations/fraud-priority",
        params={
            "description": "Pay outside on Telegram for a pirated PDF copy.",
            "price_amount_cents": 50,
            "title": "Exam Guide",
        },
    )
    assert fraud_response.status_code == 200, fraud_response.text
    assert fraud_response.json()["priority"] == "high"
    assert fraud_response.json()["review_only"] is True
    assert fraud_response.json()["auto_action_allowed"] is False
    assert fraud_response.json()["reasons"]
