import logging

import pandas as pd

from sqlalchemy import Engine, create_engine, select, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from etl.models import (
    ActivityArea,
    ActivitySubarea,
    Base,
    Cnae,
    LegalNature,
    Municipality,
    Organization,
    OrganizationArea,
    OrganizationCnae,
    OrganizationSubarea,
)


# Source columns and their database names.
AREA_COLUMNS = {
    "Area_Assistencia_social": "Assistência social",
    "Area_Associacoes_patronais_e_profissionais": (
        "Associações patronais e profissionais"
    ),
    "Area_Cultura_e_recreacao": "Cultura e recreação",
    "Area_Desenvolvimento_e_defesa_de_direitos_e_interesses": (
        "Desenvolvimento e defesa de direitos e interesses"
    ),
    "Area_Educacao_e_pesquisa": "Educação e pesquisa",
    "Area_Outras_atividades_associativas": (
        "Outras atividades associativas"
    ),
    "Area_Religiao": "Religião",
    "Area_Saude": "Saúde",
}


SUBAREA_COLUMNS = {
    "SubArea_Assistencia_social": (
        "Assistência social",
        "Assistência social",
    ),
    "SubArea_Associacoes_de_atividades_nao_especificadas_anteriormente": (
        "Associações de atividades não especificadas anteriormente",
        "Associações patronais e profissionais",
    ),
    "SubArea_Associacoes_de_produtores_rurais_pescadores_e_similares": (
        "Associações de produtores rurais, pescadores e similares",
        "Associações patronais e profissionais",
    ),
    "SubArea_Associacoes_empresariais_e_patronais": (
        "Associações empresariais e patronais",
        "Associações patronais e profissionais",
    ),
    "SubArea_Associacoes_profissionais": (
        "Associações profissionais",
        "Associações patronais e profissionais",
    ),
    "SubArea_Atividades_de_apoio_a_educacao": (
        "Atividades de apoio à educação",
        "Educação e pesquisa",
    ),
    "SubArea_Cultura_e_arte": (
        "Cultura e arte",
        "Cultura e recreação",
    ),
    "SubArea_Desenvolvimento_e_defesa_de_direitos": (
        "Desenvolvimento e defesa de direitos",
        "Desenvolvimento e defesa de direitos e interesses",
    ),
    "SubArea_Educacao_infantil": (
        "Educação infantil",
        "Educação e pesquisa",
    ),
    "SubArea_Educacao_profissional": (
        "Educação profissional",
        "Educação e pesquisa",
    ),
    "SubArea_Ensino_fundamental": (
        "Ensino fundamental",
        "Educação e pesquisa",
    ),
    "SubArea_Ensino_superior": (
        "Ensino superior",
        "Educação e pesquisa",
    ),
    "SubArea_Esportes_e_recreacao": (
        "Esportes e recreação",
        "Cultura e recreação",
    ),
    "SubArea_Estudos_e_pesquisas": (
        "Estudos e pesquisas",
        "Educação e pesquisa",
    ),
    "SubArea_Hospitais": (
        "Hospitais",
        "Saúde",
    ),
    "SubArea_Outras_formas_de_educacao_ensino": (
        "Outras formas de educação e ensino",
        "Educação e pesquisa",
    ),
    "SubArea_Outros_servicos_de_saude": (
        "Outros serviços de saúde",
        "Saúde",
    ),
    "SubArea_Religiao": (
        "Religião",
        "Religião",
    ),
}


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
    Loads transformed data into PostgreSQL.

    Uses bulk SQLAlchemy inserts instead of creating one ORM
    object per database record.
    """

    if df.empty:
        logging.warning(
            "DataFrame is empty. Nothing to load."
        )
        return

    with Session(engine) as session:
        try:
            _load_legal_natures(df, session)
            _load_municipalities(df, session)
            _load_cnaes(df, session)
            _load_activity_areas(df, session)
            _load_activity_subareas(df, session)

            organization_ids = _load_organizations(
                df,
                session,
            )

            _load_organization_cnaes(
                df,
                session,
                organization_ids,
            )

            _load_organization_areas(
                df,
                session,
                organization_ids,
            )

            _load_organization_subareas(
                df,
                session,
                organization_ids,
            )

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
    Loads legal nature reference data in bulk.
    """

    if "natureza_juridica" not in df.columns:
        return

    codes = (
        df["natureza_juridica"]
        .dropna()
        .astype(int)
        .drop_duplicates()
        .tolist()
    )

    if not codes:
        return

    existing_codes = set(
        session.scalars(
            select(LegalNature.code).where(
                LegalNature.code.in_(codes)
            )
        ).all()
    )

    records = [
        {
            "code": code,
            # TODO: replace with official legal nature name.
            "name": f"Natureza jurídica {code}",
        }
        for code in codes
        if code not in existing_codes
    ]

    if records:
        session.execute(
            insert(LegalNature),
            records,
        )


