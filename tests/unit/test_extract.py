import pytest
import pandas as pd

from etl.extract import from_csv


def test_from_csv_should_load_csv_successfully(tmp_path):
    csv_file = tmp_path / "test.csv"

    csv_file.write_text(
        "id;cnpj;tx_razao_social_osc\n"
        "1;01022772000197;Organização A\n"
        "2;01527966000144;Organização B\n",
        encoding="latin1",
    )

    result = from_csv(csv_file)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert list(result.columns) == [
        "id",
        "cnpj",
        "tx_razao_social_osc",
    ]


def test_from_csv_should_load_cnpj_as_string(tmp_path):
    csv_file = tmp_path / "test.csv"

    csv_file.write_text(
        "cnpj\n"
        "01022772000197\n",
        encoding="latin1",
    )

    result = from_csv(csv_file)

    assert isinstance(result["cnpj"].dtype, pd.StringDtype)
    assert result.loc[0, "cnpj"] == "01022772000197"


def test_from_csv_should_read_latin1_characters(tmp_path):
    csv_file = tmp_path / "test.csv"

    csv_file.write_text(
        "nome\n"
        "São Paulo\n"
        "Associação\n",
        encoding="latin1",
    )

    result = from_csv(csv_file)

    assert result.loc[0, "nome"] == "São Paulo"
    assert result.loc[1, "nome"] == "Associação"


def test_from_csv_should_raise_error_when_file_does_not_exist(tmp_path):
    csv_file = tmp_path / "does_not_exist.csv"

    with pytest.raises(FileNotFoundError):
        from_csv(csv_file)
