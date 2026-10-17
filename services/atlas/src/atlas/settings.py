"""
Settings of the Atlas service, read from the environment and the service's .env file.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# ----- Consts ----- #

ENV_FILE_PATH = Path(__file__).resolve().parents[2] / ".env"

# ----- Classes ----- #


class AtlasSettings(BaseSettings):
    """
    Connection settings of the Atlas service.
    """
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        extra="ignore",
    )

    database_url: str
    test_database_url: str | None = None
