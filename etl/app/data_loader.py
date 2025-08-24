import pandas as pd

def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def prepare_chunks(path: str):
    df = load_csv(path)
    df = df.dropna(subset=["pali_text"])  # Example cleaning
    return df
