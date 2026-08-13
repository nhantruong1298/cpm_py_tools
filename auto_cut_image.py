import zipfile
import os
import shutil
from openpyxl import load_workbook
from typing import List
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from PIL import Image
import pyautogui
import pyperclip
import subprocess
from common import get_login_credentials, login
from smart_crop_text import smart_crop_text
from logger import logger


def run_auto_cut_image(base_path: str):
    driver = webdriver.Chrome()
    try:
        urls = get_urls_from_excel(base_path + "Book1.xlsx")

        username, password = get_login_credentials()
        logged_in = False

        for index, url in enumerate(urls):
            logger.info(f"** Row index: {index+1}, URL to process: {url} **")
            try:
                driver.get(url)
                time.sleep(2.1)

                if not logged_in:
                    try:
                        login(driver, username, password)

                        time.sleep(2.2)
                        logged_in = True

                        driver.get(url)
                        logger.info("Đã login thành công")
                    except:
                        logger.info("Không cần login")
                        logged_in = True
                        pass

                download_images_from(driver)
                time.sleep(3.1)

                extract_all_images_from(base_path)
                time.sleep(2.1)

                crop_jpg_images_in_image_folder_from(base_path)
                time.sleep(2.1)

                clear_images_from(url, driver)
                time.sleep(2.3)

                send_images_to(driver, base_path)
                time.sleep(3.1)

                clean_base_path(base_path)
                time.sleep(2)

            except Exception as e:
                logger.info(f"Lỗi khi xử lý url tại hàng {index+1}: {e}")
                clean_base_path(base_path)
                logged_in = False
                time.sleep(2)
                continue
    finally:
        driver.quit()
    return


def send_images_to(driver: webdriver.Chrome, base_path: str):
    try:
        btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//button[contains(@onclick,'initUpload') and contains(@onclick,'plan_image_audit') and contains(@onclick,'type_image=image_audit')]",
                )
            )
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        time.sleep(1)
        try:
            btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", btn)

        time.sleep(2)
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "image-dropzone"))
        )

        # Select dropdown image_type_id và chọn Overview (value="2")
        image_type_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "image_type_id"))
        )
        driver.execute_script("arguments[0].value = '2';", image_type_select)
        time.sleep(1)

        image_folder = find_first_image_folder(base_path)
        path_to_file = image_folder

        if not path_to_file:
            logger.info(f"Không tìm thấy thư mục chứa ảnh trong: {base_path}")
            return

        # Lấy danh sách tất cả file ảnh trong folder
        image_files = []
        for file_name in os.listdir(path_to_file):
            if file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                full_path = os.path.join(path_to_file, file_name)
                image_files.append(full_path)

        if not image_files:
            logger.info(f"Không tìm thấy file ảnh trong: {path_to_file}")
            return

        # Dùng Selenium để submit file
        # Tìm file input element
        file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        
        if file_inputs:
            file_input = file_inputs[-1]  # Lấy file input cuối cùng
            
            # Focus vào element và clear trước khi gửi
            driver.execute_script("arguments[0].focus();", file_input)
            time.sleep(0.5)
            
            try:
                # Gửi danh sách file path - dùng separator \n cho multiple files
                file_path_string = '\n'.join(image_files)
                file_input.send_keys(file_path_string)
                logger.info(f"Đã gửi {len(image_files)} file ảnh: {', '.join([os.path.basename(f) for f in image_files[:3]])}")
                time.sleep(5)  # Chờ thêm để server xử lý
            except Exception as send_error:
                logger.warning(f"Lỗi send_keys: {send_error}")
                # Nếu gửi batch fail, thử gửi file đầu tiên
                try:
                    logger.info(f"Thử lại: gửi file đầu tiên {os.path.basename(image_files[0])}")
                    file_input.send_keys(image_files[0])
                    time.sleep(3)
                except Exception as retry_error:
                    logger.error(f"Cả batch lẫn single file đều fail: {retry_error}")
        else:
            logger.warning("Không tìm thấy file input element")

        logger.info(f"Hoàn tất gửi ảnh")
    except Exception as e:
        logger.error(f"Lỗi khi gửi ảnh: {type(e).__name__}: {e}")
    return


def find_first_image_folder(base_path: str) -> str | None:
    if not os.path.isdir(base_path):
        return None

    for root, dirs, files in os.walk(base_path):
        folder_name = os.path.basename(root).lower()
        if "image" in folder_name:
            return root

    return None


def clear_images_from(url: str, driver: webdriver.Chrome):
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, "a.del-img")
        count = len(elements)

        if count == 0:
            logger.info(f"Không có ảnh để xóa tại URL: {url}")
            return

        # Scroll to the target section
        target_element = driver.find_element(
            By.XPATH, "//h3[contains(text(), 'Hình ảnh cửa hàng')]"
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", target_element)
        time.sleep(1)

        driver.execute_script(
            "document.querySelectorAll('a.del-img').forEach(el => el.click());"
        )

        logger.info(f"Đã xóa {count} ảnh")
        time.sleep(2)

    except Exception as e:
        logger.info(f"Lỗi khi xóa ảnh từ {url}: {e}")
    return


def crop_jpg_images_in_image_folder_from(base_path: str, crop_ratio: float = 0.125):
    if not os.path.isdir(base_path):
        logger.info(f"Base path không tồn tại: {base_path}")
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
                # Cách cũ: cắt bằng PIL, nhưng có thể bị lỗi với một số ảnh đặc biệt
                with Image.open(file_path) as img:
                    width, height = img.size
                    if height <= 1:
                        continue

                    top = int(height * 0.125)
                    cropped = img.crop((0, top, width, height))
                    if cropped.mode in ("RGBA", "LA", "P"):
                        cropped = cropped.convert("RGB")
                    cropped.save(file_path)

                # Cách mới: dùng smart_crop_text để cắt, có thể xử lý tốt hơn với các ảnh đặc biệt
                # smart_crop_text(file_path, crop_ratio)
            except Exception as e:
                logger.info(f"Lỗi khi cắt ảnh: {file_path} - {e}")
    logger.info("Đã cắt xong tất cả ảnh")
    return


def extract_all_images_from(basePath: str):
    for fileName in os.listdir(basePath):
        if fileName.endswith(".zip"):
            filePath = os.path.join(basePath, fileName)
            with zipfile.ZipFile(filePath, "r") as zip_ref:
                extract_path = os.path.join(basePath, fileName[:-4])
                zip_ref.extractall(extract_path)
    logger.info("Đã giải nén tất cả file zip")
    return


def download_images_from(driver: webdriver.Chrome):
    download_button_xpath = "//a[contains(., 'Tải hình ảnh')]"

    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, download_button_xpath))
    )

    button.click()
    logger.info("Đã click vào nút tải hình ảnh")
    return


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
        logger.info(f"Lỗi: Không tìm thấy file tại: {file_path}")
    except Exception as e:
        logger.info(f"Lỗi khi đọc file Excel: {e}")

    return urls


def clean_base_path(base_path: str):
    """Xóa tất cả folders và files trong base_path, chỉ giữ lại file .xlsx"""
    if not os.path.isdir(base_path):
        logger.info(f"Base path không tồn tại: {base_path}")
        return

    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)

        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        elif os.path.isfile(item_path) and not item.endswith(".xlsx"):
            os.remove(item_path)

    logger.info(f"Đã dọn dẹp xong")
    return
