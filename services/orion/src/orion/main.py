"""
FastAPI application for the documents service, which stores files and metadata in MongoDB.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from fastapi import FastAPI

# ----- Consts ----- #

app = FastAPI(title="FieldOps Documents")

# ----- Routes ----- #


@app.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "ok"}
