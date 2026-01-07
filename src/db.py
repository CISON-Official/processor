#!/usr/bin/env python3
from decouple import config
from sqlmodel import Session
from sqlalchemy.engine import create_engine


def get_session() -> Session:
    db_database: str = str(config("DB_DATABASE"))
    db_username: str = str(config("DB_USERNAME"))
    db_password: str = str(config("DB_PASSWORD"))
    db_host: str = str(config("DB_HOST"))
    db_port: str = str(config("DB_PORT"))
    engine = create_engine(
        f"mysql+pymy://{db_username}:{db_password}@{db_host}:{db_port}/{db_database}"
    )
    return Session(engine)
