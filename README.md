# Đồ án: Phát hiện bất thường trong log hệ thống và network traffic bằng Autoencoder

## 1. Thông tin nhóm

- Sinh viên: Nguyễn Hữu Huynh - N22DCCN135
- Sinh viên: Nguyễn Đức Lộc - N22DCCN150
- Đề tài: Phát hiện bất thường trong log hệ thống và network traffic đáp ứng thời gian thực bằng Autoencoder
- Giảng viên hướng dẫn: ThS. Đàm Minh Linh

## 2. Mục tiêu dự án

Dự án xây dựng một hệ thống demo giám sát bất thường theo thời gian thực, xử lý đồng thời hai nguồn dữ liệu:

- Network traffic từ bộ CICIDS2017.
- System log từ bộ HDFS log.

Hướng chính của đề tài là **unsupervised learning** bằng Autoencoder. Mô hình học cách tái tạo dữ liệu bình thường, sau đó phát hiện bất thường dựa trên **reconstruction error**. Nếu lỗi tái tạo lớn hơn ngưỡng động, mẫu được xem là anomaly.

Ngoài mô hình chính bằng Autoencoder, dự án có thêm một baseline **supervised Random Forest** để đáp ứng phần so sánh supervised vs unsupervised.

## 3. Yêu cầu của đề tài và trạng thái hiện tại

| Yêu cầu | Trạng thái |
|---|---|
| Phân tích gói tin kết hợp log | Đạt ở mức demo, có `Hybrid_Score` và `Hybrid_Status` |
| Pipeline streaming 3 thread | Đạt |
| Deep Autoencoder cho network traffic | Đạt |
| LSTM Autoencoder cho system log | Đạt |
| Tính reconstruction error realtime | Đạt |
| Đo latency và memory usage | Đạt |
| So sánh supervised vs unsupervised | Đạt, có Random Forest baseline |
| Phân tích dynamic threshold | Đạt |

## 4. Cấu trúc thư mục

```text
DoAn_1506/
├── backups/
├── dataset/
│   ├── Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
│   └── HDFS_2k.log_structured.csv
├── MachineLearningCSV/
│   └── Các file CICIDS2017 gốc để tham khảo/mở rộng
├── models/
│   ├── deep_autoencoder_traffic.h5
│   ├── traffic_scaler.pkl
│   ├── lstm_autoencoder_logs.h5
│   ├── log_scaler.pkl
│   └── random_forest_supervised_baseline.pkl
├── DoAn_Tong.ipynb
├── supervised_baseline_random_forest_kaggle.py
├── supervised_baseline_results.txt
├── supervised_baseline_metrics.json
├── system_alert_log.txt
└── README.md
```

## 5. Các file quan trọng

| File/thư mục | Vai trò |
|---|---|
| `DoAn_Tong.ipynb` | Notebook chính để chạy pipeline streaming local |
| `models/deep_autoencoder_traffic.h5` | Deep Autoencoder cho network traffic |
| `models/traffic_scaler.pkl` | Scaler của 47 feature traffic, không fit lại ở local |
| `models/lstm_autoencoder_logs.h5` | LSTM Autoencoder cho system log |
| `models/log_scaler.pkl` | Scaler của log feature, không fit lại ở local |
| `models/random_forest_supervised_baseline.pkl` | Model supervised baseline train trên Kaggle |
| `supervised_baseline_random_forest_kaggle.py` | Script train Random Forest supervised trên Kaggle |
| `supervised_baseline_results.txt` | Kết quả supervised baseline dạng text |
| `supervised_baseline_metrics.json` | Kết quả supervised baseline dạng JSON |
| `system_alert_log.txt` | Log realtime và summary của lần chạy local gần nhất |

## 6. Mô hình chính: Unsupervised Autoencoder

### 6.1. Traffic Deep Autoencoder

- Dataset train: `Monday-WorkingHours.pcap_ISCX.csv`
- Dữ liệu train: chỉ dùng traffic `BENIGN`
- Input: 47 feature CICIDS2017
- Tiền xử lý:
  - Strip tên cột.
  - Replace `inf/-inf` bằng `NaN`.
  - Drop `NaN`.
  - Clip outlier 1%-99%.
  - Scale bằng `MinMaxScaler`.
- Kiến trúc:
  - Input 47
  - Dense 128
  - Dense 64
  - Dense 32
  - Bottleneck 16
  - Dense 32
  - Dense 64
  - Dense 128
  - Output 47 sigmoid

### 6.2. Log LSTM Autoencoder

- Dataset train: `HDFS_2k.log_structured.csv`
- Input shape: `10 timestep x 4 feature`
- Feature log:
  - `EventId_num`
  - `Level_num`
  - `Component_num`
  - `Pid_norm`
