import time
import random
import pymysql
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
]


def init_driver():
    user_agent = random.choice(user_agents)
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument(f"user-agent={user_agent}")

    driver = webdriver.Chrome(options=options)
    return driver


def connect_mysql():
    return pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="12345678",
        database="lazada_reviews_2",
        charset="utf8mb4"
    )


def save_to_mysql(data):
    conn = connect_mysql()
    cursor = conn.cursor()
    sql = """INSERT INTO reviews (category, product_name, rating, reviewer, review_text, link) 
             VALUES (%s, %s, %s, %s, %s, %s)"""

    cursor.executemany(sql, data)
    conn.commit()
    cursor.close()
    conn.close()



def handle_captcha(driver):
    time.sleep(1)
    try:
        captcha_close_btn = driver.find_element("xpath","/html/body/div[9]/div[2]/div")
        driver.execute_script("arguments[0].scrollIntoView();", captcha_close_btn)
        captcha_close_btn.click()
        print("🔓 CAPTCHA đã đóng!")
    except:
        pass


def get_product_links(driver, category_url):
    driver.get(category_url)
    time.sleep(15)
    handle_captcha(driver)

    titles = []
    links = []

    while len(titles) < 80:
        elems = driver.find_elements(By.CSS_SELECTOR, ".RfADt [href]")
        for elem in elems:
            title = elem.text.strip()
            link = elem.get_attribute("href").strip()
            if (title, link) not in zip(titles, links):
                titles.append(title)
                links.append(link)
            if len(titles) >= 80:
                break

        if len(titles) >= 80:
            break

        try:
            next_button = driver.find_element(
                By.XPATH, "//button[contains(@class, 'ant-pagination-item-link')]//span[@aria-label='right']/.."
            )
            if next_button.is_enabled():
                next_button.click()
                time.sleep(5)
                handle_captcha(driver)
            else:
                print("Nút pagination không khả dụng, dừng lấy sản phẩm.")
                break
        except Exception as e:
            print("Không tìm thấy nút pagination hoặc có lỗi:", e)
            break

    print(f"🔍 Tìm thấy {len(titles)} sản phẩm trong danh mục!")
    return list(zip(titles, links))


def apply_rating_filter(driver, star):

    try:
        time.sleep(1)
        filter_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".oper .condition"))
        )

        # driver.execute_script("arguments[0].scrollIntoView();", filter_button)
        # time.sleep(1)

        actions = ActionChains(driver)
        actions.move_to_element(filter_button).click().perform()


        filter_menu = driver.find_element(By.CSS_SELECTOR, ".next-menu-content")
        filter_options = filter_menu.find_elements(By.CLASS_NAME, "next-menu-item")

        filter_options[6 - star].click()
        time.sleep(2)
        return True
    except (NoSuchElementException, IndexError):
        return False
    except:
        pass




def scrape_product_reviews(driver, product_name, product_link, category_name):
    driver.get(product_link)
    time.sleep(4)
    handle_captcha(driver)

    for i in range(1, 5):
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
        time.sleep(1)
    handle_captcha(driver)

    all_comments = []

    for star in range(1, 6):
        if not apply_rating_filter(driver, star):
            continue
        handle_captcha(driver)
        time.sleep(2)
        comment_count = 0

        max_count = 50 if star in [4, 5] else 100

        while comment_count < max_count:
            try:
                users = driver.find_elements(By.CSS_SELECTOR, ".middle")
                comments = driver.find_elements(By.CSS_SELECTOR, ".content")

                if not users or not comments:
                    break

                for user, comment in zip(users, comments):
                    all_comments.append(
                        (category_name, product_name, star, user.text, comment.text, product_link)
                    )
                    comment_count += 1
                    if comment_count >= max_count:
                        break

                next_buttons = driver.find_elements(By.CSS_SELECTOR, ".next-pagination-item.next")
                if next_buttons and next_buttons[0].is_enabled() and comment_count < max_count:
                    next_buttons[0].click()
                    time.sleep(5)
                    handle_captcha(driver)
                else:
                    break
            except (NoSuchElementException, ElementClickInterceptedException):
                break
    print(all_comments)
    return all_comments


