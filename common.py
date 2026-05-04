import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from logger import logger

def get_login_credentials() -> tuple[str, str]:
    username = os.getenv("LOGIN_USERNAME", "").strip()
    password = os.getenv("LOGIN_PASSWORD", "").strip()

    if not username or not password:
        raise ValueError("Thiếu LOGIN_USERNAME hoặc LOGIN_PASSWORD trong file .env")

    return username, password


def login(driver, username_value, password_value):
    """Login to the website with provided credentials (handles double login)"""

    
    max_login_attempts = 2
    attempt = 0
    
    while attempt < max_login_attempts:
        try:
            # Chờ và nhập username
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.clear()
            username_field.send_keys(username_value)
            
            # Chờ và nhập password
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_field.clear()
            password_field.send_keys(password_value)
            
            # Click nút đăng nhập
            login_button = driver.find_element(By.XPATH, "//button[text()='Đăng nhập']")
            login_button.click()
            
            time.sleep(2)
            attempt += 1
            
        except Exception as e:
            logger.info(f"Login attempt {attempt + 1} failed: {e}")
            break
