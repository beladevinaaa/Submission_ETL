import gspread

from sqlalchemy import create_engine
from oauth2client.service_account import ServiceAccountCredentials


# ====================================
# SAVE CSV
# ====================================

def save_to_csv(df):

    try:

        df.to_csv(
            "products_clean.csv",
            index=False,
            encoding="utf-8-sig"
        )

        print("Berhasil simpan CSV")

    except Exception as e:
        print(f"Gagal simpan CSV: {e}")


# ====================================
# SAVE GOOGLE SHEETS
# ====================================

def save_to_google_sheets(df):

    try:

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "google-sheets-api.json",
            scope
        )

        client = gspread.authorize(creds)

        spreadsheet = client.open("Submission ETL")

        worksheet = spreadsheet.sheet1

        worksheet.clear()

        worksheet.update(
            [df.columns.values.tolist()] +
            df.values.tolist()
        )

        print("Berhasil upload Google Sheets")

    except Exception as e:
        print(f"Gagal upload Google Sheets: {e}")


# ====================================
# SAVE POSTGRESQL
# ====================================

def save_to_postgresql(df):

    try:

        username = "postgres"
        password = "admin123"
        host = "localhost"
        port = "5432"
        database = "submission_etl"

        engine = create_engine(
            f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
        )

        df.to_sql(
            "products",
            engine,
            if_exists="replace",
            index=False
        )

        print("Berhasil simpan PostgreSQL")

    except Exception as e:
        print(f"Gagal simpan PostgreSQL: {e}")
