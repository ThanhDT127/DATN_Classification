from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
import uvicorn
from huggingface_hub import hf_hub_download
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
HF_REPO = "ThanhDT127/pho-bert-bilstm"
HF_FILE  = "best_model_1.pth"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, HF_FILE)

if not os.path.exists(MODEL_PATH):
    os.makedirs("models", exist_ok=True)
    print("Downloading model from Hugging Face Hub…")
    MODEL_PATH = hf_hub_download(
      repo_id=HF_REPO,
      filename=HF_FILE,
      cache_dir="models",     
      force_filename=HF_FILE,
      token=HF_TOKEN 
    )

class TextInput(BaseModel):
    text: str

class BertBiLSTMClassifier(nn.Module):
    def __init__(self, bert_model_name, num_emotion_classes, binary_cols, lstm_hidden_size=256, dropout=0.3):
        super().__init__()
        self.bert = AutoModel.from_pretrained(bert_model_name)
        self.lstm = nn.LSTM(
            input_size=self.bert.config.hidden_size,
            hidden_size=lstm_hidden_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        self.dropout = nn.Dropout(dropout)
        self.emotion_fc = nn.Linear(lstm_hidden_size * 2, num_emotion_classes)
        self.binary_fcs = nn.ModuleDict({
            col: nn.Linear(lstm_hidden_size * 2, 1)
            for col in binary_cols
        })

    def forward(self, input_ids, attention_mask):
        bert_out = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        seq_out = bert_out.last_hidden_state
        lstm_out, _ = self.lstm(seq_out)
        last_hidden = lstm_out[:, -1, :]
        dropped = self.dropout(last_hidden)
        emo_logits = self.emotion_fc(dropped)
        bin_logits = {
            col: self.binary_fcs[col](dropped).squeeze(-1)
            for col in self.binary_fcs
        }
        return emo_logits, bin_logits


tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
binary_cols = [
    'sản phẩm', 'giá cả', 'vận chuyển',
    'thái độ và dịch vụ khách hàng', 'khác'
]
model = BertBiLSTMClassifier(
    bert_model_name="vinai/phobert-base",
    num_emotion_classes=3,
    binary_cols=binary_cols,
    lstm_hidden_size=256
).to(device)

model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()

threshold_dict = {
    'sản phẩm': 0.6,
    'giá cả': 0.4,
    'vận chuyển': 0.45,
    'thái độ và dịch vụ khách hàng': 0.35,
    'khác': 0.4
}

def predict(text: str):
    enc = tokenizer(
        text, add_special_tokens=True, max_length=128,
        padding='max_length', truncation=True, return_tensors='pt'
    )
    input_ids = enc['input_ids'].to(device)
    attention_mask = enc['attention_mask'].to(device)
    with torch.no_grad():
        emo_logits, bin_logits = model(input_ids, attention_mask)
        emo_pred = torch.argmax(emo_logits, dim=1).item()
        bin_pred = {
            col: (torch.sigmoid(bin_logits[col]) > threshold_dict[col]).float().item()
            for col in binary_cols
        }
    emo_label = ['tiêu cực', 'trung tính', 'tích cực'][emo_pred]
    bin_labels = {col: ('có' if bin_pred[col] == 1 else 'không') for col in binary_cols}
    return emo_label, bin_labels

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/predict")
async def predict_text(input: TextInput):
    emotion, binary = predict(input.text)
    return {"emotion": emotion, "binary": binary}

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))  
    uvicorn.run("main:app", host="0.0.0.0", port=port)