import logging
import sys
import time

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
        "Outras atividades associativas",
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


def validate_activity_mappings(df: pd.DataFrame) -> None:
    """Validates activity mapping definitions and source columns."""

    expected_columns = set(AREA_COLUMNS) | set(SUBAREA_COLUMNS)
    missing_columns = expected_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            "Required activity columns are missing from "
            f"the DataFrame: {sorted(missing_columns)}"
        )

    mapped_areas = set(AREA_COLUMNS.values())
    mapped_parent_areas = {
        area_name
        for _, area_name in SUBAREA_COLUMNS.values()
    }

    undefined_parent_areas = mapped_parent_areas - mapped_areas

    if undefined_parent_areas:
        raise ValueError(
            "Subareas reference undefined parent areas: "
            f"{sorted(undefined_parent_areas)}"
        )

    logging.info(
        "Activity mappings validated: %d areas and %d subareas.",
        len(AREA_COLUMNS),
        len(SUBAREA_COLUMNS),
    )


def validate_organization_activity_data(
    df: pd.DataFrame,
) -> None:
    """Checks consistency between organization activity areas and subareas."""

    area_columns = list(AREA_COLUMNS)
    subarea_columns = list(SUBAREA_COLUMNS)

    areas_marked = df[area_columns].eq(1).any(axis=1)
    subareas_marked = df[subarea_columns].eq(1).any(axis=1)

    areas_without_subareas = areas_marked & ~subareas_marked
    subareas_without_areas = subareas_marked & ~areas_marked

    logging.info(
        "Organizations with areas but no subareas: %d",
        int(areas_without_subareas.sum()),
    )

    logging.info(
        "Organizations with subareas but no areas: %d",
        int(subareas_without_areas.sum()),
    )

    inconsistent_subareas = []

    for column, (subarea_name, parent_area_name) in SUBAREA_COLUMNS.items():
        parent_area_column = next(
            (
                area_column
                for area_column, area_name in AREA_COLUMNS.items()
                if area_name == parent_area_name
            ),
            None,
        )

        if parent_area_column is None:
            raise ValueError(
                f"Parent area not found for subarea: {subarea_name}"
            )

        invalid_rows = (
            df[column].eq(1)
            & ~df[parent_area_column].eq(1)
        )

        if invalid_rows.any():
            inconsistent_subareas.append(
                {
                    "subarea": subarea_name,
                    "parent_area": parent_area_name,
                    "count": int(invalid_rows.sum()),
                    "cnpjs": (
                        df.loc[invalid_rows, "cnpj"]
                        .head(5)
                        .tolist()
                    ),
                }
            )

    if inconsistent_subareas:
        for item in inconsistent_subareas:
            logging.warning(
                "Subarea marked without its parent area: "
                "subarea=%s, parent_area=%s, count=%d, "
                "example_cnpjs=%s",
                item["subarea"],
                item["parent_area"],
                item["count"],
                item["cnpjs"],
            )
    else:
        logging.info(
            "All marked subareas have their parent area marked."
        )


def create_database_engine(db_url: str) -> Engine:
    """Creates a SQLAlchemy engine for PostgreSQL."""

    return create_engine(
        db_url,
        pool_pre_ping=True,
    )


def create_tables(engine: Engine) -> None:
    """Creates all tables defined in the SQLAlchemy models."""

    Base.metadata.create_all(engine)
    logging.info("Database tables created successfully.")


def load_dataframe(
    df: pd.DataFrame,
    engine: Engine,
) -> None:
    """Loads transformed data into PostgreSQL and logs stage durations."""

    if df.empty:
        logging.warning("DataFrame is empty. Nothing to load.")
        return

    validate_activity_mappings(df)
    validate_organization_activity_data(df)

    with Session(engine) as session:
        try:
            reference_stages = [
                ("Legal natures", _load_legal_natures),
                ("Municipalities", _load_municipalities),
                ("CNAEs", _load_cnaes),
                ("Activity areas", _load_activity_areas),
                ("Activity subareas", _load_activity_subareas),
            ]

            for stage_name, stage_function in reference_stages:
                stage_start = time.perf_counter()
                stage_function(df, session)
                elapsed = time.perf_counter() - stage_start

                logging.info(
                    "Load stage '%s': %.2f seconds",
                    stage_name,
                    elapsed,
                )

            stage_start = time.perf_counter()
            organization_ids = _load_organizations(df, session)
            elapsed = time.perf_counter() - stage_start

            logging.info(
                "Load stage 'Organizations and ID lookup': %.2f seconds",
                elapsed,
            )

            relationship_stages = [
                (
                    "Organization-CNAE relationships",
                    _load_organization_cnaes,
                ),
                (
                    "Organization-area relationships",
                    _load_organization_areas,
                ),
                (
                    "Organization-subarea relationships",
                    _load_organization_subareas,
                ),
            ]

            for stage_name, stage_function in relationship_stages:
                stage_start = time.perf_counter()

                stage_function(df, session, organization_ids)

                elapsed = time.perf_counter() - stage_start

                logging.info(
                    "Load stage '%s': %.2f seconds",
                    stage_name,
                    elapsed,
                )

            stage_start = time.perf_counter()
            session.commit()
            commit_elapsed = time.perf_counter() - stage_start

            logging.info(
                "Load stage 'Commit': %.2f seconds",
                commit_elapsed,
            )

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
    """Loads legal nature reference data in bulk."""

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
        session.execute(insert(LegalNature), records)


