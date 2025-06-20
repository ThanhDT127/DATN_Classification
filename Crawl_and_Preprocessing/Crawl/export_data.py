import mysql.connector
import pandas as pd
import re  
from pathlib import Path

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "12345678",
    "database": "lazada_reviews_2"
}


def clean_text(text):
    if isinstance(text, str):
        return re.sub(r'[\x00-\x1F\x7F]', '', text)  
    return text

def export_sentiment_dataset():

    conn = mysql.connector.connect(**DB_CONFIG)

    df = pd.read_sql("SELECT review_text, rating FROM reviews", conn)

    final_df = df[["review_text"]]


    final_df["review_text"] = final_df["review_text"].apply(clean_text)

    excel_filename = "D:/ktlt/python/thuchanh/AI/Crawl_html/data_crawl/lazada_reviews_2_full.xlsx"


    final_df.to_excel(excel_filename, index=False)
    print(f"Đã lưu dataset vào file Excel: {excel_filename}")


    conn.close()


if __name__ == "__main__":
    export_sentiment_dataset()
