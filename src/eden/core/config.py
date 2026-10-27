from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration, read from environment variables.
    Locally, values are also loaded from a .env file in the working directory.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    EDEN_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

    # Firebase RTDB. Credentials come from ADC (attached service account on
    # Cloud Run, or GOOGLE_APPLICATION_CREDENTIALS locally) - never a key in the repo.
    FIREBASE_DB_URL: str | None = None

    PROJECT_ID: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PROJECT_ID", "GOOGLE_CLOUD_PROJECT", "GCLOUD_PROJECT", "GCP_PROJECT"),
    )
    COMMUNITY_ID: str = "community_001"

    # Pub/Sub topics: sense -> think -> learn -> act
    TOPIC_SENSE_EVENTS: str = "eden-sense-events"
    TOPIC_THINK_OUTPUT: str = "eden-think-output"
    TOPIC_LEARN_TASKS: str = "eden-learn-tasks"
    TOPIC_ACT_ACTIONS: str = "eden-act-actions"


settings = Settings()
