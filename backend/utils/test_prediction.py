import sys
import os

# add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.services.prediction_service import DiseasePredictor


predictor = DiseasePredictor()

# create sample symptom vector
sample = [0] * 183

# simulate a symptom
sample[0] = 1

result = predictor.predict(sample)

print("Predicted disease:", result)