import pandas as pd
import os

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

dataset_path = os.path.join(base_dir, "backend", "dataset", "dataset.csv")

data = pd.read_csv(dataset_path)

print("Dataset Loaded Successfully")
print(data.head())
print("Shape:", data.shape)