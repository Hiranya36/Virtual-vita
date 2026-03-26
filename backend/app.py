from fastapi import FastAPI
from pydantic import BaseModel
from backend.services.prediction_service import DiseasePredictor

app = FastAPI()

predictor = DiseasePredictor()

class SymptomRequest(BaseModel):
    symptoms: list[str]

@app.post("/predict")
def predict_disease(request: SymptomRequest):

    result = predictor.predict(request.symptoms)

    return {
        "disease": result["disease"],
        "doctor": result["doctor"],
        "risk_level": result["risk_level"],
        "treatment": result["treatment"]
    }