"""
Single entry point that forwards /api/<service>/... requests to the matching service.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse, Response

# ----- Consts ----- #

SERVICE_BASE_URLS: dict[str, str] = {
    "atlas": os.environ.get("ATLAS_SERVICE_URL", "http://localhost:8001"),
    "orion": os.environ.get("ORION_SERVICE_URL", "http://localhost:8002"),
}
HOP_BY_HOP_HEADERS = {"host", "content-length", "connection", "transfer-encoding"}
PROXIED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]

# ----- Classes ----- #


class UnknownServiceError(Exception):
    """
    Raised when a request targets a service that the proxy does not know.
    """

# ----- Functions ----- #


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with httpx.AsyncClient(timeout=30.0) as http_client:
        app.state.http_client = http_client
        yield


app = FastAPI(title="FieldOps Proxy", lifespan=lifespan)


def get_http_client(request: Request) -> httpx.AsyncClient:
    http_client: httpx.AsyncClient = request.app.state.http_client
    return http_client


def get_service_base_url(service_name: str) -> str:
    """
    Resolves the base URL of a registered service.

    :param service_name: Name of the service taken from the request path
    :return: Base URL that the request is forwarded to
    :raises UnknownServiceError: When no service is registered under the name
    """
    base_url = SERVICE_BASE_URLS.get(service_name)
    if base_url is None:
        raise UnknownServiceError(f"Service '{service_name}' is not registered.")
    return base_url


@app.exception_handler(UnknownServiceError)
async def handle_unknown_service(
    request: Request,
    error: UnknownServiceError,
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(error)})

# ----- Routes ----- #


@app.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "ok"}


@app.api_route(
    "/api/{service_name}/{path:path}",
    methods=PROXIED_METHODS,
)
async def forward_to_service(
    service_name: str,
    path: str,
    request: Request,
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> Response:
    """
    Forwards the request to the service registered under the given name.
    """
    base_url = get_service_base_url(service_name)
    forwarded_headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }
    upstream_response = await http_client.request(
        method=request.method,
        url=f"{base_url}/{path}",
        params=request.query_params,
        headers=forwarded_headers,
        content=await request.body(),
    )
    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        media_type=upstream_response.headers.get("content-type"),
    )
