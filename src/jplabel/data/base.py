from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings
from .models import StampedBase

settings.db_path.parent.mkdir(parents=True, exist_ok=True)

database_url = f"sqlite:///{settings.db_path}"
database_echo = settings.db_echo

logger.info(f"Connecting to database: {database_url}")
engine = create_engine(database_url, echo=database_echo, future=True)

StampedBase.metadata.create_all(engine)

Session = sessionmaker(engine, future=True)
