import pandas as pd
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

def from_csv(filepath: str) -> pd.DataFrame:
    """
    Lê um arquivo CSV e retorna um DataFrame do pandas.
    
    Args:
        filepath (str): Caminho para o arquivo CSV.

    Returns:
        pd.DataFrame: DataFrame com os dados carregados.
    """
    try:
        df = pd.read_csv(filepath, encoding='utf-8', delimiter=';', decimal=',')
        logging.info(f"CSV carregado com sucesso: {len(df)} registros")
        
        # Mostrar as primeiras linhas somente se o nível DEBUG estiver ativado
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug(f"Primeiras 5 linhas:\n{df.head(5).to_string()}")
    
        return df
    except Exception as e:
        logging.error(f"Erro ao ler o CSV: {e}")
        return pd.DataFrame()
