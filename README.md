# 🔎 Sentiment & Aspect Classification for Vietnamese E-Commerce Reviews

<p align="center">
  <img src="https://img.shields.io/badge/BERT-Vietnamese-blue?logo=transformers" />
  <img src="https://img.shields.io/badge/BiLSTM-MultiTask-green?logo=pytorch" />
  <img src="https://img.shields.io/badge/Deployment-FastAPI-red?logo=fastapi" />
</p>

Hệ thống phâng ph\xe2n tíng ph\xe2n t\xedch cảm xúm x\xfac vàm x\xfac v\xe0 nhận diện khín kh\xeda cạnh từ bì b\xecnh luận người dùi d\xf9ng trêi d\xf9ng tr\xean Tiki vài d\xf9ng tr\xean Tiki v\xe0 Lazada. Môi d\xf9ng tr\xean Tiki v\xe0 Lazada. M\xf4 hìi d\xf9ng tr\xean Tiki v\xe0 Lazada. M\xf4 h\xecnh kết hợp **PhoBERT** vàp **PhoBERT** v\xe0 **BiLSTM**, huấn luyện theo hướng **Multi-task Learning**:

* Phâ- Ph\xe2n loại cảm xúm x\xfac: `tiêm x\xfac: `ti\xeau cực`, `trung tíc`, `trung t\xednh`, `tíc`, `trung t\xednh`, `t\xedch cực\`
* Nhận diện 5 khín 5 kh\xeda cạnh: `sản phẩm`, `giám`, `gi\xe1 cả`, `vận chuyển`, `thán`, `th\xe1i độ & dịch vụ`, `khá`, `kh\xe1c`

---

## 📌 Tí T\xednh Năng Chíng Ch\xednh

* ✅ Tự động crawl review từ Tiki & Lazada
* ✅ Gê G\xean nhã G\xean nh\xe3n bằng LLM (Groq API + DeepSeek LLaMA)
* ✅ Huấn luyện môn m\xf4 hìn m\xf4 h\xecnh đa táa t\xe1c vụ (emotion + aspects)
* ✅ Triển khai FastAPI + HuggingFace Transformers
* ✅ Biểu đồ: confusion matrix, loss/accuracy
* ✅ Checkpoint + early stopping + threshold tuning

---

## 📁 Cấu Trúu Tr\xfac Dự á \xe1n

```
DATN_Classification/
├── API_labelling/              # Gê├── API_labelling/              # G\xean nhã├── API_labelling/              # G\xean nh\xe3n qua Groq API
│   ├── API_labelling/         # Script gọi API + lưu JSON
│   └── Data/                  # File input/output sau gê│   └── Data/                  # File input/output sau g\xean nhã│   └── Data/                  # File input/output sau g\xean nh\xe3n
│
├── Crawl_and_Preprocessing/   # Crawl + Tiền xử lý l\xfd
│   ├── Crawl/                 # Crawler cho Tiki + Lazada
│   ├── Data/                  # Review thu thập
│   └── Preprocessing/        # Làm sạch + encode + balance
│
├── Deploy/                    # Triển khai FastAPI
│   └── main.py, templates/, static/
│
├── Train_model/               # Huấn luyện môn m\xf4 hìn m\xf4 h\xecnh
│   └── Build.ipynb
└── .gitattributes
```

## 🔍 Pipeline Xử Lý L\xfd

### 1. 📂 Crawl Dữ Liệu

* **Tiki**: Gọi Public API qua `requests`
* **Lazada**: Sử dụng `Selenium` + `ChromeDriver`, click + scroll + xử lý CAPTCHA giả lập

### 2. 🤖 Gê G\xean Nhã G\xean Nh\xe3n Bằng LLM

* **Model**: `deepseek-r1-distill-llama-70b` (qua Groq API)
* **Batch**: 5 review/lần gọi, nhận về danh sá danh s\xe1ch nhã danh s\xe1ch nh\xe3n
* **Output**: JSON \[\[emotion, sp, giá- **Output**: JSON \[\[emotion, sp, gi\xe1, vc, dv, khac], ...]

> ⚠️ Cần đăng kýng k\xfd Groq API key: [https://console.groq.com](https://console.groq.com)

### 3. ⚖️ Tiền Xử Lý L\xfd

* Lọc dòc d\xf2ng rác d\xf2ng r\xe1c / trống / không / kh\xf4ng hợp lệ
* Chuẩn hón h\xf3a text: xón h\xf3a text: x\xf3a HTML, kýn h\xf3a text: x\xf3a HTML, k\xfd tự lạ
* Encode nhã- Encode nh\xe3n (label encoder + map)
* Tí- T\xednh `class_weight` (emotion) + `pos_weight` (binary)

### 4. 📈 Huấn Luyện Môn M\xf4 Hìn M\xf4 H\xecnh

* **Kiến trún tr\xfac**: PhoBERT → BiLSTM → FC head (emotion + aspects)
* **Loss**:

  * CrossEntropyLoss (label\_smoothing=0.1)
  * BCEWithLogitsLoss (có  - BCEWithLogitsLoss (c\xf3 pos\_weight)
* **Sampler**: `StratifiedBatchSampler` (batch đều đủ class)
* **Optimizer**: AdamW (lr=1e-5, weight\_decay=0.05)
* **Scheduler**: Linear warmup
* **Gradient clipping**: 1.5
* **Metric**: F1 macro (emotion), F1 binary (aspects)
* **Threshold tuning**: Dò- **Threshold tuning**: D\xf2 search threshold F1 cao nhất

### 5. 🚀 Triển Khai API

* **FastAPI backend**

  * `GET /`: Giao diện HTML nhập bìp b\xecnh luận
  * `POST /predict`: Gọi text → tokenizer → model → nhã nh\xe3n dự đoáo\xe1n
* \*\*Tí- **T\xednh năng**: Load PhoBERT + BiLSTM, apply threshold, trả về nhã nh\xe3n cuối

---

## 📊 Kết Quả

\| Nhã| Nh\xe3n       | Accuracy | Precision | Recall | F1‑score |
\| ------------ | -------- | --------- | ------ | --------- |
\| Cảm xúm x\xfac    | 0.87     | 0.85      | 0.86   | 0.86      |
\| Sản phẩm   | 0.91     | 0.88      | 0.92   | 0.90      |
\| Giá| Gi\xe1 cả     | 0.92     | 0.85      | 0.87   | 0.86      |
\| Vận chuyển | 0.90     | 0.83      | 0.84   | 0.83      |
\| Dịch vụ     | 0.94     | 0.88      | 0.86   | 0.87      |
\| Khá| Kh\xe1c        | 0.95     | 0.89      | 0.84   | 0.86      |

---

## 📚 Tà T\xe0i Liệu Tham Khảo

* [PhoBERT: Pre-trained Language Models for Vietnamese (NAACL 2021)](https://arxiv.org/abs/2003.00744)
* [Groq API Documentation](https://console.groq.com/docs)
* [FastAPI Documentation](https://fastapi.tiangolo.com/)
* [PyTorch Multi-Task Learning Tutorial](https://pytorch.org/tutorials/beginner/basics/optimization_tutorial.html)

---

## ✨ Đóng Góng G\xf3p & Phíng G\xf3p & Ph\xedt Triển

* 🔄 Fork và Fork v\xe0 PR để nâ n\xe2ng cấp môp m\xf4 hìp m\xf4 h\xecnh
* 📝 Tạo issue báo issue b\xe1o lỗi, bug, UI/UX
* ⚛️ Gó G\xf3p ý G\xf3p \xfd cho chiến lược training, dữ liệu

---

## 📧 Liê Li\xean Hệ

* 💼 Tá T\xe1c giả: **An Đức Thanh**
* 📩 Email: [anthanh8573@gmail.com](mailto:anthanh8573@gmail.com)
* 📍 Đồ á \xe1n tốt nghiệp, Khoa CNTT, Trường ĐH GTVT, 2025
