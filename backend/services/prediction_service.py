import pickle
import os


class DiseasePredictor:

    def __init__(self):
        model_path = os.path.join("model_weights", "disease_model.pkl")
        self.model = pickle.load(open(model_path, "rb"))

        self.all_symptoms = [
            "fever", "headache", "vomiting",
            "cough", "fatigue", "chest pain"
        ]

    def create_vector(self, symptoms):
        vector = [0] * len(self.all_symptoms)

        for s in symptoms:
            if s in self.all_symptoms:
                index = self.all_symptoms.index(s)
                vector[index] = 1

        return vector

    def predict(self, symptoms):
        vector = self.create_vector(symptoms)
        result = self.model.predict([vector])[0]

        # simple mapping (you can improve later)
        return {
            "disease": str(result),
            "doctor": "General Physician",
            "risk_level": "Medium",
            "treatment": "Consult doctor, rest, stay hydrated"
        }