def _load_municipalities(
    df: pd.DataFrame,
    session: Session,
) -> None:
    """Loads municipality reference data in bulk."""

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
        session.execute(insert(Municipality), records)


def _load_cnaes(
    df: pd.DataFrame,
    session: Session,
) -> None:
    """Loads CNAE reference data in bulk."""

    cnae_codes: set[str] = set()

    if "cnae" in df.columns:
        primary_cnaes = (
            df["cnae"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        cnae_codes.update(code for code in primary_cnaes if code)

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
        {"code": code, "name": None}
        for code in cnae_codes
        if code not in existing_codes
    ]

    if records:
        session.execute(insert(Cnae), records)


def _load_activity_areas(
    df: pd.DataFrame,
    session: Session,
) -> None:
    """Loads activity areas without manually assigning IDs."""

    existing_names = set(
        session.scalars(select(ActivityArea.name)).all()
    )

    records = [
        {"name": name}
        for name in AREA_COLUMNS.values()
        if name not in existing_names
    ]

    if records:
        session.execute(insert(ActivityArea), records)


def _load_activity_subareas(
    df: pd.DataFrame,
    session: Session,
) -> None:
    """Loads activity subareas with their parent areas."""

    areas = {
        area.name: area.id
        for area in session.scalars(select(ActivityArea)).all()
    }

    existing_subareas = set(
        session.execute(
            select(
                ActivitySubarea.area_id,
                ActivitySubarea.name,
            )
        ).all()
    )

    records = []

    for subarea_name, area_name in SUBAREA_COLUMNS.values():
        area_id = areas.get(area_name)

        if area_id is None:
            raise ValueError(f"Activity area not found: {area_name}")

        key = (area_id, subarea_name)

        if key in existing_subareas:
            continue

        records.append(
            {
                "area_id": area_id,
                "name": subarea_name,
            }
        )

        existing_subareas.add(key)

    if records:
        session.execute(insert(ActivitySubarea), records)


def _load_organizations(
    df: pd.DataFrame,
    session: Session,
) -> dict[str, int]:
    """Inserts organizations in batches and logs stage timings."""

    # Stage 1: Build organization records.
    stage_start = time.perf_counter()
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
                "registration_status": str(row.situacao_cadastral),
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

    records_elapsed = time.perf_counter() - stage_start

    logging.info(
        "Organization record construction: %d records in %.2f seconds",
        len(records),
        records_elapsed,
    )

    if not records:
        logging.info("Organizations: 0 records.")
        return {}

    # Stage 2: Insert organizations into PostgreSQL.
    stage_start = time.perf_counter()
    insert_batch_size = 1_000

    for start in range(0, len(records), insert_batch_size):
        batch = records[start:start + insert_batch_size]

        statement = pg_insert(Organization).values(batch)
        statement = statement.on_conflict_do_nothing(
            index_elements=["cnpj"]
        )

        session.execute(statement)

    insert_elapsed = time.perf_counter() - stage_start

    logging.info(
        "Organization insertion: %d records processed in %.2f seconds",
        len(records),
        insert_elapsed,
    )

    # Stage 3: Retrieve organization IDs by CNPJ.
    stage_start = time.perf_counter()

    cnpjs = [record["cnpj"] for record in records]
    organization_ids: dict[str, int] = {}
    lookup_batch_size = 10_000

    for start in range(0, len(cnpjs), lookup_batch_size):
        batch = cnpjs[start:start + lookup_batch_size]

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

    lookup_elapsed = time.perf_counter() - stage_start

    if len(organization_ids) != len(set(cnpjs)):
        missing_cnpjs = set(cnpjs) - set(organization_ids)

        raise ValueError(
            "Could not retrieve IDs for all organizations. "
            f"Missing IDs for {len(missing_cnpjs)} CNPJs."
        )

    logging.info(
        "Organization ID lookup: %d IDs retrieved in %.2f seconds",
        len(organization_ids),
        lookup_elapsed,
    )

    total_elapsed = (
        records_elapsed
        + insert_elapsed
        + lookup_elapsed
    )

    logging.info(
        "Organization loading breakdown: %.2f seconds total "
        "(construction: %.2f, insertion: %.2f, ID lookup: %.2f)",
        total_elapsed,
        records_elapsed,
        insert_elapsed,
        lookup_elapsed,
    )

    return organization_ids


def _insert_in_batches(
    session: Session,
    model: type,
    records: list[dict],
    conflict_columns: list[str],
    batch_size: int = 5_000,
) -> None:
    """Inserts relationship records in batches, ignoring conflicts."""

    if not records:
        logging.info(
            "%s: 0 records to insert.",
            model.__tablename__,
        )
        return

    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]

        statement = pg_insert(model).values(batch)
        statement = statement.on_conflict_do_nothing(
            index_elements=conflict_columns,
        )

        session.execute(statement)

    logging.info(
        "%s: %d records processed.",
        model.__tablename__,
        len(records),
    )


