import os
import time
from auto_edit_date import run_auto_edit_date
from auto_cut_image import run_auto_cut_image
from dotenv import load_dotenv
from logger import logger

load_dotenv()

# Giữ màn hình macOS không tắt và không khóa (~3 giờ cho 180 data)
# -i: tắt idle sleep
# -s: tắt display sleep
os.system('caffeinate -is -t 10800 &')

base_path = "/Users/nhantruong/Downloads/"

# logger.info("Bắt đầu chạy auto_cut_image")
run_auto_cut_image(base_path)

# Chờ giữa 2 hàm để đảm bảo hệ thống ổn định
time.sleep(10)

run_auto_edit_date(base_path)
