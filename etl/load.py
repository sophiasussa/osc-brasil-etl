import logging

import pandas as pd
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from etl.models import (
    Base,
    LegalNature,
    Municipality,
    Organization,
)


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

    logging.info("Database tables created successfully.")


def load_dataframe(
    df: pd.DataFrame,
    engine: Engine,
) -> None:
    """
    Loads transformed organizations into PostgreSQL.
    """

    with Session(engine) as session:
        try:
            _load_legal_natures(df, session)
            _load_municipalities(df, session)
            _load_organizations(df, session)

            session.commit()

        except Exception:
            session.rollback()
            raise

    logging.info(
        "Data loaded successfully: %d organizations.",
        len(df),
    )


def _load_legal_natures(
    df: pd.DataFrame,
    session: Session,
) -> None:
    """
    Loads legal nature reference data.
    """

    legal_natures = (
        df[
            ["natureza_juridica"]
        ]
        .dropna()
        .drop_duplicates()
    )

    for row in legal_natures.itertuples(index=False):
        code = int(row.natureza_juridica)

        existing = session.get(
            LegalNature,
            code,
        )

        if existing is None:
            session.add(
                LegalNature(
                    code=code,
                    # TODO: replace with official legal nature name.
                    name=f"Natureza jurídica {code}",
                )
            )


def _load_municipalities(
    df: pd.DataFrame,
    session: Session,
) -> None:
    """
    Loads municipality reference data.
    """

    municipalities = (
        df[
            [
                "cd_municipio",
                "municipio_nome",
                "UF_Sigla",
            ]
        ]
        .dropna(subset=["cd_municipio"])
        .drop_duplicates(subset=["cd_municipio"])
    )

    for row in municipalities.itertuples(index=False):
        code = int(row.cd_municipio)

        existing = session.get(
            Municipality,
            code,
        )

        if existing is None:
            session.add(
                Municipality(
                    code=code,
                    name=(
                        str(row.municipio_nome)
                        if pd.notna(row.municipio_nome)
                        else None
                    ),
                    uf=(
                        str(row.UF_Sigla)
                        if pd.notna(row.UF_Sigla)
                        else None
                    ),
                )
            )


def _load_organizations(
    df: pd.DataFrame,
    session: Session,
) -> None:
    """
    Loads organizations into PostgreSQL.
    """

    for _, row in df.iterrows():
        organization = Organization(
            cnpj=str(row["cnpj"]),
            legal_name=(
                str(row["tx_razao_social_osc"])
                if pd.notna(row["tx_razao_social_osc"])
                else None
            ),
            trade_name=(
                str(row["tx_nome_fantasia_osc"])
                if pd.notna(row["tx_nome_fantasia_osc"])
                else None
            ),
            legal_nature_code=(
                int(row["natureza_juridica"])
                if pd.notna(row["natureza_juridica"])
                else None
            ),
            matrix_or_branch=(
                str(row["matriz_filial"])
                if pd.notna(row["matriz_filial"])
                else None
            ),
            registration_status=str(
                row["situacao_cadastral"]
            ),
            removed_from_mosc=(
                bool(row["removida_do_mosc"])
                if pd.notna(row["removida_do_mosc"])
                else None
            ),
            foundation_date=(
                row["dt_fundacao_osc"]
                if pd.notna(row["dt_fundacao_osc"])
                else None
            ),
            closing_date=(
                row["data_fechamento"]
                if pd.notna(row["data_fechamento"])
                else None
            ),
            closing_year=(
                int(row["ano_fechamento"])
                if pd.notna(row["ano_fechamento"])
                else None
            ),
            address=(
                str(row["tx_endereco_completo"])
                if pd.notna(row["tx_endereco_completo"])
                else None
            ),
            municipality_code=(
                int(row["cd_municipio"])
                if pd.notna(row["cd_municipio"])
                else None
            ),
            latitude=(
                float(row["latitude"])
                if pd.notna(row["latitude"])
                else None
            ),
            longitude=(
                float(row["longitude"])
                if pd.notna(row["longitude"])
                else None
            ),
        )

        session.add(organization)
