import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from common import get_login_credentials, login
from auto_cut_image import get_urls_from_excel
from logger import logger


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
    time.sleep(0.25)
    dropdown_button.click()
    time.sleep(0.5)

    checkbox = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//input[@type='checkbox' and @value='6.3']")
        )
    )
    if not checkbox.is_selected():
        checkbox.click()
    time.sleep(0.5)


def select_poster_hanger_and_save(driver):
    """Cuộn tới câu hỏi 'Poster/Hanger', chọn giá trị 'Poster 50x70' rồi bấm Lưu"""
    question_row = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//tr[@data-info='question_id=3002']")
        )
    )
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", question_row
    )
    time.sleep(0.5)

    chosen_toggle = question_row.find_element(
        By.XPATH,
        ".//div[contains(@class, 'chosen-container')]//a[@class='chosen-single']",
    )
    chosen_toggle.click()
    time.sleep(0.5)

    option = question_row.find_element(
        By.XPATH,
        ".//li[contains(@class, 'active-result') and normalize-space(text())='Poster 50x70']",
    )
    option.click()
    time.sleep(0.5)

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
    time.sleep(0.25)
    save_button.click()
    time.sleep(1)


def body(driver):
    select_qc_code_khac(driver)
    select_poster_hanger_and_save(driver)


def edit_poster_and_hanger(base_path: str):
    urls = get_urls_from_excel(base_path + "Book1.xlsx")

    driver = webdriver.Chrome()
    try:
        logged_in = False
        count = 0
        error_count = 0
        error_list = []  # Danh sách lưu các URL bị lỗi

        # Kiểm tra thông tin cẩn thận
        username, password = get_login_credentials()

        for url in urls:
            try:
                driver.get(url)
                time.sleep(0.5)
                if not logged_in:
                    try:
                        login(driver, username, password)

                        time.sleep(2)
                        logged_in = True

                        driver.get(url)
                        logger.info("Đã login thành công")
                    except:
                        logger.info("Không cần login")
                        logged_in = True
                        pass

                body(driver)

                time.sleep(0.5)

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

        time.sleep(5)
    finally:
        driver.quit()
