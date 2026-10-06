import logging
import os

from dotenv import load_dotenv

from etl.extract import from_csv
from etl.load import to_postgresql
from etl.transform import clean


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)

load_dotenv()

DB_URL = os.getenv("DB_URL")


def run_pipeline() -> None:
    df = from_csv("data/oscs.csv")
    df_limpo = clean(df)

    if not DB_URL:
        raise ValueError(
            "Variável DB_URL não encontrada. Verifique o arquivo .env."
        )

    to_postgresql(
        df_limpo,
        DB_URL,
        "oscs",
    )


if __name__ == "__main__":
    run_pipeline()
