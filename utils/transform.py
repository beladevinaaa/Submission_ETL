import pandas as pd

def transform_data(df):

    # =========================
    # HAPUS INVALID DATA
    # =========================

    dirty_patterns = {
        "Title": ["Unknown Product"],
        "Rating": ["Invalid Rating", "Not Rated"],
        "Price": ["Price Unavailable"]
    }

    # Filter Title
    df = df[~df["Title"].isin(dirty_patterns["Title"])]

    # Filter Rating
    for pattern in dirty_patterns["Rating"]:
        df = df[~df["Rating"].str.contains(pattern, na=False)]

    # Filter Price
    df = df[~df["Price"].isin(dirty_patterns["Price"])]

    # Hapus null
    df = df.dropna()

    # =========================
    # CLEAN PRICE
    # =========================

    # Hapus $
    df["Price"] = df["Price"].replace(r"[\$,]", "", regex=True)

    # Convert ke float
    df["Price"] = df["Price"].astype(float)

    # USD -> IDR
    df["Price"] = df["Price"] * 16000

    # =========================
    # CLEAN RATING
    # =========================

    # Ambil angka rating
    df["Rating"] = df["Rating"].str.extract(r"(\d+\.\d+)")

    # Convert float
    df["Rating"] = df["Rating"].astype(float)

    # =========================
    # CLEAN COLORS
    # =========================

    # Ambil angka saja
    df["Colors"] = df["Colors"].str.extract(r"(\d+)")

    # Convert integer
    df["Colors"] = df["Colors"].astype(int)

    # =========================
    # CLEAN SIZE
    # =========================

    df["Size"] = (
        df["Size"]
        .str.replace("Size:", "", regex=False)
        .str.strip()
    )

    # =========================
    # CLEAN GENDER
    # =========================

    df["Gender"] = (
        df["Gender"]
        .str.replace("Gender:", "", regex=False)
        .str.strip()
    )

    # =========================
    # HAPUS DUPLIKAT
    # =========================

    df = df.drop_duplicates()

    # Reset index
    df = df.reset_index(drop=True)

    return df
