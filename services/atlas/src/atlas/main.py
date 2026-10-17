"""
FastAPI application for the Atlas service, which owns the PostgreSQL data.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from fastapi import FastAPI

# ----- Consts ----- #

app = FastAPI(title="FieldOps Atlas")

# ----- Routes ----- #


@app.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "ok"}
