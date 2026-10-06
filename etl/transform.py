import pandas as pd
import logging

# Configuração global de logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica transformações no DataFrame bruto:
    - Remove linhas vazias
    - Converte colunas numéricas e booleanas
    - Padroniza strings e datas
    - Valida coordenadas geográficas

    Args:
        df (pd.DataFrame): DataFrame bruto extraído

    Returns:
        pd.DataFrame: DataFrame limpo e padronizado
    """
    if df.empty:
        logging.warning("DataFrame recebido está vazio. Nada será transformado.")
        return df
    
    original = df.shape
    logging.info(f"Shape original do DataFrame: {original}")

    # Renomeação de colunas específicas
    renomeadas = {
        'tx_razao_social_osc': 'razao_social',
        'tx_nome_fantasia_osc': 'nome_fantasia',
        'tx_endereco_completo': 'endereco_completo',
        'cd_natureza_juridica_osc': 'codigo_natureza_juridica',
        'cd_uf': 'codigo_uf',
        'tx_latitude': 'latitude',
        'tx_longitude': 'longitude',
        'dt_fundacao_osc': 'dt_fundacao'
    }
    df.rename(columns=renomeadas, inplace=True)
    logging.info("Colunas específicas renomeadas.")

    # Padroniza todos os nomes de colunas: minúsculo e _ no lugar de espaços
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    logging.info("Nomes das colunas padronizados.")

    # Remove linhas totalmente vazias
    df.dropna(how='all', inplace=True)
    logging.info(f"Linhas totalmente vazias removidas: {original[0] - df.shape[0]}")
    
    # Converte colunas binárias para booleanos
    colunas_booleans = 0
    for col in df.columns:
        if df[col].dropna().isin([0, 1]).all():
            df[col] = df[col].astype(bool)
            colunas_booleans += 1
    logging.info(f"{colunas_booleans} colunas convertidas para booleano.")

    # Conversão de colunas para numérico, quando possível
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='ignore')
    logging.info("Conversão para numérico aplicada onde possível.")

    # Padronização de strings
    colunas_texto = df.select_dtypes(include='object').columns
    for col in colunas_texto:
        df[col] = df[col].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True).str.title()
    logging.info(f"{len(colunas_texto)} colunas de texto padronizadas com .title()")

    # Conversão de datas
    if 'dt_fundacao' in df.columns:
        df['dt_fundacao'] = pd.to_datetime(df['dt_fundacao'], errors='coerce', dayfirst=True)
        logging.info("Coluna 'dt_fundacao' convertida para datetime.")

    # Validação de coordenadas geográficas
    if 'latitude' in df.columns and 'longitude' in df.columns:
        antes = df.shape[0]
        df = df[df['latitude'].between(-90, 90, inclusive='both') &
                df['longitude'].between(-180, 180, inclusive='both')]
        logging.info(f"Coordenadas inválidas removidas: {antes - df.shape[0]} linhas")

    logging.info(f"Shape final do DataFrame: {df.shape}")
    logging.info("Transformações aplicadas com sucesso.")
    return df