if __name__ == "__main__":
    categories = {
        "Thuốc": "https://www.lazada.vn/catalog/?q=Thu%E1%BB%91c&rating=1&page=2",
        "Công Nghệ": "https://www.lazada.vn/catalog/?q=C%C3%B4ng%20Ngh%E1%BB%87&rating=1&page=2",
        "Nội thất": "https://www.lazada.vn/catalog/?q=N%E1%BB%99i%20th%E1%BA%A5t&rating=1&page=2",
        "Dã Ngoại": "https://www.lazada.vn/tag/da-ngoai/?catalog_redirect_tag=true&q=d%C3%A3%20ngo%E1%BA%A1i&rating=1&page=2",
        "Gia dụng": "https://www.lazada.vn/tag/gia-d%E1%BB%A5ng/?catalog_redirect_tag=true&q=gia%20d%E1%BB%A5ng&rating=1&page=2",
        "Mẹ và bé": "https://www.lazada.vn/tag/%C4%91%E1%BB%93-ch%C6%A1i/?catalog_redirect_tag=true&q=%C4%91%E1%BB%93%20ch%C6%A1i&rating=1&page=2",
        "Mạch linh kiện": "https://www.lazada.vn/mach-dien-linh-kien/?from=hp_categories&params={%22catIdLv1%22:%2212646%22,%22pvid%22:%22ab4e6696-88fd-42c1-b148-ca2388dfe457%22,%22src%22:%22ald%22,%22categoryName%22:%22M%E1%BA%A1ch+%C4%91i%E1%BB%87n++Linh+ki%E1%BB%87n%22,%22categoryId%22:%2212909%22}&q=m%E1%BA%A1ch+%C4%91i%E1%BB%87n++linh+ki%E1%BB%87n&rating=1&page=2",
        "Quần Jeans": "https://www.lazada.vn/quan-jeans/?up_id=1715183269&clickTrackInfo=matchType--20___description--Gi%25E1%25BA%25A3m%2B53%2525___seedItemMatchType--c2i___bucket--0___spm_id--category.hp___seedItemScore--0.0___abId--333258___score--0.095610976___pvid--6d83403d-6887-4991-9606-9c6c2913c184___refer--___appId--7253___seedItemId--1715183269___scm--1007.17253.333258.0___categoryId--6414___timestamp--1741489213143&from=hp_categories&item_id=1715183269&version=v2&q=qu%E1%BA%A7n%2Bjeans&params=%7B%22catIdLv1%22%3A%2262541004%22%2C%22pvid%22%3A%226d83403d-6887-4991-9606-9c6c2913c184%22%2C%22src%22%3A%22ald%22%2C%22categoryName%22%3A%22Qu%25E1%25BA%25A7n%2Bjeans%22%2C%22categoryId%22%3A%226414%22%7D&src=hp_categories&spm=a2o4n.homepage.categoriesPC.d_11_6414&page=2",
        "Loa Bluetooth": "https://www.lazada.vn/loa-khong-day-loa-bluetooth/?from=hp_categories&params={%22catIdLv1%22:%2210100387%22,%22pvid%22:%22f1be9b84-6797-4e8c-81b7-540d5f52d29e%22,%22src%22:%22ald%22,%22categoryName%22:%22Loa+kh%C3%B4ng+d%C3%A2y++loa+Bluetooth%22,%22categoryId%22:%2210100399%22}&q=loa+kh%C3%B4ng+d%C3%A2y++loa+bluetooth&rating=1&page=2",
        "Cáp Sạc": "https://www.lazada.vn/cap-dien-thoai/?from=hp_categories&params={%22catIdLv1%22:%2242062201%22,%22pvid%22:%22f1be9b84-6797-4e8c-81b7-540d5f52d29e%22,%22src%22:%22ald%22,%22categoryName%22:%22C%C3%A1p++Dock+s%E1%BA%A1c%22,%22categoryId%22:%2211029%22}&q=c%C3%A1p++dock+s%E1%BA%A1c&rating=1&page=2",
        "phụ kiện thơm phòng": "https://www.lazada.vn/do-dung-lam-thom-phong/?from=hp_categories&params={%22catIdLv1%22:%2210100083%22,%22pvid%22:%225ed9cf67-00df-4e26-a184-4b50179e34c3%22,%22src%22:%22ald%22,%22categoryName%22:%22Ph%E1%BB%A5+ki%E1%BB%87n+l%C3%A0m+th%C6%A1m+ph%C3%B2ng%22,%22categoryId%22:%2212745%22}&q=ph%E1%BB%A5+ki%E1%BB%87n+l%C3%A0m+th%C6%A1m+ph%C3%B2ng&rating=1&page=2",
        "Tai Nghe Không Dây": "https://www.lazada.vn/tai-nghe-nhet-tai-khong-day/?from=hp_categories&params={%22catIdLv1%22:%2210100387%22,%22pvid%22:%22f1be9b84-6797-4e8c-81b7-540d5f52d29e%22,%22src%22:%22ald%22,%22categoryName%22:%22Tai+nghe+nh%C3%A9t+tai+kh%C3%B4ng+d%C3%A2y%22,%22categoryId%22:%2211412%22}&q=tai+nghe+nh%C3%A9t+tai+kh%C3%B4ng+d%C3%A2y&rating=1&page=2",
        "Đồng Hồ Thông minh": "https://www.lazada.vn/dong-ho-thong-minh/?from=hp_categories&params={%22catIdLv1%22:%2210100412%22,%22pvid%22:%22f1be9b84-6797-4e8c-81b7-540d5f52d29e%22,%22src%22:%22ald%22,%22categoryName%22:%22%C4%90%E1%BB%93ng+h%E1%BB%93+th%C3%B4ng+minh%22,%22categoryId%22:%2210100415%22}&q=%C4%90%E1%BB%93ng+h%E1%BB%93+th%C3%B4ng+minh&rating=1&page=2",
        "Microphone": "https://www.lazada.vn/micro-phones/?from=hp_categories&params={%22catIdLv1%22:%2210100387%22,%22pvid%22:%22f1be9b84-6797-4e8c-81b7-540d5f52d29e%22,%22src%22:%22ald%22,%22categoryName%22:%22Micro%22,%22categoryId%22:%223398%22}&q=micro&rating=1&page=2",
        "Điện thoại": "https://www.lazada.vn/dien-thoai-di-dong/?from=hp_categories&params={%22catIdLv1%22:%224402%22,%22pvid%22:%225ed9cf67-00df-4e26-a184-4b50179e34c3%22,%22src%22:%22ald%22,%22categoryName%22:%22%C4%90i%E1%BB%87n+tho%E1%BA%A1i+di+%C4%91%E1%BB%99ng%22,%22categoryId%22:%224518%22}&q=%C4%91i%E1%BB%87n+tho%E1%BA%A1i+di+%C4%91%E1%BB%99ng&rating=1&page=2",
        "Áo Thun": "https://www.lazada.vn/ao-thun-cho-nam/?from=hp_categories&params={%22catIdLv1%22:%2262541004%22,%22pvid%22:%22f1be9b84-6797-4e8c-81b7-540d5f52d29e%22,%22src%22:%22ald%22,%22categoryName%22:%22%C3%81o+thun+nam%22,%22categoryId%22:%227930%22}&q=%C3%A1o+thun+nam&rating=1&page=2",
        "Camera": "https://www.lazada.vn/camera-ip-ket-noi-internet/?from=hp_categories&params={%22catIdLv1%22:%224404%22,%22pvid%22:%22f1be9b84-6797-4e8c-81b7-540d5f52d29e%22,%22src%22:%22ald%22,%22categoryName%22:%22Camera+IP+k%E1%BA%BFt+n%E1%BB%91i+Internet%22,%22categoryId%22:%2215212%22}&q=camera+ip+k%E1%BA%BFt+n%E1%BB%91i+internet&rating=1&page=2",
        "Đèn Trang Trí": "https://www.lazada.vn/den-trang-tri-chuyen-dung/?from=hp_categories&params={%22catIdLv1%22:%2210100083%22,%22pvid%22:%22f1be9b84-6797-4e8c-81b7-540d5f52d29e%22,%22src%22:%22ald%22,%22categoryName%22:%22%C4%90%C3%A8n+trang+tr%C3%AD%22,%22categoryId%22:%2213113%22}&q=%C4%91%C3%A8n+trang+tr%C3%AD&rating=1&page=2",
        "Mỹ Phẩm": "https://www.lazada.vn/duong-da-va-serum/?from=hp_categories&params={%22catIdLv1%22:%224405%22,%22pvid%22:%22f1be9b84-6797-4e8c-81b7-540d5f52d29e%22,%22src%22:%22ald%22,%22categoryName%22:%22D%C6%B0%E1%BB%A1ng+da++Serum%22,%22categoryId%22:%222283%22}&q=d%C6%B0%E1%BB%A1ng+da++serum&rating=1&page=2",
        "Phụ Kiện Phòng": "https://www.lazada.vn/do-dung-lam-thom-phong/?from=hp_categories&params={%22catIdLv1%22:%2210100083%22,%22pvid%22:%22f1be9b84-6797-4e8c-81b7-540d5f52d29e%22,%22src%22:%22ald%22,%22categoryName%22:%22Ph%E1%BB%A5+ki%E1%BB%87n+l%C3%A0m+th%C6%A1m+ph%C3%B2ng%22,%22categoryId%22:%2212745%22}&q=ph%E1%BB%A5+ki%E1%BB%87n+l%C3%A0m+th%C6%A1m+ph%C3%B2ng&rating=1&page=2",
        "Cây và Hạt Giống": "https://www.lazada.vn/cac-loai-cay-hat-giong/?from=hp_categories&params={%22catIdLv1%22:%2210100245%22,%22pvid%22:%22f1be9b84-6797-4e8c-81b7-540d5f52d29e%22,%22src%22:%22ald%22,%22categoryName%22:%22C%C3%A2y%2C+h%E1%BA%A1t+gi%E1%BB%91ng++c%E1%BB%A7%22,%22categoryId%22:%2212965%22}&q=c%C3%A2y,+h%E1%BA%A1t+gi%E1%BB%91ng++c%E1%BB%A7&rating=1&page=2",
        "Sữa Dinh Dưỡng": "https://www.lazada.vn/sua-dinh-duong/?from=hp_categories&params={%22catIdLv1%22:%2210550%22,%22pvid%22:%22f1be9b84-6797-4e8c-81b7-540d5f52d29e%22,%22src%22:%22ald%22,%22categoryName%22:%22S%E1%BB%AFa+dinh+d%C6%B0%E1%BB%A1ng%22,%22categoryId%22:%2210557%22}&q=s%E1%BB%AFa+dinh+d%C6%B0%E1%BB%A1ng&rating=1&page=2",
        "Giày": "https://www.lazada.vn/catalog/?q=Gi%C3%A0y&rating=1&page=2",
        "Bánh": "https://www.lazada.vn/catalog/?q=B%C3%A1ch%20H%C3%B3a&rating=1&page=2",
        "Đồ Ăn": "https://www.lazada.vn/tag/%C4%91%E1%BB%93-%C4%83n/?q=%C4%91%E1%BB%93%20%C4%83n&rating=1&catalog_redirect_tag=true&page=2",
        "Thể Thao": "https://www.lazada.vn/catalog/?q=Th%E1%BB%83%20Thao&rating=1&page=2",
        "Sức Khỏe": "https://www.lazada.vn/catalog/?q=S%E1%BB%A9c%20kh%E1%BB%8Fe&rating=1&page=2",
        "Sản Phẩm gia đình": "https://www.lazada.vn/catalog/?q=Gia%20%C4%90%C3%ACnh&rating=1&page=2",
        "Thực phẩm chức năng": "https://www.lazada.vn/tag/th%E1%BB%B1c-ph%E1%BA%A9m-ch%E1%BB%A9c-n%C4%83ng/?q=th%E1%BB%B1c%20ph%E1%BA%A9m%20ch%E1%BB%A9c%20n%C4%83ng&rating=1&catalog_redirect_tag=true&page=2",
        "thực phẩm": "https://www.lazada.vn/tag/th%E1%BB%B1c-ph%E1%BA%A9m/?from=suggest_normal&q=th%E1%BB%B1c%20ph%E1%BA%A9m&rating=1&catalog_redirect_tag=true&page=2"


    }

    driver = init_driver()
    total_reviews = []

    for category_name, category_url in categories.items():
        print(f"\n=== Đang xử lý danh mục: {category_name} ===")
        products = get_product_links(driver, category_url)
        for product_name, product_link in products:
            print(f"📌 Đang xử lý sản phẩm: {product_name}")
            reviews = scrape_product_reviews(driver, product_name, product_link, category_name)
            if reviews:
                total_reviews.extend(reviews)
                save_to_mysql(reviews)

    driver.quit()

    df = pd.DataFrame(total_reviews, columns=["Category", "Product", "Rating", "User", "Comment", "Link"])
    print(df)
