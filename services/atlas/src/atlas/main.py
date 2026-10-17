"""
FastAPI application for the Atlas service, which owns the PostgreSQL data.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from atlas.errors import DuplicateNameError, EntityNotFoundError
from atlas.routers.asset_types import router as asset_types_router
from atlas.routers.sites import router as sites_router

# ----- Consts ----- #

app = FastAPI(title="FieldOps Atlas")
app.include_router(sites_router)
app.include_router(asset_types_router)

# ----- Functions ----- #


@app.exception_handler(EntityNotFoundError)
def handle_entity_not_found(
    request: Request,
    error: EntityNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(error)},
    )


@app.exception_handler(DuplicateNameError)
def handle_duplicate_name(
    request: Request,
    error: DuplicateNameError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(error)},
    )

# ----- Routes ----- #


@app.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "ok"}
