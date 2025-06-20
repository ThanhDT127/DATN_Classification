# 🔎 Sentiment & Aspect Classification for Vietnamese E-Commerce Reviews

<p align="center">
  <img src="https://img.shields.io/badge/BERT-Vietnamese-blue?logo=transformers" />
  <img src="https://img.shields.io/badge/BiLSTM-MultiTask-green?logo=pytorch" />
  <img src="https://img.shields.io/badge/Deployment-FastAPI-red?logo=fastapi" />
</p>

Dự án này xây dựng một hệ thống **phân loại cảm xúc** và **gán nhãn khía cạnh** từ các bình luận người dùng trên Tiki và Lazada. Mô hình học sâu kết hợp **PhoBERT** và **BiLSTM**, huấn luyện theo hướng **multi-task learning** để xử lý cùng lúc hai bài toán:

- Phân loại cảm xúc: `tiêu cực`, `trung tính`, `tích cực`
- Nhận diện 5 khía cạnh: `sản phẩm`, `giá cả`, `vận chuyển`, `thái độ & dịch vụ`, `khác`

## Bạn có thể thử nghiệp ngay với giao diện trên hugging face : 

https://huggingface.co/spaces/ThanhDT127/DATN

![image](https://github.com/user-attachments/assets/37698b07-2f7d-4c5a-89fa-81c98ec81c50)


## 📌 Tính Năng Chính

- ✅ Tự động crawl review từ Tiki & Lazada
- ✅ Gán nhãn bằng LLM (Groq API + DeepSeek LLaMA)
- ✅ Huấn luyện mô hình đa tác vụ (emotion + aspects)
- ✅ Triển khai với FastAPI + HuggingFace Transformers
- ✅ Visualization kết quả: ma trận nhầm lẫn, biểu đồ loss/accuracy
- ✅ Hỗ trợ checkpoint, early stopping, threshold tuning

---

## 📁 Cấu Trúc Dự Án
![image](https://github.com/user-attachments/assets/51f0e402-1c31-4088-9934-77a828b89c84)

### 🔍 Pipeline Xử Lý
#### 1. 📂 Crawl dữ liệu

* **Tiki**: Dùng Public API + `requests`
* **Lazada**: Dùng `Selenium` + `ChromeDriver` + xử lý CAPTCHA (fake user + scroll + xử lý DOM)
* 
#### 2. 🤖 Gán nhãn bằng LLM

* **Mô hình**: `deepseek-r1-distill-llama-70b` (qua Groq API)
* **Phân lô batch**: 5 comment/lần gọi
* **Output**: JSON danh sách nhãn dạng `[[emotion, sp, giá, v.chuyển, d.v, khác], ...]`
> ⚠️ Cần đăng ký Groq API key: [https://console.groq.com](https://console.groq.com)

#### 3. ⚖️ Tiền xử lý

* Loại dòng rỗng / comment lỗi / nhiễu whitespace
* Chuẩn hóa văn bản (xóa HTML, ký tự lạ)
* Encode nhãn (map + `LabelEncoder`), chuẩn hóa nhãn binary
* Tính **trọng số loss** cho nhãn imbalance (pos\_weight / class\_weight)
#### 4. 📈 Huấn luyện mô hình
* Kiến trúc: **PhoBERT → BiLSTM → Emotion FC + Multi Aspect FCs**
* Loss:

  * `CrossEntropyLoss(weight, label_smoothing=0.1)` cho emotion
  * `BCEWithLogitsLoss(pos_weight)` cho nhãn binary
* Sampler: `StratifiedBatchSampler` đảm bảo cân bằng batch theo class
* Tối ưu:

  * Optimizer: `AdamW(lr=1e-5, weight_decay=0.05)`
  * Scheduler: `get_linear_schedule_with_warmup`
  * Clip gradient: `clip_grad_norm_`
* Đánh giá: Macro-F1 cho emotion, binary-F1 cho khía cạnh, tune threshold cho mỗi nhãn

#### 5. 🚀 Triển khai API
* Backend: `FastAPI`
  * GET `/`: giao diện HTML + form Jinja2
  * POST `/predict`: nhận input, tokenize, dự đoán, decode nhãn
* Load PhoBERT + BiLSTM model, ngưỡng threshold được tinh chỉnh
* Gửi ra nhãn cảm xúc + danh mục nhị phân "có/không"

📊 Kết Quả Mô Hình

| Nhãn       | Accuracy | Precision | Recall | F1‑score |
| ---------- | -------- | --------- | ------ | -------- |
| Cảm xúc    | 0.87     | 0.85      | 0.86   | 0.86     |
| Sản phẩm   | 0.91     | 0.88      | 0.92   | 0.90     |
| Giá cả     | 0.92     | 0.90      | 0.92   | 0.91     |
| Vận chuyển | 0.90     | 0.89      | 0.90   | 0.89     |
| Thái độ/DV | 0.89     | 0.75      | 0.80   | 0.77     |
| Khác       | 0.85     | 0.72      | 0.68   | 0.70     |

📚 Tài Liệu Tham Khảo
* PhoBERT paper (NAACL 2021) 
* Groq API Docs
* FastAPI Docs
* PyTorch MultiTask Learning

✨ Đóng Góp & Phát Triển 
Mọi ý kiến đóng góp, báo lỗi hoặc cải tiến mô hình đều được chào đón. Bạn có thể:

-- Fork và mở PR

-- Tạo issue nếu gặp bug

-- Góp ý mô hình, hiệu năng hoặc trải nghiệm người dùng

📧 Liên Hệ :

💼 Tác giả: [An Đức Thanh]

📮 Email: anthanh8573@gmail.com

📌 Đồ án tốt nghiệp Khoa CNTT, Trường Đại Học Giao Thông Vận Tải, 2025
