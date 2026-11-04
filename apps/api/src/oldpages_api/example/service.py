from __future__ import annotations

from oldpages_api import __version__
from oldpages_api.example.schemas import ExampleResponse


def get_example_response(request_id: str) -> ExampleResponse:
    return ExampleResponse(
        message="OldPages API foundation is running.",
        request_id=request_id,
        service="oldpages-api",
        version=__version__,
    )
