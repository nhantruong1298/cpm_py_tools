# import os
# import time
from auto_edit_date import run_auto_edit_date
# from auto_cut_image import run_auto_cut_image
from dotenv import load_dotenv
# from edit_poster_and_hanger import edit_poster_and_hanger
# from logger import logger

load_dotenv()

# Giữ màn hình macOS không tắt và không khóa (~2 giờ30 phút cho 120 data)
# -i: tắt idle sleep
# -s: tắt display sleep
# os.system('caffeinate -is -t 9000 &')

base_path = "/Users/nhantruong/Downloads/"

# Số URL đã xử lý ở lần chạy trước, dùng để chạy tiếp (bỏ qua các URL đã xử lý)
# Ví dụ hôm qua đã xử lý 667 URL thì đặt START_FROM = 667
# START_FROM = 667

# Bước 1: Tự động cắt hình
# logger.info("Bắt đầu chạy auto_cut_image")
# run_auto_cut_image(base_path)

# Chờ giữa 2 hàm để đảm bảo hệ thống ổn định
# time.sleep(1)

# Bước 2: Tự động sửa ngày
run_auto_edit_date(base_path)

# Bước 3: Tự động xác nhận đã ký
# run_auto_sign(base_path)

# Bước 4: Chỉnh sửa poster và hanger
# edit_poster_and_hanger(base_path, START_FROM)
