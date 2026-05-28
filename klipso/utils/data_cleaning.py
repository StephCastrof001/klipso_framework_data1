import pandas as pd


def fix_types(df_spotify: pd.DataFrame, df_competition: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fixes dirty types detected in the raw CSVs:
    - streams: object with commas → int
    - in_deezer_playlists, in_shazam_charts: object → int
    - track_id: normalized to Int64 in both tables for JOIN
    """
    df_s = df_spotify.copy()
    df_c = df_competition.copy()

    df_s["streams"] = pd.to_numeric(
        df_s["streams"].astype(str).str.replace(",", ""), errors="coerce"
    )
    df_c["in_deezer_playlists"] = pd.to_numeric(df_c["in_deezer_playlists"], errors="coerce")
    df_c["in_shazam_charts"] = pd.to_numeric(df_c["in_shazam_charts"], errors="coerce")
    df_c["track_id"] = pd.to_numeric(df_c["track_id"], errors="coerce").astype("Int64")
    df_s["track_id"] = df_s["track_id"].astype("Int64")

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
