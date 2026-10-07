import pandas as pd

from etl.transform import clean, fix_mojibake


def test_clean_should_return_empty_dataframe_unchanged():
    df = pd.DataFrame()

    result = clean(df)

    assert result.empty


def test_fix_mojibake_should_correct_invalid_encoding():
    value = "SÃ£o Paulo"

    result = fix_mojibake(value)

    assert result == "São Paulo"


def test_fix_mojibake_should_keep_valid_text_unchanged():
    value = "São Paulo"

    result = fix_mojibake(value)

    assert result == "São Paulo"


def test_clean_should_remove_completely_empty_rows():
    df = pd.DataFrame(
        {
            "cnpj": ["01022772000197", None],
            "situacao_cadastral": ["Ativa", None],
        }
    )

    result = clean(df)

    assert len(result) == 1
    assert result.iloc[0]["cnpj"] == "01022772000197"


def test_clean_should_strip_text_columns():
    df = pd.DataFrame(
        {
            "tx_razao_social_osc": ["  Organização A  "],
            "tx_nome_fantasia_osc": ["  Org A  "],
            "tx_endereco_completo": ["  Rua A, 100  "],
        }
    )

    result = clean(df)

    assert result.loc[0, "tx_razao_social_osc"] == "Organização A"
    assert result.loc[0, "tx_nome_fantasia_osc"] == "Org A"
    assert result.loc[0, "tx_endereco_completo"] == "Rua A, 100"


def test_clean_should_transform_registration_status():
    df = pd.DataFrame(
        {
            "situacao_cadastral": [
                "Ativa",
                "Inapta",
                "Nula ou Baixada",
                "Suspensa",
            ]
        }
    )

    result = clean(df)

    assert result["situacao_cadastral"].tolist() == [
        "ACTIVE",
        "INAPT",
        "CLOSED_OR_NULL",
        "SUSPENDED",
    ]


def test_clean_should_transform_matrix_or_branch():
    df = pd.DataFrame(
        {
            "matriz_filial": [
                "Matriz",
                "Filial",
                "Não Identificado",
            ]
        }
    )

    result = clean(df)

    assert result["matriz_filial"].tolist() == [
        "HEADQUARTERS",
        "BRANCH",
        "UNKNOWN",
    ]


def test_clean_should_transform_removed_from_mosc():
    df = pd.DataFrame(
        {
            "removida_do_mosc": [
                "sim",
                "não",
            ]
        }
    )

    result = clean(df)

    assert result["removida_do_mosc"].tolist() == [
        True,
        False,
    ]


def test_clean_should_convert_dates():
    df = pd.DataFrame(
        {
            "dt_fundacao_osc": ["2020-01-15"],
            "data_fechamento": ["2024-05-20"],
        }
    )

    result = clean(df)

    assert result.loc[0, "dt_fundacao_osc"] == pd.Timestamp(
        "2020-01-15"
    ).date()

    assert result.loc[0, "data_fechamento"] == pd.Timestamp(
        "2024-05-20"
    ).date()


def test_clean_should_convert_invalid_dates_to_null():
    df = pd.DataFrame(
        {
            "dt_fundacao_osc": ["invalid-date"],
            "data_fechamento": ["invalid-date"],
        }
    )

    result = clean(df)

    assert pd.isna(result.loc[0, "dt_fundacao_osc"])
    assert pd.isna(result.loc[0, "data_fechamento"])


def test_clean_should_convert_municipality_code_zero_to_null():
    df = pd.DataFrame(
        {
            "cd_municipio": [0, 1100130],
        }
    )

    result = clean(df)

    assert pd.isna(result.loc[0, "cd_municipio"])
    assert result.loc[1, "cd_municipio"] == 1100130


def test_clean_should_normalize_uf():
    df = pd.DataFrame(
        {
            "UF_Sigla": [" sp ", "rj", " GO"],
        }
    )

    result = clean(df)

    assert result["UF_Sigla"].tolist() == [
        "SP",
        "RJ",
        "GO",
    ]


def test_clean_should_convert_invalid_latitude_to_null():
    df = pd.DataFrame(
        {
            "latitude": [
                -90,
                0,
                90,
                91,
                -91,
            ]
        }
    )

    result = clean(df)

    assert result["latitude"].tolist()[:3] == [
        -90,
        0,
        90,
    ]

    assert pd.isna(result.loc[3, "latitude"])
    assert pd.isna(result.loc[4, "latitude"])


def test_clean_should_convert_invalid_longitude_to_null():
    df = pd.DataFrame(
        {
            "longitude": [
                -180,
                0,
                180,
                181,
                -181,
            ]
        }
    )

    result = clean(df)

    assert result["longitude"].tolist()[:3] == [
        -180,
        0,
        180,
    ]

    assert pd.isna(result.loc[3, "longitude"])
    assert pd.isna(result.loc[4, "longitude"])


def test_clean_should_convert_primary_cnae_to_string():
    df = pd.DataFrame(
        {
            "cnae": [9493600, 1234567],
        }
    )

    result = clean(df)

    assert result["cnae"].tolist() == [
        "9493600",
        "1234567",
    ]


def test_clean_should_strip_secondary_cnaes():
    df = pd.DataFrame(
        {
            "cnae_secundaria": [
                " 1234567|7654321 "
            ]
        }
    )

    result = clean(df)

    assert result.loc[0, "cnae_secundaria"] == (
        "1234567|7654321"
    )
