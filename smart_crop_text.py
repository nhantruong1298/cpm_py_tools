import cv2
import os
from logger import logger


def smart_crop_text(
    image_path: str, crop_ratio: float = 0.125, scan_ratio: float = 0.05
):
    """Cắt bỏ phần có chữ trắng ở cạnh ảnh và ghi đè lên file gốc."""
    # 1. Đọc ảnh
    img = cv2.imread(image_path)
    if img is None:
        logger.warning(f"Không thể mở ảnh: {image_path}")
        return

    h, w, _ = img.shape

    # Tính toán tọa độ pixel
    h_scan = int(h * scan_ratio)
    w_scan = int(w * scan_ratio)
    h_crop = int(h * crop_ratio)
    w_crop = int(w * crop_ratio)

    # 2. Tiền xử lý (Chuyển xám)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Thử nhiều threshold để phát hiện chữ trắng (có thể không hoàn toàn trắng)
    thresholds = [250, 245, 240, 230, 220]
    best_result = None
    best_edge = None
    best_max_white = 0
    
    for threshold_val in thresholds:
        _, binary = cv2.threshold(gray, threshold_val, 255, cv2.THRESH_BINARY)
        
        # Dùng morphological operations để làm mạnh text pattern
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        binary = cv2.dilate(binary, kernel, iterations=2)

        # 3. Định nghĩa vùng quét (chỉ 5% sát mép)
        scan_zones = {
            "top": binary[0:h_scan, :],
            "bottom": binary[h - h_scan : h, :],
            "left": binary[:, 0:w_scan],
            "right": binary[:, w - w_scan : w],
        }

        # 4. Tìm cạnh có mật độ chữ trắng cao nhất
        max_white = 0
        target_edge = None

        for edge, zone in scan_zones.items():
            white_pixels = cv2.countNonZero(zone)
            if white_pixels > max_white:
                max_white = white_pixels
                target_edge = edge

        # Nếu phát hiện được chữ ở cạnh nào, lưu kết quả tốt nhất
        if max_white > best_max_white and max_white > 50:
            best_max_white = max_white
            best_edge = target_edge
            best_result = (img, target_edge, threshold_val)

    # 5. Cắt bỏ tại cạnh đã xác định
    if best_result is None or best_max_white < 50:
        logger.info(f"Không phát hiện chữ trắng ở các cạnh")
        return

    img, target_edge, used_threshold = best_result

    if target_edge == "top":
        result = img[h_crop:h, :]
    elif target_edge == "bottom":
        result = img[0 : h - h_crop, :]
    elif target_edge == "left":
        result = img[:, w_crop:w]
    elif target_edge == "right":
        result = img[:, 0 : w - w_crop]

    # 6. Ghi đè lên file gốc
    cv2.imwrite(image_path, result)
    logger.info(f"Cắt hình thành công (threshold: {used_threshold}, vị trí: {target_edge})")
