import logging

import pandas as pd
from sqlalchemy import create_engine


def to_postgresql(
    df: pd.DataFrame,
    db_url: str,
    table_name: str,
) -> None:
    """
    Loads a DataFrame into a PostgreSQL table.

    Args:
        df: DataFrame to be loaded.
        db_url: PostgreSQL connection URL.
        table_name: Target table name.
    """
    try:
        engine = create_engine(db_url)

        df.to_sql(
            table_name,
            con=engine,
            if_exists="replace",
            index=False,
            chunksize=1000,
        )

        logging.info(
            "Tabela '%s' carregada com sucesso no PostgreSQL.",
            table_name,
        )
    except Exception as e:
        logging.error(
            "Erro ao carregar dados no PostgreSQL: %s",
            e,
        )
        raise
