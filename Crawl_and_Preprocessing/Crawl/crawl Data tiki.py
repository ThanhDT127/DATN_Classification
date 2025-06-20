import requests
import mysql.connector
import time
import random
import json
from datetime import datetime
from bs4 import BeautifulSoup


DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "12345678",
    "database": "tiki_reviews_2"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def connect_db():
    return mysql.connector.connect(**DB_CONFIG)

def save_to_db(data):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        sql = """
        INSERT INTO reviews (category, product_name, product_id, product_link, review_text, rating, reviewer_name, review_time, product_info) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(sql, (
            data["category"],
            data["product_name"],
            data["product_id"],
            data["product_link"],
            data["review_text"],
            data["rating"],
            data["reviewer_name"],
            data["review_time"],
            json.dumps(data["product_info"])
        ))

        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Lỗi MySQL: {err}")



def convert_timestamp(timestamp):
    try:
        return datetime.utcfromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return None


def get_products_from_category(category_id):
    url = f"https://tiki.vn/api/personalish/v1/blocks/listings?category={category_id}&page=1&limit=20"

    session = requests.Session()
    response = session.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"Lỗi khi gọi API Tiki: {response.status_code}")
        return []

    try:
        data = response.json()
    except json.JSONDecodeError:
        print("Lỗi giải mã JSON")
        return []

    products = data.get("data", [])

    product_list = []
    for product in products:
        product_info = {
            "product_id": product["id"],
            "product_name": product["name"],
            "product_link": f"https://tiki.vn/p/{product['id']}.html",
            "category": product.get("categories", [{}])[0].get("name", "Unknown"),
            "product_info": product  # Lưu toàn bộ thông tin sản phẩm
        }
        product_list.append(product_info)

    return product_list



def get_reviews(product):
    session = requests.Session()
    page = 1

    while True:
        url = f"https://tiki.vn/api/v2/reviews?product_id={product['product_id']}&page={page}"
        response = session.get(url, headers=HEADERS)

        if response.status_code != 200:
            print(f"Lỗi lấy dữ liệu: {response.status_code}")
            return

        try:
            data = response.json()
        except json.JSONDecodeError:
            print("Lỗi giải mã JSON")
            return

        reviews = data.get("data", [])
        if not reviews:
            break  # Hết đánh giá

        for review in reviews:
            review_time = convert_timestamp(review.get("created_at", 0))  # Chuyển đổi timestamp

            review_data = {
                "category": product["category"],
                "product_name": product["product_name"],
                "product_id": product["product_id"],
                "product_link": product["product_link"],
                "review_text": review.get("content", "").strip(),
                "rating": review.get("rating", 0),
                "reviewer_name": review.get("created_by", {}).get("full_name", "Unknown"),
                "review_time": review_time,  # Giá trị đã được chuyển đổi
                "product_info": product["product_info"]
            }
            save_to_db(review_data)

        page += 1
        time.sleep(random.uniform(1, 3))  # Tránh bị Tiki chặn


# Chạy chương trình chính
def main():
    # categories = {
    #     "Điện thoại - Máy tính bảng": 1789,
    #     "Laptop": 1846
    # }
    categories = {
        # "Nhà Sách Tiki": 8322,
        # "Nhà Cửa - Đời Sống": 1883,
        # "Điện Thoại - Máy Tính Bảng": 1789,
        # "Đồ Chơi - Mẹ & Bé": 2549,
        # "Thiết Bị Số - Phụ Kiện Số": 1815,
        # "Điện Gia Dụng": 1882,
        # "Làm Đẹp - Sức Khỏe": 1520,
        "Ô Tô - Xe Máy - Xe Đạp": 8594,
        "Thời trang nữ": 931,
        "Bách Hóa Online": 4384,
        "Thể Thao - Dã Ngoại": 1975,
        "Thời trang nam": 915,
        "Cross Border - Hàng Quốc Tế": 17166,
        "Laptop - Máy Vi Tính - Linh kiện": 1846,
        "Giày - Dép nam": 1686,
        "Điện Tử - Điện Lạnh": 4221,
        "Giày - Dép nữ": 1703,
        "Máy Ảnh - Máy Quay Phim": 1801,
        "Phụ kiện thời trang": 27498,
        "NGON": 44792,
        "Đồng hồ và Trang sức": 8371,
        "Balo và Vali": 6000,
        "Voucher - Dịch vụ": 11312,
        "Túi thời trang nữ": 976,
        "Túi thời trang nam": 27616
    }

    for category_name, category_id in categories.items():
        print(f"Đang lấy sản phẩm từ danh mục: {category_name}")
        products = get_products_from_category(category_id)

        for product in products:
            print(f"Đang lấy đánh giá cho sản phẩm: {product['product_name']}")
            get_reviews(product)
            time.sleep(random.uniform(2, 5))  # Hạn chế bị chặn


if __name__ == "__main__":
    main()
