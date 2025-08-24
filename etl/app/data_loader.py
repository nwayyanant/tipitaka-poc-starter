"""Data loader for ETL.


Provides functions to read CSV files (chunks and windows),
normalize their structure, and return clean pandas DataFrames.
"""
import pandas as pd
from typing import Tuple
import logging


import etl.config as config


logger = logging.getLogger(__name__)
logger.setLevel(config.LOG_LEVEL)




def load_chunks() -> pd.DataFrame:
"""Load the main chunk.csv file."""
logger.info(f"Loading chunks from {config.CSV_CHUNKS}")
df = pd.read_csv(config.CSV_CHUNKS)


if config.TEXT_COLUMN not in df.columns:
raise ValueError(f"Expected column '{config.TEXT_COLUMN}' in {config.CSV_CHUNKS}")


# Drop rows with missing text
df = df.dropna(subset=[config.TEXT_COLUMN])
df[config.TEXT_COLUMN] = df[config.TEXT_COLUMN].astype(str).str.strip()


logger.info(f"Loaded {len(df)} rows from chunk.csv")
return df




def load_windows() -> pd.DataFrame:
"""Load the windows.csv file."""
logger.info(f"Loading windows from {config.CSV_WINDOWS}")
df = pd.read_csv(config.CSV_WINDOWS)


if config.WINDOW_COLUMN not in df.columns:
raise ValueError(f"Expected column '{config.WINDOW_COLUMN}' in {config.CSV_WINDOWS}")


df = df.dropna(subset=[config.WINDOW_COLUMN])
df[config.WINDOW_COLUMN] = df[config.WINDOW_COLUMN].astype(str).str.strip()


logger.info(f"Loaded {len(df)} rows from windows.csv")
return df




def load_all() -> Tuple[pd.DataFrame, pd.DataFrame]:
"""Convenience function: load both chunks and windows."""
chunks = load_chunks()
windows = load_windows()
return chunks, windows




if __name__ == "__main__":
config.summary()
chunks, windows = load_all()
print(chunks.head())
print(windows.head())