def _log_relationship_memory(
    relationship_name: str,
    records: list[dict],
) -> None:
    """Logs relationship count and estimated in-memory size."""

    records_memory_bytes = sys.getsizeof(records)

    records_memory_bytes += sum(
        sys.getsizeof(record)
        + sum(
            sys.getsizeof(key) + sys.getsizeof(value)
            for key, value in record.items()
        )
        for record in records
    )

    logging.info(
        "%s: %d records; estimated list memory: %.2f MB",
        relationship_name,
        len(records),
        records_memory_bytes / (1024 ** 2),
    )


def _load_organization_cnaes(
    df: pd.DataFrame,
    session: Session,
    organization_ids: dict[str, int],
) -> None:
    """Loads organization/CNAE relationships in bulk."""

    records = []

    for row in df.itertuples(index=False):
        organization_id = organization_ids.get(str(row.cnpj))

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
            for code in str(row.cnae_secundaria).split("|"):
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
        logging.info("Organization-CNAE relationships: 0 records.")
        return

    _log_relationship_memory(
        "Organization-CNAE relationships",
        records,
    )

    _insert_in_batches(
        session=session,
        model=OrganizationCnae,
        records=records,
        conflict_columns=[
            "organization_id",
            "cnae_code",
        ],
    )


def _load_organization_areas(
    df: pd.DataFrame,
    session: Session,
    organization_ids: dict[str, int],
) -> None:
    """Loads organization/activity-area relationships in bulk."""

    areas = {
        area.name: area.id
        for area in session.scalars(select(ActivityArea)).all()
    }

    records = []

    for row in df.itertuples(index=False):
        organization_id = organization_ids.get(str(row.cnpj))

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
        logging.info("Organization-area relationships: 0 records.")
        return

    _log_relationship_memory(
        "Organization-area relationships",
        records,
    )

    _insert_in_batches(
        session=session,
        model=OrganizationArea,
        records=records,
        conflict_columns=[
            "organization_id",
            "area_id",
        ],
    )


def _load_organization_subareas(
    df: pd.DataFrame,
    session: Session,
    organization_ids: dict[str, int],
) -> None:
    """Loads organization/activity-subarea relationships in bulk."""

    areas = {
        area.name: area.id
        for area in session.scalars(select(ActivityArea)).all()
    }

    subareas = {
        (subarea.area_id, subarea.name): subarea.id
        for subarea in session.scalars(
            select(ActivitySubarea)
        ).all()
    }

    records = []

    for row in df.itertuples(index=False):
        organization_id = organization_ids.get(str(row.cnpj))

        if organization_id is None:
            continue

        for column, (subarea_name, area_name) in SUBAREA_COLUMNS.items():
            value = getattr(row, column)

            if pd.isna(value) or value != 1:
                continue

            area_id = areas[area_name]
            subarea_id = subareas.get((area_id, subarea_name))

            if subarea_id is None:
                raise ValueError(
                    f"Activity subarea not found: '{subarea_name}' "
                    f"under parent area '{area_name}'."
                )

            records.append(
                {
                    "organization_id": organization_id,
                    "subarea_id": subarea_id,
                }
            )

    if not records:
        logging.info("Organization-subarea relationships: 0 records.")
        return

    _log_relationship_memory(
        "Organization-subarea relationships",
        records,
    )

    _insert_in_batches(
        session=session,
        model=OrganizationSubarea,
        records=records,
        conflict_columns=[
            "organization_id",
            "subarea_id",
        ],
    )
