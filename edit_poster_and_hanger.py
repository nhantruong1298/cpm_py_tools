import random
import time
from typing import Dict
from openpyxl import load_workbook
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from common import get_login_credentials, login
from logger import logger

PLAN_INFO_URL = "https://aws2.cpm-vietnam.com/posm/index.php?route=plan/plan/info&plan_id="
ALLOWED_POSTER_TYPES = {"Poster 50x70", "Poster 30x40"}


def human_sleep(base_seconds: float) -> None:
    """Sleep một khoảng thời gian ngẫu nhiên quanh base_seconds để giống thao tác của người thật"""
    time.sleep(base_seconds * random.uniform(1.1, 1.3))


def read_plan_ids_and_poster_type(file_path: str) -> Dict[str, str]:
    """Đọc plan_id (cột A) và loại Poster (cột B), trả về {url: poster_type}"""
    data_map = {}

    try:
        workbook = load_workbook(file_path, data_only=True)
        sheet = workbook.active

        for row in sheet.iter_rows(min_row=1):
            if len(row) < 2:
                continue

            plan_id_cell = row[0].value
            poster_type_cell = row[1].value
            if not plan_id_cell or not poster_type_cell:
                continue

            plan_id = str(plan_id_cell).strip()
            poster_type = str(poster_type_cell).strip()
            if poster_type not in ALLOWED_POSTER_TYPES:
                logger.warning(
                    f"Bỏ qua plan_id {plan_id}: giá trị cột B không hợp lệ '{poster_type}'"
                )
                continue

            data_map[PLAN_INFO_URL + plan_id] = poster_type

    except FileNotFoundError:
        logger.info(f"Lỗi: Không tìm thấy file tại đường dẫn: {file_path}")
    except Exception as e:
        logger.info(f"Lỗi xảy ra khi đọc file Excel: {e}")

    return data_map


def select_qc_code_khac(driver):
    """Mở dropdown 'Code 6: Khác' và tick checkbox Code 6.3 - Code Khác"""
    dropdown_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[contains(@class, 'dropdown-toggle') and contains(., 'Code 6')]",
            )
        )
    )
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", dropdown_button
    )
    human_sleep(0.25)
    dropdown_button.click()
    human_sleep(0.5)

    checkbox = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//input[@type='checkbox' and @value='6.3']")
        )
    )
    if not checkbox.is_selected():
        checkbox.click()
    human_sleep(0.5)


def select_poster_hanger_and_save(driver, poster_type: str):
    """Cuộn tới câu hỏi 'Poster/Hanger', chọn giá trị theo poster_type rồi bấm Lưu"""
    question_row = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//tr[@data-info='question_id=3002']")
        )
    )
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", question_row
    )
    human_sleep(0.5)

    chosen_toggle = question_row.find_element(
        By.XPATH,
        ".//div[contains(@class, 'chosen-container')]//a[@class='chosen-single']",
    )
    chosen_toggle.click()
    human_sleep(0.5)

    option = question_row.find_element(
        By.XPATH,
        f".//li[contains(@class, 'active-result') and normalize-space(text())='{poster_type}']",
    )
    option.click()
    human_sleep(0.5)

    save_buttons = question_row.find_elements(
        By.XPATH,
        "./ancestor::div[contains(@class, 'card') and contains(@class, 'box-default')][1]"
        "//div[contains(@class, 'card-footer')]//button[contains(@class, 'save-survey')]",
    )
    if len(save_buttons) != 1:
        logger.warning(
            f"Tìm thấy {len(save_buttons)} nút Lưu khớp điều kiện (kỳ vọng 1), kiểm tra lại layout trang"
        )
    save_button = save_buttons[0]
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", save_button
    )
    human_sleep(0.25)
    save_button.click()
    human_sleep(1)


def body(driver, poster_type: str):
    select_qc_code_khac(driver)
    select_poster_hanger_and_save(driver, poster_type)


def edit_poster_and_hanger(base_path: str, start_from: int = 0):
    """Chạy xử lý poster/hanger. start_from: số URL đã xử lý ở lần chạy trước,
    dùng để bỏ qua và chạy tiếp (vd: hôm qua đã xử lý 667 URL thì truyền start_from=667)."""
    data = read_plan_ids_and_poster_type(base_path + "Book1.xlsx")
    items = list(data.items())
    total = len(items)

    if start_from > 0:
        logger.info(
            f"⏩ Bỏ qua {start_from} URL đã xử lý trước đó, tiếp tục từ URL số {start_from + 1}/{total}"
        )
        items = items[start_from:]

    driver = webdriver.Chrome()
    try:
        logged_in = False
        count = start_from
        error_count = 0
        error_list = []  # Danh sách lưu các URL bị lỗi

        # Kiểm tra thông tin cẩn thận
        username, password = get_login_credentials()

        for url, poster_type in items:
            try:
                driver.get(url)
                human_sleep(0.5)
                if not logged_in:
                    try:
                        login(driver, username, password)

                        human_sleep(2)
                        logged_in = True

                        driver.get(url)
                        logger.info("Đã login thành công")
                    except:
                        logger.info("Không cần login")
                        logged_in = True
                        pass

                body(driver, poster_type)

                human_sleep(0.5)

                count += 1
                logger.info(f"Đã xử lý {count} URL")

            except Exception as e:
                error_count += 1
                error_info = {"URL": url, "Lỗi": str(e)}
                error_list.append(error_info)
                logger.info(f"❌ Lỗi tại URL: {url}")
                logger.info(f"   Lỗi: {str(e)}")
                logger.info(f"   Tổng số lỗi: {error_count}")
                continue

        # Xuất danh sách lỗi ra file Excel
        if error_list:
            output_file = "/Users/nhantruong/Desktop/Error_Report.xlsx"
            try:
                from openpyxl import Workbook

                wb = Workbook()
                ws = wb.active
                ws.title = "Danh sách lỗi"

                # Header
                ws["A1"] = "URL"
                ws["B1"] = "Lỗi"

                # Dữ liệu
                for idx, error_info in enumerate(error_list, start=2):
                    ws[f"A{idx}"] = error_info["URL"]
                    ws[f"B{idx}"] = error_info["Lỗi"]

                # Tự động điều chỉnh độ rộng cột
                ws.column_dimensions["A"].width = 80
                ws.column_dimensions["B"].width = 50

                wb.save(output_file)
                logger.info(f"\n📄 Đã xuất danh sách lỗi ra file: {output_file}")
            except Exception as e:
                logger.info(f"\n⚠️ Không thể tạo file báo cáo lỗi: {e}")
        else:
            logger.info(f"\n✅ Không có lỗi nào để xuất ra file")

        logger.info(f"✅ Đã xử lý thành công: {count} URL")
        logger.info(f"❌ Số lỗi: {error_count} URL")
        logger.info(f"📊 Tổng cộng: {count + error_count} URL")

        human_sleep(5)
    finally:
        driver.quit()
