from pathlib import Path
from typing import Literal

import platformdirs
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    db_path: Path = Field(
        description="Path to the SQLite database file.",
        default=platformdirs.user_data_path(appname="jplabel") / "data.db",
    )
    image_path: Path = Field(
        description="Path to the download directory where raw images are stored.",
    )
    db_echo: bool | Literal["debug"] | None = Field(
        description="Whether to echo database queries.",
        default=False,
    )

    class Config:
        env_prefix = "jplabel_"
        env_file = ".env"


settings = Settings()
