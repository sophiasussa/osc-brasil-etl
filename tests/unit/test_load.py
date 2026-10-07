from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from etl.load import (
    _load_legal_natures,
    _load_municipalities,
    _load_organizations,
    load_dataframe,
)


def test_load_legal_natures_should_add_new_legal_natures():
    df = pd.DataFrame(
        {
            "natureza_juridica": [
                3999,
                3220,
                3999,
            ]
        }
    )

    session = MagicMock()

    _load_legal_natures(df, session)

    session.execute.assert_called_once()

    records = session.execute.call_args.args[1]

    assert records == [
        {
            "code": 3999,
            "name": "Natureza jurídica 3999",
        },
        {
            "code": 3220,
            "name": "Natureza jurídica 3220",
        },
    ]


def test_load_legal_natures_should_ignore_null_values():
    df = pd.DataFrame(
        {
            "natureza_juridica": [
                3999,
                None,
                3220,
            ]
        }
    )

    session = MagicMock()

    _load_legal_natures(df, session)

    session.execute.assert_called_once()

    records = session.execute.call_args.args[1]

    assert records == [
        {
            "code": 3999,
            "name": "Natureza jurídica 3999",
        },
        {
            "code": 3220,
            "name": "Natureza jurídica 3220",
        },
    ]


def test_load_municipalities_should_add_new_municipalities():
    df = pd.DataFrame(
        {
            "cd_municipio": [
                3550308,
                3304557,
            ],
            "municipio_nome": [
                "SÃO PAULO",
                "RIO DE JANEIRO",
            ],
            "UF_Sigla": [
                "SP",
                "RJ",
            ],
        }
    )

    session = MagicMock()

    _load_municipalities(df, session)

    session.execute.assert_called_once()

    records = session.execute.call_args.args[1]

    assert records == [
        {
            "code": 3550308,
            "name": "SÃO PAULO",
            "uf": "SP",
        },
        {
            "code": 3304557,
            "name": "RIO DE JANEIRO",
            "uf": "RJ",
        },
    ]


def test_load_municipalities_should_not_add_duplicate_codes():
    df = pd.DataFrame(
        {
            "cd_municipio": [
                3550308,
                3550308,
            ],
            "municipio_nome": [
                "SÃO PAULO",
                "SÃO PAULO",
            ],
            "UF_Sigla": [
                "SP",
                "SP",
            ],
        }
    )

    session = MagicMock()

    _load_municipalities(df, session)

    session.execute.assert_called_once()

    records = session.execute.call_args.args[1]

    assert records == [
        {
            "code": 3550308,
            "name": "SÃO PAULO",
            "uf": "SP",
        }
    ]


def test_load_municipalities_should_ignore_null_codes():
    df = pd.DataFrame(
        {
            "cd_municipio": [
                3550308,
                None,
            ],
            "municipio_nome": [
                "SÃO PAULO",
                "SEM MUNICÍPIO",
            ],
            "UF_Sigla": [
                "SP",
                None,
            ],
        }
    )

    session = MagicMock()

    _load_municipalities(df, session)

    session.execute.assert_called_once()

    records = session.execute.call_args.args[1]

    assert records == [
        {
            "code": 3550308,
            "name": "SÃO PAULO",
            "uf": "SP",
        }
    ]


def test_load_organizations_should_add_organizations():
    df = pd.DataFrame(
        {
            "cnpj": [
                "01022772000197",
                "01527966000144",
            ],
            "tx_razao_social_osc": [
                "Organização A",
                "Organização B",
            ],
            "tx_nome_fantasia_osc": [
                "Org A",
                "Org B",
            ],
            "natureza_juridica": [
                3999,
                3220,
            ],
            "matriz_filial": [
                "HEADQUARTERS",
                "BRANCH",
            ],
            "situacao_cadastral": [
                "ACTIVE",
                "INAPT",
            ],
            "removida_do_mosc": [
                False,
                True,
            ],
            "dt_fundacao_osc": [
                pd.Timestamp("2000-01-01").date(),
                pd.Timestamp("2010-05-10").date(),
            ],
            "data_fechamento": [
                None,
                pd.Timestamp("2024-01-01").date(),
            ],
            "ano_fechamento": [
                None,
                2024,
            ],
            "tx_endereco_completo": [
                "Rua A, 100",
                "Rua B, 200",
            ],
            "cd_municipio": [
                3550308,
                3304557,
            ],
            "latitude": [
                -23.5505,
                -22.9068,
            ],
            "longitude": [
                -46.6333,
                -43.1729,
            ],
        }
    )

    session = MagicMock()

    session.execute.return_value.all.return_value = [
        ("01022772000197", 1),
        ("01527966000144", 2),
    ]

    organization_ids = _load_organizations(
        df,
        session,
    )

    # INSERT + SELECT
    assert session.execute.call_count == 2

    # A função deve retornar o mapa CNPJ -> ID
    assert organization_ids == {
        "01022772000197": 1,
        "01527966000144": 2,
    }

    # A primeira operação deve ser um INSERT
    insert_statement = session.execute.call_args_list[0].args[0]

    assert insert_statement.table.name == "organizations"

    # A segunda operação deve ser um SELECT
    select_statement = session.execute.call_args_list[1].args[0]

    assert select_statement is not None


def test_load_dataframe_should_commit():
    df = pd.DataFrame(
        {
            "cnpj": [
                "01022772000197",
            ]
        }
    )

    engine = MagicMock()
    session = MagicMock()

    with patch("etl.load.Session") as session_class:
        session_class.return_value.__enter__.return_value = session

        with patch("etl.load._load_legal_natures"), \
             patch("etl.load._load_municipalities"), \
             patch("etl.load._load_cnaes"), \
             patch("etl.load._load_activity_areas"), \
             patch("etl.load._load_activity_subareas"), \
             patch("etl.load._load_organizations"), \
             patch("etl.load._load_organization_cnaes"), \
             patch("etl.load._load_organization_areas"), \
             patch("etl.load._load_organization_subareas"):

            load_dataframe(df, engine)

    session.commit.assert_called_once()
    session.rollback.assert_not_called()


def test_load_dataframe_should_rollback_when_loading_fails():
    df = pd.DataFrame(
        {
            "cnpj": [
                "01022772000197",
            ]
        }
    )

    engine = MagicMock()
    session = MagicMock()

    with patch("etl.load.Session") as session_class:
        session_class.return_value.__enter__.return_value = session

        with patch(
            "etl.load._load_legal_natures",
            side_effect=Exception("Database error"),
        ):
            with pytest.raises(
                Exception,
                match="Database error",
            ):
                load_dataframe(df, engine)

    session.rollback.assert_called_once()
    session.commit.assert_not_called()
