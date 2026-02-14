import cv2
import os


def smart_crop_text(
    image_path: str, crop_ratio: float = 0.125, scan_ratio: float = 0.05
):
    """Cắt bỏ phần có chữ trắng ở cạnh ảnh và ghi đè lên file gốc."""
    # 1. Đọc ảnh
    img = cv2.imread(image_path)
    if img is None:
        print(f"Không thể mở ảnh: {image_path}")
        return

    h, w, _ = img.shape

    # Tính toán tọa độ pixel
    h_scan = int(h * scan_ratio)
    w_scan = int(w * scan_ratio)
    h_crop = int(h * crop_ratio)
    w_crop = int(w * crop_ratio)

    # 2. Tiền xử lý (Chuyển xám và lấy ngưỡng trắng)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)

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

    # 5. Cắt bỏ tại cạnh đã xác định
    # Nếu max_white quá thấp (< 100 pixel), ảnh không có chữ, giữ nguyên
    if max_white < 100:
        print("Không phát hiện chữ trắng ở các cạnh.")
        return

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
    print("Cắt hình thành công")
