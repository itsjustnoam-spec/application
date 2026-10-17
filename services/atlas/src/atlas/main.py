"""
FastAPI application for the Atlas service, which owns the PostgreSQL data.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from atlas.managers.errors import DuplicateNameError, EntityNotFoundError
from atlas.routers import asset_types, sites

# ----- Consts ----- #

app = FastAPI(title="FieldOps Atlas")
app.include_router(sites.router)
app.include_router(asset_types.router)

# ----- Functions ----- #


@app.exception_handler(EntityNotFoundError)
def handle_entity_not_found(
    request: Request,
    error: EntityNotFoundError,
) -> JSONResponse:
    """
    Turns a missing or archived row into a 404 response.
    """
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(error)},
    )


@app.exception_handler(DuplicateNameError)
def handle_duplicate_name(
    request: Request,
    error: DuplicateNameError,
) -> JSONResponse:
    """
    Turns a name conflict into a 409 response.
    """
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(error)},
    )

# ----- Routes ----- #


@app.get("/health")
def read_health() -> dict[str, str]:
    """
    Reports that the service is up.
    """
    return {"status": "ok"}
