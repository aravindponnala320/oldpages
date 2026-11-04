from __future__ import annotations

from fastapi import APIRouter, Request

from oldpages_api.example.schemas import ExampleResponse
from oldpages_api.example.service import get_example_response

router = APIRouter()


@router.get("/example", response_model=ExampleResponse)
async def example(request: Request) -> ExampleResponse:
    return get_example_response(request_id=request.state.request_id)
