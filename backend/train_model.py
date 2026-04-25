import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

base_dir = os.path.dirname(__file__)
cleaned_dataset_path = os.path.join(base_dir, "dataset", "dataset_cleaned.csv")
dataset_path = cleaned_dataset_path if os.path.exists(cleaned_dataset_path) else os.path.join(base_dir, "dataset", "dataset.csv")

print("Loading dataset...")
df = pd.read_csv(dataset_path)

# Extract all unique symptoms
all_symptoms = set()
for col in df.columns[1:]:
    unique_vals = df[col].dropna().unique()
    for val in unique_vals:
        clean_val = str(val).strip().replace('_', ' ').lower()
        all_symptoms.add(clean_val)

all_symptoms = sorted(list(all_symptoms))
symptom_to_idx = {symptom: idx for idx, symptom in enumerate(all_symptoms)}
print(f"Total unique symptoms found: {len(all_symptoms)}")

# Create feature matrix (X) and labels (Y)
print("Building feature matrix...")
X = []
Y = []

for idx, row in df.iterrows():
    vector = [0] * len(all_symptoms)
    for col in df.columns[1:]:
        val = row[col]
        if pd.notna(val):
            clean_val = str(val).strip().replace('_', ' ').lower()
            v_idx = symptom_to_idx.get(clean_val)
            if v_idx is not None:
                vector[v_idx] = 1
    X.append(vector)
    # Disease names might have trailing spaces
    disease_clean = str(row['Disease']).strip()
    Y.append(disease_clean)

X = np.array(X)
Y = np.array(Y)

print("Training Random Forest Classifier (The Doctor Brain)...")
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X, Y)
print(f"Training accuracy: {rf.score(X, Y)*100:.2f}%")

# Save model and symptom list
model_dir = os.path.join(base_dir, "model_weights")
os.makedirs(model_dir, exist_ok=True)

joblib.dump(rf, os.path.join(model_dir, "disease_model.pkl"))
joblib.dump(all_symptoms, os.path.join(model_dir, "all_symptoms.pkl"))
joblib.dump(list(np.unique(Y)), os.path.join(model_dir, "diseases.pkl"))

print(f"Model and symptoms successfully saved to {model_dir}")
