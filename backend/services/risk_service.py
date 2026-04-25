import os
from typing import Dict, List, Tuple

import pandas as pd


class RiskScorer:
    """Simple, explainable rule-based risk scorer for intake prioritization."""

    HIGH_ALERT_SYMPTOMS = {
        "chest pain",
        "chest tightness",
        "breathlessness",
        "shortness of breath",
        "coma",
        "stomach bleeding",
        "acute liver failure",
        "fast heart rate",
        "weakness in limbs",
        "weakness of one body side",
        "swelling of stomach",
        "high fever",
    }

    def __init__(self, severity_csv_path: str = None):
        if severity_csv_path is None:
            severity_csv_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "dataset",
                "Symptom-severity.csv",
            )

        self.symptom_weights = self._load_symptom_weights(severity_csv_path)

    def _load_symptom_weights(self, csv_path: str) -> Dict[str, int]:
        try:
            df = pd.read_csv(csv_path)
            mapping: Dict[str, int] = {}
            for _, row in df.iterrows():
                symptom = str(row.get("Symptom", "")).strip().replace("_", " ").lower()
                weight = int(row.get("weight", 0))
                if symptom:
                    mapping[symptom] = weight
            return mapping
        except Exception:
            return {}

    def score(self, profile: Dict) -> Tuple[int, str, List[str]]:
        symptoms = [str(s).replace("_", " ").lower().strip() for s in profile.get("symptoms", [])]
        age = self._safe_int(profile.get("age"))
        notes_blob = " ".join(str(n).lower() for n in profile.get("notes", []))

        if not symptoms:
            return 10, "Low", ["No clear symptom pattern detected yet."]

        # Symptom severity component.
        matched_weights = [self.symptom_weights.get(s, 2) for s in symptoms]
        max_weight = max(matched_weights) if matched_weights else 0
        avg_weight = sum(matched_weights) / len(matched_weights) if matched_weights else 0
        score = min(60, int(avg_weight * 8 + max_weight * 2))
        reasons: List[str] = [f"Severity index from {len(symptoms)} reported symptom(s)."]

        # High-alert symptoms.
        alert_found = sorted([s for s in symptoms if s in self.HIGH_ALERT_SYMPTOMS])
        if alert_found:
            score += min(25, 8 * len(alert_found))
            reasons.append(f"High-alert symptom(s): {', '.join(alert_found[:3])}.")

        # Escalate when language indicates severe distress.
        if any(term in notes_blob for term in ("severe", "svere", "very severe", "intense", "unbearable", "extreme")):
            score += 10
            reasons.append("Severe symptom intensity reported by patient.")

        # Multiple simultaneous symptoms increase uncertainty and risk burden.
        if len(symptoms) >= 2:
            score += 6
            reasons.append("Multiple concurrent symptoms reported.")

        # Age-based fragility adjustment.
        if age is not None and age >= 65:
            score += 10
            reasons.append("Age >= 65 increases clinical risk.")
        elif age is not None and age <= 5:
            score += 8
            reasons.append("Pediatric age bracket needs faster screening.")

        score = max(0, min(100, score))
        triage = self._triage_from_score(score)
        return score, triage, reasons

    def detect_emergency(self, profile: Dict) -> Tuple[bool, List[str]]:
        """Hard-rule emergency detector for immediate escalation."""
        symptoms = [str(s).replace("_", " ").lower().strip() for s in profile.get("symptoms", [])]
        matched = sorted({s for s in symptoms if s in self.HIGH_ALERT_SYMPTOMS})
        return bool(matched), matched

    def _safe_int(self, value):
        try:
            return int(str(value).strip())
        except Exception:
            return None

    def _triage_from_score(self, score: int) -> str:
        if score >= 75:
            return "Critical"
        if score >= 55:
            return "High"
        if score >= 35:
            return "Medium"
        return "Low"
