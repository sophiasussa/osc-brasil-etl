import logging

import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)


def fix_mojibake(value: str) -> str:
    """
    Corrige textos que foram decodificados incorretamente
    como Latin-1 quando originalmente eram UTF-8.
    """
    try:
        return value.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa e transforma o DataFrame bruto do dataset OSC Brasil.

    As transformações são específicas para o formato atual
    do dataset e preservam a semântica dos dados de origem.
    """
    if df.empty:
        logging.warning(
            "DataFrame recebido está vazio. Nada será transformado."
        )
        return df

    df = df.copy()

    logging.info(f"Shape original do DataFrame: {df.shape}")

    # ------------------------------------------------------------------
    # 1. Remover linhas completamente vazias
    # ------------------------------------------------------------------

    before = len(df)

    df.dropna(how="all", inplace=True)

    logging.info(
        f"Linhas totalmente vazias removidas: {before - len(df)}"
    )

    # ------------------------------------------------------------------
    # 2. Limpeza básica de strings
    # ------------------------------------------------------------------

    text_columns = [
        "tx_razao_social_osc",
        "tx_nome_fantasia_osc",
        "tx_endereco_completo",
        "matriz_filial",
        "situacao_cadastral",
        "removida_do_mosc",
    ]

    for column in text_columns:
        if column in df.columns:
            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
            )

    # ------------------------------------------------------------------
    # 3. Corrigir mojibake
    # ------------------------------------------------------------------

    mojibake_columns = [
        "tx_endereco_completo",
        "matriz_filial",
        "removida_do_mosc",
    ]

    for column in mojibake_columns:
        if column in df.columns:
            df[column] = df[column].map(
                lambda value: (
                    fix_mojibake(value)
                    if pd.notna(value)
                    else value
                )
            )

    logging.info("Correção de encoding aplicada.")

    # ------------------------------------------------------------------
    # 4. CNPJ
    # ------------------------------------------------------------------

    if "cnpj" in df.columns:
        df["cnpj"] = (
            df["cnpj"]
            .astype("string")
            .str.strip()
        )

        invalid_cnpj = (
            df["cnpj"].notna()
            & ~df["cnpj"].str.fullmatch(r"\d{14}")
        )

        logging.info(
            f"CNPJs inválidos encontrados: {invalid_cnpj.sum()}"
        )

    # ------------------------------------------------------------------
    # 5. Natureza jurídica
    # ------------------------------------------------------------------

    if "natureza_juridica" in df.columns:
        df["natureza_juridica"] = (
            pd.to_numeric(
                df["natureza_juridica"],
                errors="coerce",
            )
            .astype("Int64")
        )

    # ------------------------------------------------------------------
    # 6. Situação cadastral
    # ------------------------------------------------------------------

    status_mapping = {
        "Ativa": "ACTIVE",
        "Inapta": "INAPT",
        "Nula ou Baixada": "CLOSED_OR_NULL",
        "Suspensa": "SUSPENDED",
    }

    if "situacao_cadastral" in df.columns:
        df["situacao_cadastral"] = (
            df["situacao_cadastral"]
            .replace(status_mapping)
        )

    # ------------------------------------------------------------------
    # 7. Matriz / filial
    # ------------------------------------------------------------------

    matrix_mapping = {
        "Matriz": "HEADQUARTERS",
        "Filial": "BRANCH",
        "Não Identificado": "UNKNOWN",
    }

    if "matriz_filial" in df.columns:
        df["matriz_filial"] = (
            df["matriz_filial"]
            .replace(matrix_mapping)
        )

    # ------------------------------------------------------------------
    # 8. Removida do MOSC
    # ------------------------------------------------------------------

    removed_mapping = {
        "sim": True,
        "não": False,
    }

    if "removida_do_mosc" in df.columns:
        df["removida_do_mosc"] = (
            df["removida_do_mosc"]
            .map(removed_mapping)
            .astype("boolean")
        )

    # ------------------------------------------------------------------
    # 9. Datas
    # ------------------------------------------------------------------

    for column in [
        "dt_fundacao_osc",
        "data_fechamento",
    ]:
        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce",
            ).dt.date

    # ------------------------------------------------------------------
    # 10. Ano de fechamento
    # ------------------------------------------------------------------

    if "ano_fechamento" in df.columns:
        df["ano_fechamento"] = (
            pd.to_numeric(
                df["ano_fechamento"],
                errors="coerce",
            )
            .astype("Int64")
        )

    # ------------------------------------------------------------------
    # 11. Município
    # ------------------------------------------------------------------

    if "cd_municipio" in df.columns:
        df["cd_municipio"] = (
            pd.to_numeric(
                df["cd_municipio"],
                errors="coerce",
            )
            .astype("Int64")
        )

        # 0 não representa um município válido.
        # Deve ser tratado como NULL no banco.
        df.loc[
            df["cd_municipio"] == 0,
            "cd_municipio",
        ] = pd.NA

    if "municipio_nome" in df.columns:
        df["municipio_nome"] = (
            df["municipio_nome"]
            .astype("string")
            .str.strip()
        )

    if "UF_Sigla" in df.columns:
        df["UF_Sigla"] = (
            df["UF_Sigla"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

    # ------------------------------------------------------------------
    # 12. Coordenadas
    # ------------------------------------------------------------------

    for column in ["latitude", "longitude"]:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    if "latitude" in df.columns:
        invalid_latitude = (
            df["latitude"].notna()
            & ~df["latitude"].between(-90, 90)
        )

        logging.info(
            f"Latitudes inválidas: {invalid_latitude.sum()}"
        )

        df.loc[invalid_latitude, "latitude"] = pd.NA

    if "longitude" in df.columns:
        invalid_longitude = (
            df["longitude"].notna()
            & ~df["longitude"].between(-180, 180)
        )

        logging.info(
            f"Longitudes inválidas: {invalid_longitude.sum()}"
        )

        df.loc[invalid_longitude, "longitude"] = pd.NA

    # ------------------------------------------------------------------
    # 13. CNAE principal
    # ------------------------------------------------------------------

    if "cnae" in df.columns:
        df["cnae"] = (
            pd.to_numeric(
                df["cnae"],
                errors="coerce",
            )
            .astype("Int64")
            .astype("string")
        )

    # ------------------------------------------------------------------
    # 14. CNAEs secundários
    # ------------------------------------------------------------------

    if "cnae_secundaria" in df.columns:
        df["cnae_secundaria"] = (
            df["cnae_secundaria"]
            .astype("string")
            .str.strip()
        )

    # ------------------------------------------------------------------
    # 15. Nomes e endereço
    # ------------------------------------------------------------------

    for column in [
        "tx_razao_social_osc",
        "tx_nome_fantasia_osc",
        "tx_endereco_completo",
    ]:
        if column in df.columns:
            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
            )

    # ------------------------------------------------------------------
    # Resultado
    # ------------------------------------------------------------------

    logging.info(f"Shape final do DataFrame: {df.shape}")
    logging.info("Transformações aplicadas com sucesso.")

    return df
