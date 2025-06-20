# 🔎 Sentiment & Aspect Classification for Vietnamese E-Commerce Reviews

<p align="center">
  <img src="https://img.shields.io/badge/BERT-Vietnamese-blue?logo=transformers" />
  <img src="https://img.shields.io/badge/BiLSTM-MultiTask-green?logo=pytorch" />
  <img src="https://img.shields.io/badge/Deployment-FastAPI-red?logo=fastapi" />
</p>

Dự án này xây dựng một hệ thống **phân loại cảm xúc** và **gán nhãn khía cạnh** từ các bình luận người dùng trên Tiki và Lazada. Mô hình học sâu kết hợp **PhoBERT** và **BiLSTM**, huấn luyện theo hướng **multi-task learning** để xử lý cùng lúc hai bài toán:

- Phân loại cảm xúc: `tiêu cực`, `trung tính`, `tích cực`
- Nhận diện 5 khía cạnh: `sản phẩm`, `giá cả`, `vận chuyển`, `thái độ & dịch vụ`, `khác`
