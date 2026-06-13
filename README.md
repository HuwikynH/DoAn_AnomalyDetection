# ĐỒ ÁN: PHÁT HIỆN BẤT THƯỜNG TRONG LOG VÀ NETWORK TRAFFIC

## 1. Tổng quan dự án

Đây là hệ thống giám sát an ninh mạng theo thời gian thực (Real-time Cybersecurity Monitoring System), được xây dựng dựa trên kiến trúc **Streaming Pipeline đa luồng** nhằm phân tích đồng thời dữ liệu **Network Traffic** và **System Log**.

Dự án ứng dụng phương pháp **Học máy không giám sát (Unsupervised Learning)** thông qua các mô hình Autoencoder để tự động phát hiện các hành vi bất thường chưa từng xuất hiện trong dữ liệu. Cơ chế phát hiện dựa trên việc đánh giá **Reconstruction Error (Sai số tái tạo)** giữa dữ liệu đầu vào và dữ liệu được mô hình tái tạo lại.

Hệ thống bao gồm:
- Deep Autoencoder phát hiện bất thường trong lưu lượng mạng.
- LSTM Autoencoder phân tích và phát hiện bất thường trong nhật ký hệ thống.
- Cơ chế Dynamic Threshold tự động xác định ngưỡng cảnh báo.
- Streaming Pipeline mô phỏng quá trình xử lý dữ liệu thời gian thực.
- Theo dõi hiệu năng hệ thống thông qua Latency và Memory Usage.

---

## 2. Cấu trúc thư mục

```
DOAN_1506/
│
├── dataset/
│   ├── Friday-WorkingHours-Afternoon-DDoS.pcap_ISCX.csv
│   └── HDFS_2k.log_structured.csv
│
├── MachineLearningCSV/
│   ├── Friday-WorkingHours-Afternoon-DDoS.pcap_ISCX.csv
│   ├── Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv
│   ├── Friday-WorkingHours-Morning.pcap_ISCX.csv
│   ├── Monday-WorkingHours.pcap_ISCX.csv
│   ├── Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv
│   ├── Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv
│   ├── Tuesday-WorkingHours.pcap_ISCX.csv
│   └── Wednesday-workingHours.pcap_ISCX.csv
│
├── models/
│   ├── deep_autoencoder_traffic.h5
│   └── lstm_autoencoder_logs.h5
│
├── DoAn_Tong.ipynb
└── README.md
```

### Mô tả thành phần

| Thành phần | Mô tả |
|---|---|
| `DoAn_Tong.ipynb` | Tệp mã nguồn chính chứa toàn bộ thuật toán Streaming Pipeline, xử lý đa luồng, cơ chế Dynamic Threshold và giám sát hiệu năng. |
| `models/` | Thư mục chứa các mô hình AI đã được huấn luyện sẵn. |
| `deep_autoencoder_traffic.h5` | Mô hình Deep Autoencoder dùng để phát hiện bất thường trong Network Traffic. |
| `lstm_autoencoder_logs.h5` | Mô hình LSTM Autoencoder dùng để phân tích và phát hiện bất thường trong System Log. |
| `dataset/` | Chứa dữ liệu đầu vào phục vụ quá trình mô phỏng phát hiện bất thường thời gian thực. |
| `MachineLearningCSV/` | Lưu trữ toàn bộ dữ liệu gốc của bộ CICIDS2017 phục vụ mục đích tham khảo và mở rộng nghiên cứu, không tham gia trực tiếp vào quá trình chạy hệ thống. |

---

## 3. Yêu cầu môi trường

### Phiên bản đề xuất
- Python 3.10 trở lên
- Visual Studio Code với Jupyter Extension

### Cài đặt thư viện

Mở Terminal và chạy lệnh:

```bash
pip install numpy pandas tensorflow scikit-learn psutil
```

---

## 4. Hướng dẫn khởi chạy

### Bước 1: Mở dự án

Mở thư mục dự án bằng **Visual Studio Code**.

### Bước 2: Mở Notebook

Mở tệp:

```
DoAn_Tong.ipynb
```

