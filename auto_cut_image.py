from asyncio import wait
import zipfile
import os
from pathlib import Path
from openpyxl import load_workbook
from typing import List
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from PIL import Image
from dotenv import load_dotenv


def runAutoCutImage():
    load_dotenv()
    basePath = "/Users/nhan.tt/Downloads/"

    urls = get_urls_from_excel(basePath + "Book1.xlsx")
    downloadImage(urls)
    time.sleep(1)

    # extractAll(basePath)
    # time.sleep(1)

    # crop_jpg_images_in_image_folders(basePath)
    # time.sleep(1)

    # clearImages(urls)
    # time.sleep(1)

    return


def clearImages(urls: List[str]):
    driver = webdriver.Chrome()
    logged_in = False
    username, password = get_login_credentials()
    for index, url in enumerate(urls):
        try:
            driver.get(url)

            if not logged_in:
                try:
                    driver.find_element(By.NAME, "username")
                    driver.find_element(By.NAME, "password")

                    login(driver, username, password)

                    time.sleep(2)
                    logged_in = True

                    driver.get(url)
                    print("Đã login thành công")
                except:
                    print("Không cần login")
                    logged_in = True
                    pass

            elements = driver.find_elements(By.CSS_SELECTOR, "a.del-img")
            count = len(elements)

            if count == 0:
                continue

            # Scroll to the target section
            target_element = driver.find_element(
                By.XPATH, "//h3[contains(text(), 'Hình ảnh cửa hàng')]"
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", target_element)
            time.sleep(1)

            driver.execute_script(
                "document.querySelectorAll('a.del-img').forEach(el => el.click());"
            )

            print(f"Đã xóa {count} ảnh, index: {index}, URL: {url}")
            time.sleep(2)

        except Exception as e:
            print(f"Lỗi khi xóa ảnh từ {url}: {e} - URL index: {index}")
    driver.quit()
    return


def crop_jpg_images_in_image_folders(base_path: str, top_ratio: float = 0.5):
    if not os.path.isdir(base_path):
        print(f"Base path không tồn tại: {base_path}")
        return

    for root, dirs, files in os.walk(base_path):
        folder_name = os.path.basename(root).lower()
        if "images" not in folder_name:
            continue

        for file_name in files:
            if not file_name.lower().endswith(".jpg"):
                continue

            file_path = os.path.join(root, file_name)
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    if height <= 1:
                        continue

                    top = int(height * top_ratio)
                    cropped = img.crop((0, top, width, height))
                    if cropped.mode in ("RGBA", "LA", "P"):
                        cropped = cropped.convert("RGB")
                    cropped.save(file_path)
            except Exception as e:
                print(f"Lỗi khi cắt ảnh: {file_path} - {e}")
    print("Đã cắt xong tất cả ảnh trong các thư mục chứa 'images'")
    return


def extractAll(path: str):
    for fileName in os.listdir(path):
        if fileName.endswith(".zip"):
            filePath = os.path.join(path, fileName)
            with zipfile.ZipFile(filePath, "r") as zip_ref:
                extract_path = os.path.join(path, fileName[:-4])
                zip_ref.extractall(extract_path)
        print("Đã giải nén tất cả file zip")
    return


def downloadImage(urls: List[str]):
    driver = webdriver.Chrome()
    logged_in = False
    username, password = get_login_credentials()
    for index, url in enumerate(urls):
        try:
            driver.get(url)

            if not logged_in:
                try:
                    driver.find_element(By.NAME, "username")
                    driver.find_element(By.NAME, "password")

                    # PA account
                    login(driver, username, password)

                    time.sleep(2)
                    logged_in = True

                    driver.get(url)
                    print("Đã login thành công")
                except:
                    print("Không cần login")
                    logged_in = True
                    pass

            download_button_xpath = "//a[contains(., 'Tải hình ảnh')]"

            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, download_button_xpath))
            )

            print("Đang click nút tải hình ảnh... URL index:", index)
            button.click()
            time.sleep(3)

        except Exception as e:
            print(f"Lỗi khi tải ảnh từ {url}: {e} - URL index: {index}")

    driver.quit()


def get_urls_from_excel(file_path: str) -> List[str]:
    """
    Đọc file Excel và trích xuất danh sách URL từ cột A.
    """
    urls = []

    try:
        # data_only=False để đọc được công thức nếu có
        workbook = load_workbook(file_path, data_only=False)
        sheet = workbook.active

        for row in sheet.iter_rows(min_row=1):
            cell = row[0]  # Chỉ xét cột A
            url = None

            # 1. Kiểm tra nếu cell có đối tượng Hyperlink trực tiếp
            if cell.hyperlink:
                url = cell.hyperlink.target

            # 2. Nếu không có hyperlink object, kiểm tra xem có phải công thức =HYPERLINK() không
            elif isinstance(cell.value, str) and cell.value.startswith("=HYPERLINK("):
                # Trích xuất URL bên trong dấu ngoặc kép: =HYPERLINK("https://...", "Display Name")
                try:
                    # Tách lấy phần nằm giữa cặp dấu ngoặc kép đầu tiên
                    url = cell.value.split('"')[1]
                except IndexError:
                    url = cell.value

            # 3. Nếu là text thuần (người dùng dán thẳng link vào)
            else:
                url = cell.value

            # Làm sạch dữ liệu và chỉ thêm vào list nếu là chuỗi có nội dung
            if url and isinstance(url, str):
                clean_url = url.strip()
                if clean_url.startswith("http"):
                    urls.append(clean_url)

    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file tại: {file_path}")
    except Exception as e:
        print(f"Lỗi khi đọc file Excel: {e}")

    return urls


def get_login_credentials() -> tuple[str, str]:
    username = os.getenv("LOGIN_USERNAME", "").strip()
    password = os.getenv("LOGIN_PASSWORD", "").strip()

    if not username or not password:
        raise ValueError("Thiếu LOGIN_USERNAME hoặc LOGIN_PASSWORD trong file .env")

    return username, password


def login(driver, username_value, password_value):
    """Login to the website with provided credentials"""
    username = driver.find_element(By.NAME, "username")
    username.send_keys(username_value)

    password = driver.find_element(By.NAME, "password")
    password.send_keys(password_value)

    driver.find_element(By.XPATH, "//button[text()='Đăng nhập']").click()
    time.sleep(1)
