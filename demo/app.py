"""
Ứng dụng Demo Dự báo Lưu lượng Giao thông theo Giờ (Đề tài 3 - Phân tích dữ liệu lớn)
Sử dụng thư viện Gradio và mô hình XGBoost đã huấn luyện tại models/demo_model.joblib.

Phong cách code: Tuần tự (procedural) và hàm cơ bản, có giải thích tiếng Việt từng bước
để sinh viên dễ dàng đọc hiểu và trình bày khi bảo vệ Bài tập lớn.
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
import gradio as gr

# ==============================================================================
# 1. XÁC ĐỊNH ĐƯỜNG DẪN VÀ NẠP MÔ HÌNH ĐÃ HUẤN LUYỆN
# Tại sao làm bước này?
# - Giúp chạy file app.py từ bất kỳ thư mục nào (thư mục gốc dự án hoặc thư mục app/)
#   mà không bị lỗi không tìm thấy file mô hình.
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "demo_model.joblib")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# Nạp gói mô hình đã lưu từ Notebook 04 (bao gồm model, danh sách cột, ngưỡng P50 và P85)
bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
DEMO_FEATURES = bundle["features"]
P50 = float(bundle["p50"])
P85 = float(bundle["p85"])

# Bảng ánh xạ từ tên Thứ tiếng Việt trên giao diện sang mã số (0 = Thứ Hai ... 6 = Chủ Nhật)
# Tại sao làm bước này? Mô hình học máy chỉ hiểu dữ liệu số, cần khớp đúng quy ước dt.dayofweek của pandas.
DANH_SACH_THU = [
    "Thứ Hai",
    "Thứ Ba",
    "Thứ Tư",
    "Thứ Năm",
    "Thứ Sáu",
    "Thứ Bảy",
    "Chủ Nhật",
]
MAP_THU = {ten: idx for idx, ten in enumerate(DANH_SACH_THU)}


# ==============================================================================
# 2. HÀM BIẾN ĐỔI ĐẶC TRƯNG VÀ DỰ BÁO LƯU LƯỢNG
# Tại sao làm bước này?
# - Người dùng chỉ nhập 6 thông tin cơ bản (Giờ, Thứ, Tháng, Ngày lễ, Nhiệt độ, Độ phủ mây).
# - Hàm này tự động tính thêm 4 đặc trưng phái sinh (is_weekend, is_rush_hour, hour_sin, hour_cos)
#   theo đúng công thức ở Notebook 02 để đưa vào mô hình XGBoost dự báo.
# ==============================================================================
def du_bao_giao_thong(gio, thu_ten, thang, la_ngay_le, nhiet_do_c, do_phu_may):
    # Chuyển đổi kiểu dữ liệu đầu vào
    hour = int(gio)
    day_of_week = int(MAP_THU[thu_ten])
    month = int(thang)
    is_holiday = 1 if bool(la_ngay_le) else 0
    temp_c = float(nhiet_do_c)
    clouds_all = float(do_phu_may)

    # Tính cờ cuối tuần: Thứ Bảy (5) và Chủ Nhật (6) là cuối tuần
    is_weekend = 1 if day_of_week >= 5 else 0

    # Tính cờ giờ cao điểm: 7h-9h sáng hoặc 16h-18h chiều của ngày làm việc bình thường
    khung_cao_diem = (7 <= hour <= 9) or (16 <= hour <= 18)
    ngay_lam_viec = (is_weekend == 0) and (is_holiday == 0)
    is_rush_hour = 1 if (khung_cao_diem and ngay_lam_viec) else 0

    # Mã hóa chu kỳ giờ bằng hàm lượng giác sin/cos để mô hình hiểu 23h và 0h liền kề nhau
    hour_sin = float(np.sin(2.0 * np.pi * hour / 24.0))
    hour_cos = float(np.cos(2.0 * np.pi * hour / 24.0))

    # Đóng gói thành bảng 1 dòng theo đúng thứ tự cột DEMO_FEATURES lúc huấn luyện
    du_lieu_dau_vao = pd.DataFrame([{
        "hour": hour,
        "day_of_week": day_of_week,
        "month": month,
        "is_holiday": is_holiday,
        "temp_c": temp_c,
        "clouds_all": clouds_all,
        "is_weekend": is_weekend,
        "is_rush_hour": is_rush_hour,
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
    }])[DEMO_FEATURES]

    # Dự báo lưu lượng xe/giờ (chặn dưới ở 0 để không bao giờ ra số xe âm)
    du_bao_so = float(model.predict(du_lieu_dau_vao.values)[0])
    luu_luong = max(0, int(round(du_bao_so)))

    # Phân loại mức độ giao thông dựa trên phân vị P50 và P85 của tập Train
    if luu_luong < P50:
        muc_do = "Thông thoáng"
        chi_tiet = f"Thông thoáng (< P50 = {P50:.0f} xe/giờ)"
    elif luu_luong < P85:
        muc_do = "Đông đúc"
        chi_tiet = f"Đông đúc (P50 = {P50:.0f} – P85 = {P85:.0f} xe/giờ)"
    else:
        muc_do = "Nguy cơ ùn tắc"
        chi_tiet = f"Nguy cơ ùn tắc (>= P85 = {P85:.0f} xe/giờ)"

    ket_qua_luu_luong = f"{luu_luong:,} xe/giờ"
    ket_qua_canh_bao = f"{muc_do} — {chi_tiet}"
    return ket_qua_luu_luong, ket_qua_canh_bao


# ==============================================================================
# 3. HÀM KIỂM THỬ TỰ ĐỘNG 4 KỊCH BẢN CHUẨN TRONG ĐỀ CƯƠNG BÁO CÁO
# Tại sao làm bước này?
# - Tự động chạy đúng 4 kịch bản thực nghiệm trong Mục 4.5 của đề cương báo cáo.
# - In bảng kết quả rõ ràng ra màn hình và lưu thành file CSV + TXT trong thư mục results/
#   để nhóm chép trực tiếp số liệu chính xác vào báo cáo.
# ==============================================================================
def chay_kiem_thu_4_kich_ban():
    danh_sach_kich_ban = [
        {
            "kich_ban": "Kịch bản 1",
            "mo_ta": "8h sáng, Thứ Ba, Tháng 10, Không lễ, 15°C, Mây 40%",
            "gio": 8,
            "thu": "Thứ Ba",
            "thang": 10,
            "ngay_le": False,
            "nhiet_do_c": 15.0,
            "may_pct": 40,
            "nhan_xet": "Giờ cao điểm sáng ngày đi làm -> lưu lượng rất cao, cảnh báo nguy cơ ùn tắc.",
        },
        {
            "kich_ban": "Kịch bản 2",
            "mo_ta": "3h sáng, Thứ Ba, Tháng 10, Không lễ, 10°C, Mây 20%",
            "gio": 3,
            "thu": "Thứ Ba",
            "thang": 10,
            "ngay_le": False,
            "nhiet_do_c": 10.0,
            "may_pct": 20,
            "nhan_xet": "Khung giờ đêm khuya rạng sáng -> rất ít phương tiện, đường thông thoáng.",
        },
        {
            "kich_ban": "Kịch bản 3",
            "mo_ta": "15h chiều, Chủ Nhật, Tháng 10, Không lễ, 18°C, Mây 30%",
            "gio": 15,
            "thu": "Chủ Nhật",
            "thang": 10,
            "ngay_le": False,
            "nhiet_do_c": 18.0,
            "may_pct": 30,
            "nhan_xet": "Buổi chiều cuối tuần nhu cầu đi lại vui chơi cao vừa phải -> mức đông đúc.",
        },
        {
            "kich_ban": "Kịch bản 4",
            "mo_ta": "8h sáng, Thứ Ba, Tháng 10, Có Ngày lễ, 15°C, Mây 40%",
            "gio": 8,
            "thu": "Thứ Ba",
            "thang": 10,
            "ngay_le": True,
            "nhiet_do_c": 15.0,
            "may_pct": 40,
            "nhan_xet": "Cùng 8h sáng Thứ Ba nhưng là Ngày lễ -> lưu lượng giảm mạnh so với Kịch bản 1.",
        },
    ]

    ket_qua_bang = []
    for kb in danh_sach_kich_ban:
        luu_luong_str, canh_bao_str = du_bao_giao_thong(
            kb["gio"],
            kb["thu"],
            kb["thang"],
            kb["ngay_le"],
            kb["nhiet_do_c"],
            kb["may_pct"],
        )
        luu_luong_so = int(luu_luong_str.replace(" xe/giờ", "").replace(",", ""))
        muc_do_ngan = canh_bao_str.split(" — ")[0]
        ket_qua_bang.append({
            "Kịch bản": kb["kich_ban"],
            "Thông số đầu vào": kb["mo_ta"],
            "Lưu lượng dự báo (xe/giờ)": luu_luong_so,
            "Hiển thị lưu lượng": luu_luong_str,
            "Mức độ cảnh báo": muc_do_ngan,
            "Chi tiết cảnh báo": canh_bao_str,
            "Đánh giá tính hợp lý thực tế": kb["nhan_xet"],
        })

    df_kb = pd.DataFrame(ket_qua_bang)

    # Lưu kết quả ra file CSV và file log TXT để chép vào báo cáo
    csv_path = os.path.join(RESULTS_DIR, "demo_scenarios_log.csv")
    txt_path = os.path.join(RESULTS_DIR, "demo_scenarios_log.txt")
    df_kb.to_csv(csv_path, index=False, encoding="utf-8-sig")

    lines = [
        "=" * 95,
        "KẾT QUẢ KIỂM THỬ 4 KỊCH BẢN CHUẨN TRONG ĐỀ CƯƠNG (MÔ HÌNH DEMO XGBOOST)",
        f"Ngưỡng phân vị tập Train: P50 = {P50:.0f} xe/giờ | P85 = {P85:.0f} xe/giờ",
        "=" * 95,
        df_kb[["Kịch bản", "Thông số đầu vào", "Lưu lượng dự báo (xe/giờ)", "Mức độ cảnh báo", "Đánh giá tính hợp lý thực tế"]].to_string(index=False),
        "=" * 95,
    ]
    noi_dung_log = "\n".join(lines)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(noi_dung_log + "\n")

    print(noi_dung_log)
    print(f"Đã lưu log kịch bản kiểm thử tại: {csv_path} và {txt_path}")
    return df_kb


# ==============================================================================
# 4. XÂY DỰNG GIAO DIỆN WEB TƯƠNG TÁC BẰNG GRADIO
# Tại sao làm bước này?
# - Cung cấp giao diện trực quan gồm đúng 6 đầu vào và 2 đầu ra theo yêu cầu đề tài,
#   kèm sẵn 4 nút kịch bản mẫu để bấm thử nhanh khi thuyết trình.
# ==============================================================================
def tao_giao_dien_gradio():
    dau_vao = [
        gr.Slider(minimum=0, maximum=23, step=1, value=8, label="1. Giờ trong ngày (0 - 23h)"),
        gr.Dropdown(choices=DANH_SACH_THU, value="Thứ Ba", label="2. Thứ trong tuần"),
        gr.Slider(minimum=1, maximum=12, step=1, value=10, label="3. Tháng trong năm (1 - 12)"),
        gr.Checkbox(value=False, label="4. Ngày lễ (Tick nếu là ngày nghỉ lễ)"),
        gr.Number(value=15.0, label="5. Nhiệt độ ngoài trời (°C)"),
        gr.Slider(minimum=0, maximum=100, step=1, value=40, label="6. Độ phủ mây (%)"),
    ]

    dau_ra = [
        gr.Textbox(label="1. Lưu lượng giao thông dự báo (xe/giờ)"),
        gr.Textbox(label="2. Cảnh báo mức độ giao thông"),
    ]

    cac_vi_du_mau = [
        [8, "Thứ Ba", 10, False, 15.0, 40],     # Kịch bản 1
        [3, "Thứ Ba", 10, False, 10.0, 20],     # Kịch bản 2
        [15, "Chủ Nhật", 10, False, 18.0, 30],  # Kịch bản 3
        [8, "Thứ Ba", 10, True, 15.0, 40],      # Kịch bản 4
    ]

    giao_dien = gr.Interface(
        fn=du_bao_giao_thong,
        inputs=dau_vao,
        outputs=dau_ra,
        title="Dự báo Lưu lượng Giao thông theo Giờ (Đề tài 3 - Phân tích Dữ liệu lớn)",
        examples=cac_vi_du_mau,
        flagging_mode="never",
    )
    return giao_dien


if __name__ == "__main__":
    # Luôn chạy kiểm thử 4 kịch bản chuẩn trước để in bảng kết quả và xuất file log
    chay_kiem_thu_4_kich_ban()

    # Nếu truyền tham số --test-only thì chỉ xuất kết quả kiểm thử rồi thoát (dùng cho tự động hóa)
    if "--test-only" not in sys.argv and os.environ.get("DEMO_TEST_ONLY") != "1":
        demo_app = tao_giao_dien_gradio()
        demo_app.launch()