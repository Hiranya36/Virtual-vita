import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "default-secret-key")
    MODEL_WEIGHTS_PATH = os.environ.get("MODEL_WEIGHTS_PATH", "model_weights/disease_model.pkl")
    DATASET_PATH = os.environ.get("DATASET_PATH", "dataset/dataset.csv")
