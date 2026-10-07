import logging

from sqlalchemy import Engine, create_engine

from etl.models import Base


def create_database_engine(db_url: str) -> Engine:
    """
    Creates a SQLAlchemy engine for PostgreSQL.
    """
    return create_engine(
        db_url,
        pool_pre_ping=True,
    )


def create_tables(engine: Engine) -> None:
    """
    Creates all tables defined in the SQLAlchemy models.
    """
    Base.metadata.create_all(engine)

    logging.info(
        "Database tables created successfully."
    )
