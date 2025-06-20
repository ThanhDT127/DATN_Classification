from transformers import AutoTokenizer, AutoModel

model = AutoModel.from_pretrained("vinai/phobert-base")
tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base", use_fast=False)

model.save_pretrained("D:/ktlt/python/thuchanh/DATN/DATN/tokenizer/phobert-base-fixed")
tokenizer.save_pretrained("D:/ktlt/python/thuchanh/DATN/DATN/tokenizer/phobert-base-fixed")
