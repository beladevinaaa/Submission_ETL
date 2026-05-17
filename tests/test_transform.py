import pytest
import pandas as pd
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../utils")))
from transform import transform_data # type: ignore

# ── helper ────────────────────────────────────────────────────────────

def make_df(n=3, **overrides):
    df = pd.DataFrame({
        "Title":     [f"Product {i}" for i in range(n)],
        "Price":     [f"${10 + i}.99" for i in range(n)],
        "Rating":    [f"Rating: ⭐ {3.5 + i * 0.1:.1f} / 5" for i in range(n)],
        "Colors":    [f"{i + 1} Colors" for i in range(n)],
        "Size":      ["Size: M"] * n,
        "Gender":    ["Gender: Men"] * n,
        "timestamp": ["2024-01-01 00:00:00"] * n,
    })
    for col, val in overrides.items():
        df[col] = val
    return df

# ── return type ───────────────────────────────────────────────────────

def test_returns_dataframe():
    assert isinstance(transform_data(make_df()), pd.DataFrame)

def test_index_reset():
    df = make_df(5)
    result = transform_data(df)
    assert list(result.index) == list(range(len(result)))

def test_empty_dataframe():
    df = pd.DataFrame(columns=["Title","Price","Rating","Colors","Size","Gender","timestamp"])
    assert isinstance(transform_data(df), pd.DataFrame)

# ── filtering ─────────────────────────────────────────────────────────

def test_removes_unknown_product():
    df = make_df(3, Title=["Unknown Product", "Shirt", "Pants"])
    assert "Unknown Product" not in transform_data(df)["Title"].values

def test_removes_invalid_rating():
    df = make_df(3, Rating=["Invalid Rating", "Rating: ⭐ 4.0 / 5", "Rating: ⭐ 3.5 / 5"])
    assert len(transform_data(df)) == 2

def test_removes_not_rated():
    df = make_df(3, Rating=["Not Rated", "Rating: ⭐ 4.0 / 5", "Rating: ⭐ 3.5 / 5"])
    assert len(transform_data(df)) == 2

def test_removes_price_unavailable():
    df = make_df(3, Price=["Price Unavailable", "$10.00", "$20.00"])
    assert len(transform_data(df)) == 2

def test_drops_null_rows():
    df = make_df(3)
    df.loc[1, "Title"] = None
    assert transform_data(df)["Title"].isnull().sum() == 0

def test_removes_duplicates():
    df = pd.concat([make_df(3), make_df(3)], ignore_index=True)
    assert len(transform_data(df)) == 3

# ── price ─────────────────────────────────────────────────────────────

def test_price_is_float():
    assert transform_data(make_df())["Price"].dtype == float

def test_price_converted_to_idr():
    df = make_df(1, Price=["$10.00"])
    assert transform_data(df)["Price"].iloc[0] == pytest.approx(10.00 * 16000)

def test_price_with_comma():
    df = make_df(1, Price=["$1,000.00"])
    assert transform_data(df)["Price"].iloc[0] == pytest.approx(1000.00 * 16000)

# ── rating ────────────────────────────────────────────────────────────

def test_rating_is_float():
    assert transform_data(make_df())["Rating"].dtype == float

def test_rating_extracted_correctly():
    df = make_df(1, Rating=["Rating: ⭐ 4.5 / 5"])
    assert transform_data(df)["Rating"].iloc[0] == pytest.approx(4.5)

# ── colors ────────────────────────────────────────────────────────────

def test_colors_is_int():
    assert transform_data(make_df())["Colors"].dtype in [int, "int64", "int32"]

def test_colors_extracted_correctly():
    df = make_df(1, Colors=["5 Colors"])
    assert transform_data(df)["Colors"].iloc[0] == 5

# ── size & gender ─────────────────────────────────────────────────────

def test_size_prefix_removed():
    df = make_df(1, Size=["Size: XL"])
    assert transform_data(df)["Size"].iloc[0] == "XL"

def test_gender_prefix_removed():
    df = make_df(1, Gender=["Gender: Women"])
    assert transform_data(df)["Gender"].iloc[0] == "Women"
