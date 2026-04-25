# Virtual Vita - Viva / Presentation Talking Points

## 1) Problem and Motivation (30-45 sec)
- Hospitals face high patient load, reducing time per consultation.
- Manual intake can miss symptoms and delay high-risk case detection.
- Goal: build an AI-assisted system for early risk-aware screening and patient prioritization.

## 2) Project Objective (30 sec)
- Provide preliminary disease prediction from symptom input.
- Compute explainable risk score and triage level.
- Help doctors prioritize urgent patients faster.
- Reduce waiting time and improve workflow visibility.

## 3) System Overview (45 sec)
- Frontend: React dashboards for User Intake and Admin Review.
- Backend: Flask APIs for chat intake, patient records, risk scoring, and analytics.
- ML layer: Random Forest symptom-to-disease prediction.
- Data layer: cleaned training dataset, evaluation dataset, and generated performance reports.

## 4) Core Innovation (45 sec)
- Explainable risk stratification (score + risk reasons).
- Workflow states for case handling: Waiting, In Review, Escalated, Closed.
- Admin queue sorted by clinical urgency (triage + risk score).
- Evaluation pipeline with cross-validation, per-class metrics, and confusion matrix export.

## 5) Demo Flow Script (1-2 min)
- Show patient entering demographics and symptoms in User Dashboard.
- Show generated intake completion and saved patient record.
- Switch to Admin Dashboard:
  - highlight triage distribution
  - open top-risk patient
  - update status (In Review/Escalated/Closed)
- Show `performance_report.json`, `per_class_metrics.csv`, and `confusion_matrix.csv`.

## 6) Evaluation Highlights (45 sec)
- Metrics reported: Accuracy, Precision, Recall, F1 (macro + weighted).
- Added k-fold cross-validation to improve trust in results.
- Per-class metrics identify weaker classes for future improvement.
- Response-time stats show system suitability for near-real-time screening.

## 7) Limitations (30 sec)
- Dataset is structured and relatively clean compared to real clinical notes.
- No direct hospital EHR integration in current prototype.
- Final diagnosis must always remain with clinicians.

## 8) Future Scope (30-45 sec)
- Integrate EHR/EMR and stronger authentication.
- Expand multilingual symptom normalization and typo handling.
- Add real-world hospital pilot feedback and calibration.
- Explore ensemble models and uncertainty/confidence scoring.

## 9) Closing Statement (15 sec)
- Virtual Vita demonstrates a practical, explainable, and workflow-ready AI assistant for early diagnosis support and patient load management in clinical settings.