- Kiến trúc:
  - LSTM 32
  - RepeatVector 10
  - LSTM 32
  - TimeDistributed Dense 4

## 7. Adaptive dynamic threshold

Hệ thống dùng ngưỡng động theo 2 tầng:

```text
threshold = mean(MSE_calibration) + 3 * std(MSE_calibration)
```

Trong runtime local:

- Tầng 1: Traffic dùng 100 mẫu `BENIGN` đầu để tạo threshold ban đầu.
- Tầng 1: Log dùng 100 sequence đầu để tạo threshold ban đầu.
- Tầng 2: Khi streaming đang chạy, threshold tiếp tục được cập nhật bằng rolling window 100 MSE mới nhất.

Quy tắc cập nhật rolling threshold:

```text
Sau mỗi sample:
    đưa MSE mới vào rolling_window
    chỉ giữ lại 100 MSE mới nhất
    threshold_mới = mean(rolling_window) + 3 * std(rolling_window)
```

Trong `system_alert_log.txt`, mỗi dòng sẽ có thêm:

- `Traffic_Threshold`
- `Log_Threshold`

Cuối log sẽ có:

- `Initial Traffic Threshold`
- `Final Traffic Threshold`
- `Traffic Threshold Updates`
- `Initial Log Threshold`
- `Final Log Threshold`
- `Log Threshold Updates`

## 8. Pipeline streaming

Notebook chính triển khai 3 thread:

| Thread | Vai trò |
|---|---|
| `packet_analysis_stream` | Đọc từng flow traffic, đưa vào `traffic_queue` |
| `log_ingestion_stream` | Đọc từng sequence log, đưa vào `log_queue` |
| `hybrid_model_inference` | Lấy dữ liệu từ queue, chạy model, tính MSE, đo latency/RAM, ghi log |

Hệ thống tự dừng khi đã xử lý hết dữ liệu traffic và log trong dataset demo.

## 9. Hybrid traffic + log

Vì CICIDS2017 và HDFS là hai dataset độc lập, bản demo chưa correlation thật theo timestamp/IP/process. Để đáp ứng phần kết hợp gói tin và log, hệ thống dùng quyết định hybrid trong cùng pipeline streaming:

```text
traffic_score = traffic_mse / traffic_threshold
log_score = log_mse / log_threshold
hybrid_score = max(traffic_score, log_score)
hybrid_status = ANOMALY nếu traffic hoặc log bất thường
```

Trong `system_alert_log.txt`, mỗi dòng có:

- `Traffic_MSE`
- `Traffic_Status`
- `Log_MSE`
- `Log_Status`
- `Hybrid_Score`
- `Hybrid_Status`
- `Latency_ms`
- `RAM_MB`

## 10. Kết quả chạy local gần nhất

Kết quả lấy từ `system_alert_log.txt`:

| Chỉ số | Giá trị |
|---|---:|
| Total Traffic Processed | 2000 |
| Total Log Sequences Processed | 2000 |
| Traffic Alerts | 1243 |
| Traffic Anomaly Rate | 62.15% |
| Actual Attack Flows | 1900 |
| Detected Attack Flows | 1240 |
| Detection Rate | 65.26% |
| False Positive | 3 |
| False Positive Rate | 3.00% |
| Log Alerts | 10 |
| Log Anomaly Rate | 0.50% |
| Hybrid Alerts | 1248 |
| Hybrid Anomaly Rate | 62.40% |
| Both Traffic and Log Alerts | 5 |
| Total Runtime | 142.77 seconds |
| Average Latency | 71.24 ms |
| Max Latency | 354.04 ms |
| Average RAM | 629.21 MB |
| Peak RAM | 629.40 MB |

Adaptive threshold summary:

| Chỉ số | Giá trị |
|---|---:|
| Initial Traffic Threshold | 0.00044971 |
| Final Traffic Threshold | 0.00035481 |
| Traffic Threshold Updates | 757 |
| Initial Log Threshold | 0.05503221 |
| Final Log Threshold | 0.05744186 |
| Log Threshold Updates | 1990 |

## 11. Supervised baseline để so sánh

File `supervised_baseline_random_forest_kaggle.py` dùng để train một mô hình supervised baseline trên Kaggle.

Mục đích của file này:

- Đọc dataset CICIDS2017 Friday DDoS.
- Dùng cùng 47 feature traffic với Autoencoder.
- Dùng cột `Label` làm nhãn:
  - `BENIGN = 0`
  - `ATTACK = 1`
- Train `RandomForestClassifier`.
- Xuất kết quả để đưa vào phần so sánh supervised vs unsupervised.

