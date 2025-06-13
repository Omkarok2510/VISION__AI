import os

# ABSOLUTE PATH SOLUTION (foolproof)
BASE_DIR = "/Users/dewangmagar/Desktop/ocr"  # ← Hardcoded for 100% accuracy
ERROR_DATASET_DIR = os.path.join(BASE_DIR, "ai", "error_dataset")
MODEL_DIR = os.path.join(BASE_DIR, "ai", "models")

print(f"CONFIG LOADED FROM: {os.path.abspath(__file__)}")
