import logging
import os
from datetime import datetime

# Tạo thư mục logs nếu chưa tồn tại
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Tạo file log với timestamp
log_filename = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()  # Cũng in ra console
    ]
)

# Tạo logger
logger = logging.getLogger(__name__)

# In ra file log được sử dụng
logger.info(f"Log file: {log_filename}")
