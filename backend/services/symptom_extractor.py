import pandas as pd
import os
import re


class SymptomExtractor:

    def __init__(self, dataset_path=None):
        if dataset_path is None:
            dataset_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "dataset",
                "dataset.csv"
            )

        try:
            df = pd.read_csv(dataset_path)

            symptoms = set()

            if "symptoms" in df.columns:
                # collect symptoms from normalized text column
                for symptom_list in df["symptoms"].dropna():
                    items = str(symptom_list).lower().split(",")
                    for s in items:
                        clean = s.strip().replace("_", " ")
                        if clean:
                            symptoms.add(clean)
            else:
                # fallback for wide format: Symptom_1 ... Symptom_n
                symptom_columns = [c for c in df.columns if c.lower().startswith("symptom_")]
                for col in symptom_columns:
                    for val in df[col].dropna():
                        clean = str(val).strip().replace("_", " ").lower()
                        if clean:
                            symptoms.add(clean)

            # sort symptoms by length (longer first)
            self.symptoms = sorted(list(symptoms), key=len, reverse=True)
        except Exception as e:
            print(f"Warning: Could not load dataset from {dataset_path}: {e}")
            self.symptoms = []

    def extract(self, text):

        text = text.lower()

        detected = []

        for symptom in self.symptoms:

            pattern = r'\b' + re.escape(symptom) + r'\b'

            if re.search(pattern, text):

                # avoid detecting smaller symptoms inside bigger ones
                if not any(symptom in d for d in detected):
                    detected.append(symptom)

        return detected
