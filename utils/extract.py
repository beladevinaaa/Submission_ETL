import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime

BASE_URL = "https://fashion-studio.dicoding.dev/"

headers = {
    "User-Agent": "Mozilla/5.0"
}


def extract_data():

    all_products = []

    # Loop halaman 1 - 50
    for page in range(1, 51):

        # URL tiap halaman
        if page == 1:
            url = BASE_URL
        else:
            url = f"{BASE_URL}page{page}"

        print(f"Scraping halaman {page}")

        response = requests.get(url, headers=headers)

        # Cek request
        if response.status_code != 200:
            print(f"Gagal mengambil halaman {page}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        # Ambil semua product card
        products = soup.find_all("div", class_="collection-card")

        for product in products:

            # =========================
            # TITLE
            # =========================
            title = product.find("h3")
            title = title.text.strip() if title else "Unknown Product"

            # =========================
            # PRICE
            # =========================
            price = product.find("span", class_="price")
            price = price.text.strip() if price else "Price Unavailable"

            # =========================
            # INFO LAINNYA
            # =========================
            info = product.find_all("p")

            rating = "Invalid Rating"
            colors = "Unknown"
            size = "Unknown"
            gender = "Unknown"

            for item in info:

                text = item.text.strip()

                if "Rating" in text:
                    rating = text

                elif "Colors" in text:
                    colors = text

                elif "Size" in text:
                    size = text

                elif "Gender" in text:
                    gender = text

            # =========================
            # APPEND DATA
            # =========================
            all_products.append({
                "Title": title,
                "Price": price,
                "Rating": rating,
                "Colors": colors,
                "Size": size,
                "Gender": gender,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        # Delay biar aman
        time.sleep(1)

    # Convert ke dataframe
    df = pd.DataFrame(all_products)

    print(f"\nTotal data berhasil diambil: {len(df)}")

    return df


if __name__ == "__main__":

    data = extract_data()

    # Save raw data
    data.to_csv(
        "products.csv",
        index=False,
        encoding="utf-8-sig"
    )


    print("\nData berhasil disimpan ke products.csv")
