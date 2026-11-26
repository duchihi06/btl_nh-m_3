# Đề tài 3: Dự báo lưu lượng giao thông theo giờ (UCI Metro Interstate Traffic Volume)

**Học phần:** Phân tích Dữ liệu lớn – **Nhóm 3** (GVHD: ThS. Đỗ Mạnh Quang)

## Cấu trúc thư mục dự án (Giai đoạn 1 → 3: EDA, Tiền xử lý & Mô hình hóa)

```text
btl_nhom_3_den_note_03/
├── code/
│   ├── note_01.ipynb       # Thu thập, khảo sát dữ liệu thô & 5 biểu đồ EDA
│   ├── note_02.ipynb       # Làm sạch 6 bước & tạo Bộ đặc trưng A (23 biến), Bộ B (26 biến)
│   └── note_03.ipynb       # Chia Train/Test theo thời gian, đối sánh 5 mô hình, tối ưu XGBoost & phân tích lỗi
├── data/
│   ├── raw/                # Dữ liệu gốc metro_interstate_traffic_volume.csv (48.204 dòng × 9 cột)
│   └── processed/          # Dữ liệu sạch clean_data.parquet (34.833 dòng × 30 cột) & clean_data.json
├── figures/                # Các biểu đồ EDA, ma trận tương quan và biểu đồ đánh giá mô hình
├── models/                 # Mô hình XGBoost đã huấn luyện và tinh chỉnh (.joblib)
└── results/                # Bảng kết quả đối sánh Bộ A vs Bộ B và tinh chỉnh siêu tham số (.csv)
```

## Thứ tự chạy thực nghiệm
1. Chạy `code/note_01.ipynb`: Khảo sát chất lượng dữ liệu và xuất 5 hình EDA vào `figures/`.
2. Chạy `code/note_02.ipynb`: Thực hiện 6 bước làm sạch, trích xuất đặc trưng và xuất `clean_data.parquet`, `clean_data.json`.
3. Chạy `code/note_03.ipynb`: Huấn luyện, tinh chỉnh siêu tham số `XGBoost` (`RandomizedSearchCV` + `TimeSeriesSplit`), phân tích lỗi và lưu mô hình vào `models/`.
