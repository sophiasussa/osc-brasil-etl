import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from etl.extract import from_csv
from etl.load import create_tables, load_dataframe
from etl.transform import clean


BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

DB_URL = os.getenv("DB_URL")

CSV_PATH = BASE_DIR / "data" / "osc.csv"

TEST_RECORDS = 100


def test_etl_pipeline_should_load_data_into_postgresql():
    if not DB_URL:
        raise ValueError("DB_URL não configurada.")

    engine = create_engine(
        DB_URL,
        pool_pre_ping=True,
    )

    try:
        # Create database tables.
        create_tables(engine)

        # Start with a clean database.
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    TRUNCATE
                        organization_cnaes,
                        organization_areas,
                        organization_subareas,
                        organizations,
                        activity_subareas,
                        activity_areas,
                        cnaes,
                        municipalities,
                        legal_natures
                    RESTART IDENTITY CASCADE
                    """
                )
            )

        # Extract
        df = from_csv(CSV_PATH)

        assert not df.empty

        # Use a small subset for the integration test.
        df = df.head(TEST_RECORDS)

        assert len(df) == TEST_RECORDS

        # Transform
        df = clean(df)

        assert len(df) == TEST_RECORDS

        # Load
        load_dataframe(df, engine)

        # Verify the data in PostgreSQL.
        with engine.connect() as connection:
            organization_count = connection.execute(
                text(
                    "SELECT COUNT(*) FROM organizations"
                )
            ).scalar_one()

            municipality_count = connection.execute(
                text(
                    "SELECT COUNT(*) FROM municipalities"
                )
            ).scalar_one()

            legal_nature_count = connection.execute(
                text(
                    "SELECT COUNT(*) FROM legal_natures"
                )
            ).scalar_one()

            cnae_count = connection.execute(
                text(
                    "SELECT COUNT(*) FROM cnaes"
                )
            ).scalar_one()

            area_count = connection.execute(
                text(
                    "SELECT COUNT(*) FROM activity_areas"
                )
            ).scalar_one()

            subarea_count = connection.execute(
                text(
                    "SELECT COUNT(*) FROM activity_subareas"
                )
            ).scalar_one()

            organization_cnae_count = connection.execute(
                text(
                    "SELECT COUNT(*) FROM organization_cnaes"
                )
            ).scalar_one()

            organization_area_count = connection.execute(
                text(
                    "SELECT COUNT(*) FROM organization_areas"
                )
            ).scalar_one()

            organization_subarea_count = connection.execute(
                text(
                    "SELECT COUNT(*) FROM organization_subareas"
                )
            ).scalar_one()

        # Main entities
        assert organization_count == TEST_RECORDS
        assert municipality_count > 0
        assert legal_nature_count > 0

        # Reference data
        assert cnae_count > 0
        assert area_count > 0
        assert subarea_count > 0

        # Relationships
        assert organization_cnae_count > 0
        assert organization_area_count > 0
        assert organization_subarea_count > 0

    finally:
        engine.dispose()
