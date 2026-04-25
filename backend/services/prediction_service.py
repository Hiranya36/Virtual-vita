import os
import joblib
import pandas as pd

class DiseasePredictor:
    # Pre-translated headers for medical assessments
    TRANSLATIONS = {
        "preliminary_assessment": {"en": "Preliminary Assessment", "te": "ప్రాథమిక అంచనా"},
        "suggested_doctor": {"en": "Suggested Doctor", "te": "సిఫార్సు చేయబడిన వైద్యుడు"},
        "risk_level": {"en": "Risk Level", "te": "ప్రమాద స్థాయి"},
        "recommended_action": {"en": "Recommended Action", "te": "సిఫార్సు చేయబడిన చర్య"},
        "description": {"en": "Description", "te": "వివరణ"},
        "precautions": {"en": "Precautions", "te": "జాగ్రత్తలు"}
    }

    def __init__(self, model_path=None, base_dir=None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            
        if model_path is None:
            model_path = os.path.join(base_dir, "model_weights", "disease_model.pkl")
            
        model_path = os.path.abspath(os.path.normpath(model_path))
        try:
            self.model = joblib.load(model_path)
            self.all_symptoms = joblib.load(os.path.join(base_dir, "model_weights", "all_symptoms.pkl"))
        except Exception as e:
            print(f"Warning: Could not load model or symptoms from {model_path}: {e}")
            self.model = None
            self.all_symptoms = []
            
        try:
            desc_path = os.path.join(base_dir, "dataset", "symptom_Description.csv")
            prec_path = os.path.join(base_dir, "dataset", "symptom_precaution.csv")
            
            df_desc = pd.read_csv(desc_path)
            df_prec = pd.read_csv(prec_path)
            
            # The description table has trailing spaces sometimes
            df_desc['Disease'] = df_desc['Disease'].str.strip()
            df_prec['Disease'] = df_prec['Disease'].str.strip()
            
            self.disease_desc = df_desc.set_index('Disease')['Description'].to_dict()
            
            self.disease_prec = {}
            for idx, row in df_prec.iterrows():
                disease = row['Disease']
                precs = [str(row[f'Precaution_{i}']).strip() for i in range(1, 5) if pd.notna(row[f'Precaution_{i}'])]
                self.disease_prec[disease] = ", ".join(precs)
                
        except Exception as e:
            print(f"Warning: Could not load disease description or precautions: {e}")
            self.disease_desc = {}
            self.disease_prec = {}

    def create_vector(self, symptoms):
        vector = [0] * len(self.all_symptoms)
        
        for s in symptoms:
            clean_s = s.strip().replace('_', ' ').lower()
            if clean_s in self.all_symptoms:
                index = self.all_symptoms.index(clean_s)
                vector[index] = 1

        return vector

    def predict(self, symptoms):
        vector = self.create_vector(symptoms)
        
        disease_name = "Unknown"
        doctor = "General Physician" # Kaggle dataset does not have 'doctor' map, so we default
        risk_level = "Determined by Doctor" # Same as above
        treatment = "Consult a doctor for full evaluation."
        description = "Medical description unavailable."
        precautions = "Consult a doctor for further guidance."
        
        if self.model and sum(vector) > 0:
            numeric_result = self.model.predict([vector])[0]
            # Random Forest was trained on strings, so numeric_result IS the string target!
            disease_name = str(numeric_result).strip()
            
            description = self.disease_desc.get(disease_name, "Medical description unavailable.")
            precautions = self.disease_prec.get(disease_name, "Rest and hydrate.")
            
            # Pack this rich data into our Treatment string so Gemini can format it beautifully
            treatment = f"{description} | Recommended Precautions: {precautions}"
        elif sum(vector) == 0:
            disease_name = "Undetermined (No recognized symptoms found)"
            treatment = "Please provide more specific physical symptoms like 'itching', 'fever', 'joint pain'."
            description = "No recognized symptom pattern was detected by the model."
            precautions = "Share clearer symptom details and consult a clinician."

        return {
            "disease": disease_name.title(),
            "doctor": doctor,
            "risk_level": risk_level,
            "treatment": treatment,
            "description": description,
            "precautions": precautions
        }

    def format_bilingual_response(self, result, lang_mode='en'):
        """Generates a response in English, Telugu, or Both based on context."""
        en = result
        
        # Define the blocks for English and Telugu
        eng_block = (
            f"### {self.TRANSLATIONS['preliminary_assessment']['en']}\n"
            f"Based on the symptoms, you might be suffering from **{en['disease']}**.\n\n"
            f"**{self.TRANSLATIONS['description']['en']}:**\n{en['description']}\n\n"
            f"**{self.TRANSLATIONS['precautions']['en']}:**\n{en['precautions']}\n\n"
            f"**{self.TRANSLATIONS['suggested_doctor']['en']}:** {en['doctor']}\n"
            f"**{self.TRANSLATIONS['risk_level']['en']}:** {en['risk_level']}"
        )

        tel_block = (
            f"### {self.TRANSLATIONS['preliminary_assessment']['te']}\n"
            f"మీరు వివరించిన లక్షణాల ఆధారంగా, మీరు **{en['disease']}** తో బాధపడుతుండవచ్చు.\n\n"
            f"**{self.TRANSLATIONS['description']['te']}:**\n{en['description']}\n\n"
            f"**{self.TRANSLATIONS['precautions']['te']}:**\n{en['precautions']}\n\n"
            f"**{self.TRANSLATIONS['suggested_doctor']['te']}:** {en['doctor']}\n"
            f"**{self.TRANSLATIONS['risk_level']['te']}:** {en['risk_level']}"
        )

        if lang_mode == 'te':
            return tel_block
        elif lang_mode == 'bilingual':
            return f"{tel_block}\n\n---\n\n{eng_block}"
        else:
            return eng_block