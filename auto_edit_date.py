from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from typing import Dict, Any
from openpyxl import load_workbook
from common import get_login_credentials, login
from logger import logger


def select_date(driver, plan, date):
    """Sửa ngày format MM/DD/YYYY"""
    driver.find_element(By.NAME, f"plan[{plan}]").click()
    time.sleep(0.5)
    driver.find_element(
        By.CSS_SELECTOR, f"td[data-day='{date.replace('\"', '')}']"
    ).click()
    time.sleep(0.5)
    driver.find_element(By.NAME, f"plan[{plan}]").click()
    time.sleep(0.5)


def replace_date(driver, plan, dateFromExcel):
    """Sửa ngày format 2025-12-28"""
    element = driver.find_element(By.NAME, f"plan[{plan}]")
    time.sleep(0.25)
    dateFromWeb = element.get_attribute("value")
    dateParts = dateFromWeb.split(" ")

    element.clear()
    time.sleep(0.5)
    element.send_keys(dateFromExcel + " " + dateParts[1])


def save_date(driver):
    """Lưu ngày đã chọn"""

    button_save = driver.find_element(
        By.XPATH,
        "//button[@type='button' and contains(@class, 'btn-success') and contains(@onclick, 'savePlan')]",
    )

    driver.execute_script("arguments[0].scrollIntoView(true);", button_save)
    time.sleep(0.5)
    button_save.click()
    time.sleep(1)


def select_note_and_fill_and_save(driver, name):
    """Chọn note khác và điền nội dung và lưu"""
    element_to_click = driver.find_element(
        By.XPATH, "//a[@class='chosen-single' and contains(., 'Chọn loại Note')]"
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", element_to_click)
    time.sleep(0.25)
    element_to_click.click()
    time.sleep(0.25)
    element_to_click = driver.find_element(
        By.XPATH, "//li[contains(@class, 'active-result') and text()='Note khác']"
    )
    element_to_click.click()
    time.sleep(0.25)
    driver.find_element(By.ID, "note_comment").send_keys(
        f"{name} - Chỉnh Ngày + Cắt Hình"
    )
    time.sleep(0.25)
    save_button = driver.find_element(
        By.XPATH,
        "//button[@id='uploadSnap' and @type='button' and contains(@onclick, 'uploadSnap')]",
    )

    driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
    save_button.click()
    time.sleep(0.25)
    

def confirm_sign(driver):
    """Nhan nut Xac nhan da ky"""
    confirm_button = driver.find_element(
        By.XPATH,
        "//button[@id='xbutton-confirm' and @type='button' and contains(@onclick, 'savePlan')]",
    )

    driver.execute_script("arguments[0].scrollIntoView(true);", confirm_button)
    confirm_button.click()
    time.sleep(0.25)


def read_excel_to_map_with_hyperlinks(file_path: str) -> Dict[str, Any]:
    """
    Đọc dữ liệu từ file Excel, lấy URL ẩn từ hyperlink ở cột A
    và String hiển thị ở cột B, lưu vào dictionary.
    """
    data_map = {}

    try:
        workbook = load_workbook(file_path, data_only=False)
        sheet = workbook.active

        for row in sheet.iter_rows(min_row=1):
            # Check if row has at least 2 columns
            if len(row) < 1:
                continue
            
            # Use .target to get the actual URL from hyperlink in column A (row[0])
            url_cell = (
                row[0].value
                # if row[0].hyperlink and row[0].value
                # else row[0].value
            )
            
            # Get date from column B (row[1])
            # date_cell = row[1].value
            # if not date_cell:
            #     continue
            # date_cell = str(date_cell).replace("'", "")
            date_cell = '2025-12-28'  # Hardcoded date for testing

            if url_cell and isinstance(url_cell, str):
                # Extract URL from =HYPERLINK(url, text) formula
                if url_cell.startswith('=HYPERLINK('):
                    start = url_cell.find('(') + 1
                    end = url_cell.find(',', start)
                    url_cell = url_cell[start:end].strip().replace('"', '')
                else:
                    # Remove quotes if present
                    url_cell = url_cell.replace('"', "").strip()

            url_parts = [url_cell] if url_cell else []
            if url_parts and url_parts[0] and url_parts[0].startswith("https://"):
                data_map[url_parts[0]] = date_cell.strip()
            else:
                continue

    except FileNotFoundError:
        logger.info(f"Lỗi: Không tìm thấy file tại đường dẫn: {file_path}")
    except Exception as e:
        logger.info(f"Lỗi xảy ra khi đọc file Excel: {e}")

    return data_map


def run_auto_edit_date(base_path: str):
    data = read_excel_to_map_with_hyperlinks(base_path + "Book1.xlsx")

    driver = webdriver.Chrome()
    try:
        logged_in = False
        count = 0
        error_count = 0
        error_list = []  # Danh sách lưu các URL bị lỗi

        # Kiểm tra thông tin cẩn thận
        username, password = get_login_credentials()

        for url, dateFromExcel in data.items():
            try:
                driver.get(url)
                time.sleep(.5)
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

                # replace_date(driver, "time_checkin", dateFromExcel)
                # replace_date(driver, "time_checkout", dateFromExcel)
                # replace_date(driver, "time_upload", dateFromExcel)

                # time.sleep(0.5)
                # save_date(driver)

                # PA , Phước , Khắc Huy
                select_note_and_fill_and_save(driver, "PA")

                time.sleep(0.5)

                count += 1
                logger.info(f"Đã xử lý {count} URL")

            except Exception as e:
                error_count += 1
                error_info = {"URL": url, "Ngày": dateFromExcel, "Lỗi": str(e)}
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
                ws["B1"] = "Ngày"
                ws["C1"] = "Lỗi"

                # Dữ liệu
                for idx, error_info in enumerate(error_list, start=2):
                    ws[f"A{idx}"] = error_info["URL"]
                    ws[f"B{idx}"] = error_info["Ngày"]
                    ws[f"C{idx}"] = error_info["Lỗi"]

                # Tự động điều chỉnh độ rộng cột
                ws.column_dimensions["A"].width = 80
                ws.column_dimensions["B"].width = 15
                ws.column_dimensions["C"].width = 50

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




def run_auto_sign(base_path: str):
    data = read_excel_to_map_with_hyperlinks(base_path + "Book1.xlsx")

    driver = webdriver.Chrome()
    try:
        logged_in = False
        count = 0
        error_count = 0
        error_list = []  # Danh sách lưu các URL bị lỗi

        # Kiểm tra thông tin cẩn thận
        username, password = get_login_credentials()

        for url, _ in data.items():
            try:
                driver.get(url)
                time.sleep(.5)
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


                confirm_sign(driver)

                time.sleep(0.25)

                count += 1
                logger.info(f"Đã xử lý {count} URL")

            except Exception as e:
                error_count += 1
                error_info = {"URL": url, "Ngày": "", "Lỗi": str(e)}
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
                ws["B1"] = "Ngày"
                ws["C1"] = "Lỗi"

                # Dữ liệu
                for idx, error_info in enumerate(error_list, start=2):
                    ws[f"A{idx}"] = error_info["URL"]
                    ws[f"B{idx}"] = error_info["Ngày"]
                    ws[f"C{idx}"] = error_info["Lỗi"]

                # Tự động điều chỉnh độ rộng cột
                ws.column_dimensions["A"].width = 80
                ws.column_dimensions["B"].width = 15
                ws.column_dimensions["C"].width = 50

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
