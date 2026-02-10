from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from typing import Dict, Any
from openpyxl import load_workbook
from dotenv import load_dotenv
import os


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
            url_cell = (
                row[0].hyperlink.display
                if row[0].hyperlink and row[0].hyperlink.display
                else row[0].value
            )
            string_cell = row[1].value.replace("'", "")

            if url_cell and isinstance(url_cell, str):
                if url_cell.startswith('=HYPERLINK("') and url_cell.endswith('")'):
                    url_cell = url_cell[12:-2]

            url_parts = url_cell.split(",")
            if url_parts[0].strip().startswith("https://") and "-" in string_cell:
                data_map[url_parts[0].replace('"', "").strip()] = string_cell.replace(
                    '"', ""
                ).strip()
            else:
                continue

    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file tại đường dẫn: {file_path}")
    except Exception as e:
        print(f"Lỗi xảy ra khi đọc file Excel: {e}")

    return data_map


# Code execution starts here
def runAutoEditDate():
    load_dotenv()
    data = read_excel_to_map_with_hyperlinks("/Users/nhan.tt/Desktop/Book1.xlsx")

    driver = webdriver.Chrome()
    logged_in = False
    count = 0
    error_count = 0
    error_list = []  # Danh sách lưu các URL bị lỗi

    username, password = get_login_credentials()

    for url, dateFromExcel in data.items():
        try:
            driver.get(url)

            # Chỉ login một lần duy nhất
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

            replace_date(driver, "time_checkin", dateFromExcel)
            replace_date(driver, "time_checkout", dateFromExcel)
            replace_date(driver, "time_upload", dateFromExcel)

            time.sleep(0.5)
            save_date(driver)

            # select_note_and_fill_and_save(driver, "PA")

            # select_note_and_fill_and_save(driver, "Phước")

            select_note_and_fill_and_save(driver, "Khắc Huy")

            time.sleep(0.5)

            count += 1
            print(f"Đã xử lý {count} URL")

        except Exception as e:
            error_count += 1
            error_info = {"URL": url, "Ngày": dateFromExcel, "Lỗi": str(e)}
            error_list.append(error_info)
            print(f"❌ Lỗi tại URL: {url}")
            print(f"   Lỗi: {str(e)}")
            print(f"   Tổng số lỗi: {error_count}")
            continue
    # Xuất danh sách lỗi ra file Excel
    if error_list:
        output_file = "/Users/nhan.tt/Desktop/Error_Report.xlsx"
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
            print(f"\n📄 Đã xuất danh sách lỗi ra file: {output_file}")
        except Exception as e:
            print(f"\n⚠️ Không thể tạo file báo cáo lỗi: {e}")
    else:
        print(f"\n✅ Không có lỗi nào để xuất ra file")

    print(f"✅ Đã xử lý thành công: {count} URL")
    print(f"❌ Số lỗi: {error_count} URL")
    print(f"📊 Tổng cộng: {count + error_count} URL")

    time.sleep(5)
    driver.quit()
