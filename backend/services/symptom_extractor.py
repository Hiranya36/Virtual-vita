import pandas as pd
import os
import re


class SymptomExtractor:

    def __init__(self):

        dataset_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "dataset",
            "dataset.csv"
        )

        df = pd.read_csv(dataset_path)

        symptoms = set()

        # collect symptoms
        for symptom_list in df["symptoms"].dropna():

            items = symptom_list.lower().split(",")

            for s in items:
                symptoms.add(s.strip())

        # sort symptoms by length (longer first)
        self.symptoms = sorted(list(symptoms), key=len, reverse=True)


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