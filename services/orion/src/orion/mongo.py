"""
MongoDB client setup for the documents service.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

import os
from typing import Any

from pymongo import MongoClient
from pymongo.database import Database

# ----- Consts ----- #

MONGO_URL: str = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
MONGO_DATABASE_NAME: str = os.environ.get("MONGO_DATABASE_NAME", "fieldops_documents")
mongo_client: MongoClient[dict[str, Any]] = MongoClient(MONGO_URL)

# ----- Functions ----- #


def get_documents_database() -> Database[dict[str, Any]]:
    return mongo_client[MONGO_DATABASE_NAME]