Kết quả supervised baseline:

| Chỉ số | Giá trị |
|---|---:|
| Model | RandomForestClassifier |
| Feature count | 47 |
| Train samples | 157997 |
| Test samples | 67714 |
| Accuracy | 0.999705 |
| Precision | 0.999896 |
| Recall | 0.999583 |
| F1-score | 0.999740 |
| Confusion matrix | `[[29302, 4], [16, 38392]]` |

## 12. Vì sao Autoencoder vẫn là unsupervised dù log có Label?

Trong `system_alert_log.txt` có dòng như:

```text
Label=DDoS | Traffic_MSE=... | Traffic_Status=ANOMALY
```

Điều này không làm Autoencoder thành supervised.

Khác biệt nằm ở cách dùng label:

| Mô hình | Label được dùng để làm gì? |
|---|---|
| Autoencoder unsupervised | Không dùng label để train/inference. Label chỉ dùng để đối chiếu kết quả demo và tính detection rate |
| Random Forest supervised | Dùng label trực tiếp để train mô hình phân loại `BENIGN/ATTACK` |

Nói ngắn gọn:

```text
Autoencoder: 47 feature -> reconstruct -> MSE -> threshold -> anomaly
Random Forest: 47 feature + Label -> học phân loại BENIGN/ATTACK
```

## 13. Hướng dẫn chạy demo local

### Bước 1: Mở project

Mở thư mục:

```text
C:\Users\huuhu\Desktop\DoAn_1506
```

### Bước 2: Mở notebook

Mở file:

```text
DoAn_Tong.ipynb
```

### Bước 3: Chọn kernel

Chọn kernel Python đang dùng cho project, ví dụ:

```text
streaming_ai (Python 3.10.x)
```

### Bước 4: Chạy toàn bộ notebook

Nhấn `Run All`.

Khi chạy đúng, notebook sẽ:

- Load 2 Autoencoder model bằng `compile=False`.
- Load 2 scaler `.pkl`.
- Calibration dynamic threshold bằng 100 mẫu đầu.
- Cập nhật adaptive threshold bằng rolling window trong lúc streaming.
- Chạy 3 thread streaming.
- In trạng thái realtime.
- Ghi log vào `system_alert_log.txt`.
- Tự dừng sau khi xử lý xong dữ liệu.
- In `FINAL SYSTEM SUMMARY`.

## 14. Lưu ý quan trọng khi chạy

- Không fit scaler mới ở local.
- Luôn load:
  - `models/traffic_scaler.pkl`
  - `models/log_scaler.pkl`
- Traffic phải dùng đúng 47 feature và đúng thứ tự như lúc train.
- `Label` chỉ dùng để đánh giá demo, không đưa vào Autoencoder.
- Nếu load `.h5` lỗi `quantization_config`, notebook đã có hàm load model tương thích để xử lý.

## 15. Cách nói khi bảo vệ

Câu tóm tắt ngắn:

> Đề tài của nhóm em xây dựng pipeline streaming 3 thread để xử lý song song network traffic và system log. Mô hình chính là Deep Autoencoder cho traffic và LSTM Autoencoder cho log. Hai mô hình được train theo hướng unsupervised, không dùng nhãn attack để học, mà phát hiện anomaly bằng reconstruction error và dynamic threshold. Nhóm em cũng bổ sung Random Forest supervised baseline để so sánh với Autoencoder.

Nếu bị hỏi vì sao supervised cao hơn:

> Random Forest có kết quả cao vì được học trực tiếp từ nhãn BENIGN/ATTACK trên cùng phân phối dữ liệu DDoS. Autoencoder không cần nhãn attack khi train nên phù hợp hơn trong tình huống thiếu nhãn hoặc muốn phát hiện bất thường chưa biết, nhưng độ chính xác phụ thuộc nhiều vào threshold và độ khác biệt của attack so với traffic bình thường.

Nếu bị hỏi hạn chế:

> Demo hiện mô phỏng realtime bằng CSV, chưa bắt packet live từ card mạng. Traffic CICIDS2017 và log HDFS là hai dataset độc lập nên chưa correlation thật theo timestamp/IP/process. Phần kết hợp hiện được triển khai bằng Hybrid_Status trong cùng pipeline streaming.

## 16. Hướng phát triển

- Bổ sung live packet capture bằng Scapy hoặc tshark.
- Dùng dataset traffic-log đồng bộ timestamp để correlation thật.
- Lưu riêng encoder cho log preprocessing.
- Thử thêm threshold percentile hoặc so sánh nhiều kích thước rolling window khác nhau.
- Thử thêm các supervised baseline khác như SVM, Logistic Regression hoặc XGBoost.
