import os

os.environ.setdefault("HF_HOME", "/app/hf_cache")

import logging
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
import uvicorn
from huggingface_hub import hf_hub_download


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
HF_REPO = "ThanhDT127/pho-bert-bilstm"
HF_FILE = "best_model_1.pth"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, HF_FILE)


try:
    if not os.path.isfile(MODEL_PATH):
        logger.info("Downloading model from Hugging Face Hub")
        MODEL_PATH = hf_hub_download(
            repo_id=HF_REPO,
            filename=HF_FILE,
            cache_dir=os.environ["HF_HOME"],
            force_filename=HF_FILE,
            token=HF_TOKEN
        )
    logger.info("Loading model from %s", MODEL_PATH)
    model_state_dict = torch.load(MODEL_PATH, map_location=device)
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error("Error loading model: %s", str(e))
    raise

class TextInput(BaseModel):
    text: str

class BertBiLSTMClassifier(nn.Module):
    def __init__(self, bert_model_name, num_emotion_classes, binary_cols, lstm_hidden_size=128, dropout=0.4):
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

tokenizer = AutoTokenizer.from_pretrained(
    "vinai/phobert-base",
    use_fast=False,
    cache_dir=os.environ["HF_HOME"]
)
binary_cols = [
    'sản phẩm', 'giá cả', 'vận chuyển',
    'thái độ và dịch vụ khách hàng', 'khác'
]
model = BertBiLSTMClassifier(
    bert_model_name="vinai/phobert-base",
    num_emotion_classes=3,
    binary_cols=binary_cols,
    lstm_hidden_size=128
).to(device)

# Load model state dict
model.load_state_dict(model_state_dict)
model.eval()

threshold_dict = {
    'sản phẩm': 0.28,
    'giá cả': 0.58,
    'vận chuyển': 0.58,
    'thái độ và dịch vụ khách hàng': 0.70,
    'khác': 0.6
}

def predict(text: str):
    logger.info("Starting prediction for text: %s", text)
    try:
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
        logger.info("Prediction completed: emotion=%s, binary=%s", emo_label, bin_labels)
        return emo_label, bin_labels
    except Exception as e:
        logger.error("Error during prediction: %s", str(e))
        raise

@app.get("/")
async def read_root(request: Request):
    logger.info("Received GET request for /")
    try:
        response = templates.TemplateResponse("index.html", {"request": request})
        logger.info("Successfully rendered index.html")
        return response
    except Exception as e:
        logger.error("Error rendering index.html: %s", str(e))
        raise

@app.post("/predict")
async def predict_text(input: TextInput):
    logger.info("Received POST request for /predict with input: %s", input.text)
    try:
        emotion, binary = predict(input.text)
        logger.info("Sending prediction response: emotion=%s, binary=%s", emotion, binary)
        return {"emotion": emotion, "binary": binary}
    except Exception as e:
        logger.error("Error in predict_text endpoint: %s", str(e))
        raise

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info("Starting Uvicorn server on port %d", port)
    uvicorn.run("main:app", host="0.0.0.0", port=port)