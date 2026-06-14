import pandas as pd


def fix_types(df_spotify: pd.DataFrame, df_competition: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fixes dirty types generically across datasets:
    - Iterates over all columns of type 'object' or 'string'.
    - Removes commas and coerces to numeric.
    - If >90% of the column becomes valid numeric, it applies the coercion.
    - Also explicitly forces 'track_id' to Int64 if it exists for JOINs.
    """
    df_s = df_spotify.copy()
    df_c = df_competition.copy()

    def _smart_coerce(df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            if df[col].dtype == "object" or pd.api.types.is_string_dtype(df[col]):
                # Try replacing commas and converting to numeric
                coerced = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce")
                # If >90% of the values are valid numbers (excluding original NaNs if possible, but simpler: just >90% of total)
                valid_ratio = coerced.notnull().mean()
                if valid_ratio > 0.90:
                    df[col] = coerced
        if "track_id" in df.columns:
            df["track_id"] = pd.to_numeric(df["track_id"], errors="coerce").astype("Int64")
        return df

    df_s = _smart_coerce(df_s)
    df_c = _smart_coerce(df_c)

    return df_s, df_c



def merge_tables(df_spotify: pd.DataFrame, df_competition: pd.DataFrame) -> pd.DataFrame:
    """Inner join on track_id. Assumes fix_types() has already been called."""
    return df_spotify.merge(df_competition, on="track_id", how="inner")


def load_and_fix(spotify_path: str, competition_path: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load both CSVs, fix types, and return (df_spotify, df_competition, df_merged)."""
    df_s = pd.read_csv(spotify_path)
    df_c = pd.read_csv(competition_path)
    df_s, df_c = fix_types(df_s, df_c)
    df_merged = merge_tables(df_s, df_c)
    return df_s, df_c, df_merged
