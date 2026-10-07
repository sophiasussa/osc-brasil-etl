import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from etl.extract import from_csv
from etl.transform import clean
from etl.load import (
    create_database_engine,
    create_tables,
    load_dataframe,
)


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)


def main() -> None:
    load_dotenv()

    filepath = Path("data/osc.csv")
    db_url = os.getenv("DB_URL")

    if not db_url:
        raise ValueError("DB_URL não configurada.")

    # --------------------------------------------------------------
    # Extract
    # --------------------------------------------------------------

    df = from_csv(filepath)

    # Para o primeiro teste, usamos apenas algumas linhas.
    df = df.head(100)

    logging.info(
        "Registros selecionados para teste: %d",
        len(df),
    )

    # --------------------------------------------------------------
    # Transform
    # --------------------------------------------------------------

    df = clean(df)

    logging.info(
        "DataFrame transformado com %d registros.",
        len(df),
    )

    # --------------------------------------------------------------
    # Load
    # --------------------------------------------------------------

    engine = create_database_engine(db_url)

    create_tables(engine)
    load_dataframe(df, engine)

    engine.dispose()

    logging.info("Pipeline executado com sucesso.")


if __name__ == "__main__":
    main()
