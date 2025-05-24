from huggingface_hub import HfApi

api = HfApi()
api.upload_file(
  path_or_fileobj="PhoBERT_BiLSTM/best_model_1.pth",
  path_in_repo="best_model_1.pth",
  repo_id="ThanhDT127/pho-bert-bilstm",
  repo_type="model",
  token=True               
)
print("Uploaded!")