### Bước 3: Chọn môi trường Python

Chọn Python Kernel phù hợp (khuyến nghị Python 3.10 hoặc cao hơn).

### Bước 4: Chạy hệ thống

Nhấn **Run All** hoặc chạy toàn bộ các ô mã nguồn trong Notebook.

Sau khi khởi chạy, hệ thống sẽ tự động:

- Tải các mô hình AI đã huấn luyện.
- Đọc dữ liệu Network Traffic và System Log.
- Mô phỏng quá trình Streaming thời gian thực.
- Tính toán Dynamic Threshold dựa trên 100 mẫu ban đầu.
- Phát hiện và cảnh báo các mẫu bất thường.
- Hiển thị các thông số hiệu năng:
  - Latency (thời gian xử lý)
  - Memory Usage (mức sử dụng RAM)

### Dừng hệ thống

Nhấn nút **Interrupt Kernel** trên thanh công cụ của VS Code để dừng quá trình chạy.

---

## 5. Kiến trúc và kỹ thuật sử dụng

### Mô hình phát hiện bất thường

- **Deep Autoencoder**:
  - Phân tích các đặc trưng của lưu lượng mạng.
  - Học biểu diễn của dữ liệu bình thường.
  - Đánh dấu các mẫu có Reconstruction Error cao là bất thường.

- **LSTM Autoencoder**:
  - Phân tích chuỗi sự kiện trong nhật ký hệ thống.
  - Khai thác mối quan hệ theo thời gian giữa các log.
  - Phát hiện các hành vi khác biệt so với mẫu thông thường.

### Dynamic Threshold

Thay vì sử dụng ngưỡng cố định, hệ thống tự động tính ngưỡng dựa trên phân phối Reconstruction Error của 100 mẫu dữ liệu đầu tiên. Điều này giúp hệ thống có khả năng thích nghi với từng loại dữ liệu đầu vào khác nhau.

---

## 6. Tiến độ và phân công công việc

### Phần kỹ thuật (Đã hoàn thiện 100%)

- Hoàn thành tích hợp hai nguồn dữ liệu:
  - HDFS System Log.
  - CICIDS2017 Network Traffic.
- Xây dựng thành công kiến trúc Streaming Pipeline đa luồng.
- Triển khai mô hình Deep Autoencoder và LSTM Autoencoder.
- Áp dụng cơ chế Dynamic Threshold tự động.
- Đo lường hiệu năng hệ thống thông qua Latency và Memory Usage.
- Kiểm thử thành công trên các tập dữ liệu tấn công thực tế.

---

### Phần báo cáo và Slide (Cần tiếp tục hoàn thiện)

Các nội dung cần bổ sung:

- So sánh chi tiết giữa Supervised Learning và Unsupervised Learning trong bài toán phát hiện bất thường.
- Giải thích công thức toán học của Autoencoder và cơ chế tính toán Dynamic Threshold.
- Tổng hợp ảnh chụp màn hình quá trình kiểm thử.
- Hoàn thiện Slide thuyết trình phục vụ bảo vệ đồ án.

---

## 7. Bộ dữ liệu sử dụng

### CICIDS2017

Bộ dữ liệu mô phỏng các loại tấn công mạng phổ biến như:
- DDoS
- PortScan
- Web Attack
- Infiltration

Được sử dụng để đánh giá khả năng phát hiện bất thường của mô hình Deep Autoencoder.

### HDFS Log Dataset

Dữ liệu nhật ký hệ thống phân tán Hadoop HDFS, được sử dụng để huấn luyện và đánh giá mô hình LSTM Autoencoder trong bài toán phát hiện bất thường trên System Log.

---

## 8. Kết luận

Dự án xây dựng thành công một hệ thống giám sát an ninh mạng thời gian thực sử dụng các kỹ thuật học sâu không giám sát. Hệ thống có khả năng phát hiện bất thường trên cả lưu lượng mạng và nhật ký hệ thống, đồng thời tự thích nghi với dữ liệu thông qua cơ chế Dynamic Threshold và cung cấp các chỉ số đánh giá hiệu năng trong quá trình vận hành.