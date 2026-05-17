import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../utils")))
import load # type: ignore

# ── helper ────────────────────────────────────────────────────────────

def make_df():
    return pd.DataFrame({
        "Title":     ["Shirt A", "Pants B"],
        "Price":     [160000.0, 480000.0],
        "Rating":    [4.5, 3.8],
        "Colors":    [3, 2],
        "Size":      ["M", "L"],
        "Gender":    ["Men", "Women"],
        "timestamp": ["2024-01-01 00:00:00"] * 2,
    })

# ── save_to_csv ───────────────────────────────────────────────────────

def test_csv_file_created(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("builtins.print"):
        load.save_to_csv(make_df())
    assert (tmp_path / "products_clean.csv").exists()

def test_csv_correct_data(tmp_path, monkeypatch):
    df = make_df()
    monkeypatch.chdir(tmp_path)
    with patch("builtins.print"):
        load.save_to_csv(df)
    loaded = pd.read_csv(tmp_path / "products_clean.csv")
    assert list(loaded.columns) == list(df.columns)
    assert len(loaded) == len(df)

def test_csv_no_index_column(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("builtins.print"):
        load.save_to_csv(make_df())
    assert "Unnamed: 0" not in pd.read_csv(tmp_path / "products_clean.csv").columns

def test_csv_prints_success(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    load.save_to_csv(make_df())
    assert "Berhasil" in capsys.readouterr().out

def test_csv_exception_handled(capsys):
    df = make_df()
    with patch.object(df, "to_csv", side_effect=Exception("disk full")):
        load.save_to_csv(df)
    assert "Gagal" in capsys.readouterr().out

# ── save_to_google_sheets ─────────────────────────────────────────────

@pytest.fixture
def mock_gsheets():
    with patch("load.ServiceAccountCredentials") as mock_creds, \
         patch("load.gspread") as mock_gs:
        mock_creds.from_json_keyfile_name.return_value = MagicMock()
        mock_client = MagicMock()
        mock_gs.authorize.return_value = mock_client
        mock_sheet = MagicMock()
        mock_client.open.return_value.sheet1 = mock_sheet
        yield mock_client, mock_sheet

def test_gsheets_opens_correct_spreadsheet(mock_gsheets):
    mock_client, _ = mock_gsheets
    with patch("builtins.print"):
        load.save_to_google_sheets(make_df())
    mock_client.open.assert_called_once_with("Submission ETL")

def test_gsheets_clears_then_updates(mock_gsheets):
    _, mock_sheet = mock_gsheets
    with patch("builtins.print"):
        load.save_to_google_sheets(make_df())
    mock_sheet.clear.assert_called_once()
    mock_sheet.update.assert_called_once()

def test_gsheets_update_includes_header(mock_gsheets):
    _, mock_sheet = mock_gsheets
    df = make_df()
    with patch("builtins.print"):
        load.save_to_google_sheets(df)
    assert mock_sheet.update.call_args[0][0][0] == df.columns.values.tolist()

def test_gsheets_prints_success(mock_gsheets, capsys):
    load.save_to_google_sheets(make_df())
    assert "Berhasil" in capsys.readouterr().out

def test_gsheets_exception_handled(capsys):
    with patch("load.ServiceAccountCredentials") as mc:
        mc.from_json_keyfile_name.side_effect = Exception("auth error")
        load.save_to_google_sheets(make_df())
    assert "Gagal" in capsys.readouterr().out

# ── save_to_postgresql ────────────────────────────────────────────────

@pytest.fixture
def mock_engine():
    with patch("load.create_engine", return_value=MagicMock()) as m:
        yield m

def test_pg_calls_create_engine(mock_engine):
    with patch.object(make_df(), "to_sql"), patch("builtins.print"):
        load.save_to_postgresql(make_df())
    mock_engine.assert_called_once()

def test_pg_engine_url(mock_engine):
    with patch("builtins.print"):
        load.save_to_postgresql(make_df())
    url = mock_engine.call_args[0][0]
    assert "localhost" in url and "submission_etl" in url and "psycopg2" in url

def test_pg_to_sql_args(mock_engine):
    df = make_df()
    with patch.object(df, "to_sql") as mock_sql, patch("builtins.print"):
        load.save_to_postgresql(df)
    _, kw = mock_sql.call_args
    assert kw.get("if_exists") == "replace"
    assert kw.get("index") is False

def test_pg_prints_success(mock_engine, capsys):
    load.save_to_postgresql(make_df())
    assert "Berhasil" in capsys.readouterr().out

def test_pg_exception_handled(capsys):
    with patch("load.create_engine", side_effect=Exception("conn refused")):
        load.save_to_postgresql(make_df())
    assert "Gagal" in capsys.readouterr().out
