import pandas as pd

df = pd.read_csv("backend/dataset/dataset.csv")

print(df["disease"].value_counts().head(10))