import os
import time
from selenium.webdriver.common.by import By

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