def _load_municipalities(
    df: pd.DataFrame,
    session: Session,
) -> None:
    """
    Loads municipality reference data in bulk.
    """

    required_columns = {
        "cd_municipio",
        "municipio_nome",
        "UF_Sigla",
    }

    if not required_columns.issubset(df.columns):
        return

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

    if municipalities.empty:
        return

    codes = municipalities["cd_municipio"].astype(int).tolist()

    existing_codes = set(
        session.scalars(
            select(Municipality.code).where(
                Municipality.code.in_(codes)
            )
        ).all()
    )

    records = []

    for row in municipalities.itertuples(index=False):
        code = int(row.cd_municipio)

        if code in existing_codes:
            continue

        records.append(
            {
                "code": code,
                "name": (
                    str(row.municipio_nome)
                    if pd.notna(row.municipio_nome)
                    else None
                ),
                "uf": (
                    str(row.UF_Sigla)
                    if pd.notna(row.UF_Sigla)
                    else None
                ),
            }
        )

    if records:
        session.execute(
            insert(Municipality),
            records,
        )


def _load_cnaes(
    df: pd.DataFrame,
    session: Session,
) -> None:
    """
    Loads CNAE reference data in bulk.

    The source dataset provides CNAE codes but does not
    provide their official names.
    """

    cnae_codes: set[str] = set()

    if "cnae" in df.columns:
        primary_cnaes = (
            df["cnae"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        cnae_codes.update(
            code
            for code in primary_cnaes
            if code
        )

    if "cnae_secundaria" in df.columns:
        secondary_cnaes = df["cnae_secundaria"].dropna()

        for value in secondary_cnaes:
            cnae_codes.update(
                code.strip()
                for code in str(value).split("|")
                if code.strip()
            )

    if not cnae_codes:
        return

    existing_codes = set(
        session.scalars(
            select(Cnae.code).where(
                Cnae.code.in_(cnae_codes)
            )
        ).all()
    )

    records = [
        {
            "code": code,
            "name": None,
        }
        for code in cnae_codes
        if code not in existing_codes
    ]

    if records:
        session.execute(
            insert(Cnae),
            records,
        )


def _load_activity_areas(
    df: pd.DataFrame,
    session: Session,
) -> None:
    """
    Loads activity areas.
    """

    existing_areas = {
        area.name: area.id
        for area in session.scalars(
            select(ActivityArea)
        ).all()
    }

    next_id = max(
        existing_areas.values(),
        default=0,
    ) + 1

    records = []

    for name in AREA_COLUMNS.values():
        if name in existing_areas:
            continue

        records.append(
            {
                "id": next_id,
                "name": name,
            }
        )

        existing_areas[name] = next_id
        next_id += 1

    if records:
        session.execute(
            insert(ActivityArea),
            records,
        )


def _load_activity_subareas(
    df: pd.DataFrame,
    session: Session,
) -> None:
    """
    Loads activity subareas and associates each subarea
    with its parent activity area.
    """

    areas = {
        area.name: area.id
        for area in session.scalars(
            select(ActivityArea)
        ).all()
    }

    existing_subareas = {
        (subarea.area_id, subarea.name): subarea.id
        for subarea in session.scalars(
            select(ActivitySubarea)
        ).all()
    }

    existing_ids = [
        subarea.id
        for subarea in session.scalars(
            select(ActivitySubarea.id)
        ).all()
    ]

    next_id = max(
        existing_ids,
        default=0,
    ) + 1

    records = []

    for name, area_name in SUBAREA_COLUMNS.values():
        area_id = areas[area_name]

        key = (
            area_id,
            name,
        )

        if key in existing_subareas:
            continue

        records.append(
            {
                "id": next_id,
                "area_id": area_id,
                "name": name,
            }
        )

        existing_subareas[key] = next_id
        next_id += 1

    if records:
        session.execute(
            insert(ActivitySubarea),
            records,
        )


def _load_organizations(
    df: pd.DataFrame,
    session: Session,
) -> dict[str, int]:
    """
    Loads organizations in bulk and returns a mapping
    from CNPJ to generated organization ID.
    """

    records = []

    for row in df.itertuples(index=False):
        records.append(
            {
                "cnpj": str(row.cnpj),
                "legal_name": (
                    str(row.tx_razao_social_osc)
                    if pd.notna(row.tx_razao_social_osc)
                    else None
                ),
                "trade_name": (
                    str(row.tx_nome_fantasia_osc)
                    if pd.notna(row.tx_nome_fantasia_osc)
                    else None
                ),
                "legal_nature_code": (
                    int(row.natureza_juridica)
                    if pd.notna(row.natureza_juridica)
                    else None
                ),
                "matrix_or_branch": (
                    str(row.matriz_filial)
                    if pd.notna(row.matriz_filial)
                    else None
                ),
                "registration_status": str(
                    row.situacao_cadastral
                ),
                "removed_from_mosc": (
                    bool(row.removida_do_mosc)
                    if pd.notna(row.removida_do_mosc)
                    else None
                ),
                "foundation_date": (
                    row.dt_fundacao_osc
                    if pd.notna(row.dt_fundacao_osc)
                    else None
                ),
                "closing_date": (
                    row.data_fechamento
                    if pd.notna(row.data_fechamento)
                    else None
                ),
                "closing_year": (
                    int(row.ano_fechamento)
                    if pd.notna(row.ano_fechamento)
                    else None
                ),
                "address": (
                    str(row.tx_endereco_completo)
                    if pd.notna(row.tx_endereco_completo)
                    else None
                ),
                "municipality_code": (
                    int(row.cd_municipio)
                    if pd.notna(row.cd_municipio)
                    else None
                ),
                "latitude": (
                    float(row.latitude)
                    if pd.notna(row.latitude)
                    else None
                ),
                "longitude": (
                    float(row.longitude)
                    if pd.notna(row.longitude)
                    else None
                ),
            }
        )

    if not records:
        return {}

    # PostgreSQL handles duplicate CNPJs safely.
    statement = pg_insert(Organization).values(
        records
    )

    statement = statement.on_conflict_do_nothing(
        index_elements=["cnpj"]
    )

    session.execute(statement)

    # Retrieve generated IDs for the organizations loaded
    # in this batch.
    cnpjs = [record["cnpj"] for record in records]

    organization_ids: dict[str, int] = {}

    batch_size = 10_000

    for start in range(
        0,
        len(cnpjs),
        batch_size,
    ):
        batch = cnpjs[
            start : start + batch_size
        ]

        rows = session.execute(
            select(
                Organization.cnpj,
                Organization.id,
            ).where(
                Organization.cnpj.in_(batch)
            )
        ).all()

        organization_ids.update(
            {
                cnpj: organization_id
                for cnpj, organization_id in rows
            }
        )

    return organization_ids


def _load_organization_cnaes(
    df: pd.DataFrame,
    session: Session,
    organization_ids: dict[str, int],
) -> None:
    """
    Loads organization/CNAE relationships in bulk.
    """

    records = []

    for row in df.itertuples(index=False):
        organization_id = organization_ids.get(
            str(row.cnpj)
        )

        if organization_id is None:
            continue

        if pd.notna(row.cnae):
            records.append(
                {
                    "organization_id": organization_id,
                    "cnae_code": str(row.cnae).strip(),
                    "is_primary": True,
                }
            )

        if pd.notna(row.cnae_secundaria):
            for code in str(
                row.cnae_secundaria
            ).split("|"):
                code = code.strip()

                if code:
                    records.append(
                        {
                            "organization_id": organization_id,
                            "cnae_code": code,
                            "is_primary": False,
                        }
                    )

    if not records:
        return

    statement = pg_insert(
        OrganizationCnae
    ).values(records)

    statement = statement.on_conflict_do_nothing(
        index_elements=[
            "organization_id",
            "cnae_code",
        ]
    )

    session.execute(statement)


def _load_organization_areas(
    df: pd.DataFrame,
    session: Session,
    organization_ids: dict[str, int],
) -> None:
    """
    Loads organization/activity-area relationships
    in bulk.
    """

    areas = {
        area.name: area.id
        for area in session.scalars(
            select(ActivityArea)
        ).all()
    }

    records = []

    for row in df.itertuples(index=False):
        organization_id = organization_ids.get(
            str(row.cnpj)
        )

        if organization_id is None:
            continue

        for column, area_name in AREA_COLUMNS.items():
            value = getattr(row, column)

            if pd.isna(value) or value != 1:
                continue

            records.append(
                {
                    "organization_id": organization_id,
                    "area_id": areas[area_name],
                }
            )

    if not records:
        return

    statement = pg_insert(
        OrganizationArea
    ).values(records)

    statement = statement.on_conflict_do_nothing(
        index_elements=[
            "organization_id",
            "area_id",
        ]
    )

    session.execute(statement)


def _load_organization_subareas(
    df: pd.DataFrame,
    session: Session,
    organization_ids: dict[str, int],
) -> None:
    """
    Loads organization/activity-subarea relationships
    in bulk.
    """

    areas = {
        area.name: area.id
        for area in session.scalars(
            select(ActivityArea)
        ).all()
    }

    subareas = {
        (subarea.area_id, subarea.name): subarea.id
        for subarea in session.scalars(
            select(ActivitySubarea)
        ).all()
    }

    records = []

    for row in df.itertuples(index=False):
        organization_id = organization_ids.get(
            str(row.cnpj)
        )

        if organization_id is None:
            continue

        for column, (
            subarea_name,
            area_name,
        ) in SUBAREA_COLUMNS.items():

            value = getattr(row, column)

            if pd.isna(value) or value != 1:
                continue

            area_id = areas[area_name]

            subarea_id = subareas.get(
                (
                    area_id,
                    subarea_name,
                )
            )

            if subarea_id is None:
                continue

            records.append(
                {
                    "organization_id": organization_id,
                    "subarea_id": subarea_id,
                }
            )

    if not records:
        return

    statement = pg_insert(
        OrganizationSubarea
    ).values(records)

    statement = statement.on_conflict_do_nothing(
        index_elements=[
            "organization_id",
            "subarea_id",
        ]
    )

    session.execute(statement)
