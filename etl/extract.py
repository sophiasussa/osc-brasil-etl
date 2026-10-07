import logging

import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)


def from_csv(filepath: str) -> pd.DataFrame:
    """
    Lê o arquivo CSV do dataset OSC Brasil e retorna um DataFrame.

    Args:
        filepath: Caminho para o arquivo CSV.

    Returns:
        DataFrame contendo os dados brutos do CSV.
    """
    try:
        df = pd.read_csv(
            filepath,
            encoding="latin1",
            delimiter=";",
            decimal=",",
            dtype={"cnpj": "string"},
        )

        logging.info(
            "CSV carregado com sucesso: %d registros",
            len(df),
        )

        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug(
                "Primeiras 5 linhas:\n%s",
                df.head(5).to_string(),
            )

        return df

    except Exception as e:
        logging.error(
            "Erro ao ler o CSV: %s",
            e,
        )
        raise
