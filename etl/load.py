import pandas as pd
from sqlalchemy import create_engine
import logging

def to_csv(df: pd.DataFrame, output_path: str):
    """
    Exporta um DataFrame para um arquivo CSV.

    Parâmetros:
        df (pd.DataFrame): DataFrame a ser exportado.
        output_path (str): Caminho do arquivo de destino (.csv).

    Logs:
        - Info: Confirmação de exportação bem-sucedida.
        - Error: Mensagem em caso de falha.
    """
    try:
        df.to_csv(output_path, index=False)
        logging.info(f"Dados exportados com sucesso para: {output_path}")
    except Exception as e:
        logging.error(f"Erro ao exportar CSV: {e}")

def to_sqlite(df: pd.DataFrame, db_path: str, table_name: str):
    """
    Exporta um DataFrame para uma tabela em banco de dados SQLite.

    Parâmetros:
        df (pd.DataFrame): DataFrame a ser salvo.
        db_path (str): Caminho do arquivo do banco SQLite (.db).
        table_name (str): Nome da tabela que será criada ou substituída.

    Logs:
        - Info: Confirmação de inserção bem-sucedida.
        - Error: Mensagem em caso de falha.
    """
    try:
        engine = create_engine(f'sqlite:///{db_path}')
        df.to_sql(table_name, con=engine, if_exists='replace', index=False)
        logging.info(f"Tabela '{table_name}' salva com sucesso em {db_path}")
    except Exception as e:
        logging.error(f"Erro ao salvar no banco SQLite: {e}")

def to_postgresql(df: pd.DataFrame, db_url: str, table_name: str):
    """
    Exporta um DataFrame para uma tabela em banco de dados PostgreSQL.

    Parâmetros:
        df (pd.DataFrame): DataFrame a ser salvo.
        db_url (str): URL de conexão com o banco (ex: 'postgresql://user:password@host:port/dbname').
        table_name (str): Nome da tabela que será criada ou substituída.

    Logs:
        - Info: Confirmação de inserção bem-sucedida.
        - Error: Mensagem em caso de falha.
    """
    try:
        engine = create_engine(db_url)
        df.to_sql(table_name, con=engine, if_exists='replace', index=False, chunksize=50)
        logging.info(f"Tabela '{table_name}' salva com sucesso no PostgreSQL")
    except Exception as e:
        logging.error(f"Erro ao salvar no PostgreSQL: {e}")
