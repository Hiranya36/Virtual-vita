import json
import os
import re
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify, request
from google import genai
from google.genai import types

from services.risk_service import RiskScorer
from services.evaluation_service import ModelEvaluator
from services.prediction_service import DiseasePredictor
from services.symptom_extractor import SymptomExtractor

chat_bp = Blueprint('chat', __name__)

api_key = os.getenv("GEMINI_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)
USE_LLM_CHAT = os.getenv("USE_LLM_CHAT", "false").lower() == "true"
USE_OLLAMA_FIRST = os.getenv("USE_OLLAMA_FIRST", "false").lower() == "true"

system_instruction = """You are an empathetic, highly professional Intake Nurse named Virtual Vita.
Your goal is to gather patient intake details conversationally.

CRITICAL INSTRUCTIONS:
1. Ask ONLY ONE QUESTION at a time.
2. Be warm and supportive, but concise.
3. DO NOT diagnose or claim certainty.
4. STRICT LANGUAGE MATCHING:
   - If patient uses Telugu script, reply fully in Telugu script.
   - If patient uses English script, reply fully in English.
5. Never output JSON, code blocks, XML, or structured markup.
"""

sessions = {}
extractor = SymptomExtractor()
risk_scorer = RiskScorer()
model_evaluator = ModelEvaluator()
predictor = DiseasePredictor()
BASE_DIR = Path(__file__).resolve().parents[2]
PATIENTS_FILE = BASE_DIR / "dataset" / "patients.json"
PERFORMANCE_REPORT_FILE = BASE_DIR / "dataset" / "performance_report.json"
ALLOWED_STATUSES = {"Waiting", "In Review", "Escalated", "Closed"}
INTAKE_PLANS = {
    "headache": ["duration", "location", "severity", "associated"],
    "breathing": ["duration", "severity", "associated", "trigger"],
    "chest": ["duration", "severity", "location", "trigger"],
    "abdominal": ["duration", "location", "severity", "associated"],
    "fever": ["duration", "severity", "associated", "pattern"],
    "general": ["duration", "severity", "location", "associated"],
}
TELUGU_SYMPTOM_MAP = {
    "జ్వరం": "fever",
    "జ్వరంగా": "fever",
    "తలనొప్పి": "headache",
    "తల నొప్పి": "headache",
    "దగ్గు": "cough",
    "శ్వాస": "breathlessness",
    "ఉపిరి": "breathlessness",
    "ఛాతి నొప్పి": "chest pain",
    "ఛాతి బిగుతు": "chest pain",
    "వాంతి": "vomiting",
    "కడుపు నొప్పి": "abdominal pain",
}
ENGLISH_SYMPTOM_MAP = {
    "body pain": "muscle pain",
    "body pains": "muscle pain",
    "body ache": "muscle pain",
    "body aches": "muscle pain",
    "head ache": "headache",
    "abdomen pain": "abdominal pain",
}


def _new_state():
    return {
        "history": [{"role": "system", "content": system_instruction}],
        "profile": {
            "patient_name": "",
            "age": "",
            "weight": "",
            "phone": "",
            "chief_complaint": "",
            "history_of_present_illness": "",
            "triage_level": "Medium",
            "risk_score": 0,
            "risk_reasons": [],
            "symptoms": [],
            "notes": [],
        },
        "post_demo_details_count": 0,
        "saved": False,
        "lang_pref": "en",
        "intake_focus": "general",
        "detail_slots": {},
        "awaiting_field": None,
        "awaiting_slot": None,
    }


def _is_telugu_script(text):
    return bool(re.search(r"[\u0C00-\u0C7F]", text or ""))


def _resolve_lang_pref(state, user_text):
    if _is_telugu_script(user_text):
        state["lang_pref"] = "te"
    elif re.search(r"[A-Za-z]", user_text or ""):
        state["lang_pref"] = "en"
    return state.get("lang_pref", "en")


def _normalize_spaces(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def _detect_focus(profile):
    complaint = (profile.get("chief_complaint") or "").lower()
    symptoms = " ".join(profile.get("symptoms", [])).lower()
    combined = f"{complaint} {symptoms}"
    if any(k in combined for k in ("headache", "head ache", "head pain", "migraine")):
        return "headache"
    if any(k in combined for k in ("breath", "breathing", "breathless", "shortness of breath")):
        return "breathing"
    if any(k in combined for k in ("chest pain", "chest tightness", "chest pressure")):
        return "chest"
    if any(k in combined for k in ("stomach", "abdomen", "abdominal", "belly")):
        return "abdominal"
    if any(k in combined for k in ("fever", "high fever", "mild fever", "temperature")):
        return "fever"
    return "general"


def _extract_detail_slots(user_text):
    text = _normalize_spaces(user_text).lower()
    slots = {}
    if not text:
        return slots
    if re.search(r"\b(since|scince|for|from|day|days|week|weeks|month|months|year|years|today|morning|night)\b", text):
        slots["duration"] = True
    # Telugu duration/time hints (e.g., "మూడు రోజులుగా", "2 వారాలుగా", "నిన్న నుండి")
    if re.search(
        r"(రోజు|రోజులు|రోజులుగా|రోజుల నుంచి|రోజుల నుండి|వారం|వారాలు|వారాలుగా|నెల|నెలలు|నెలలుగా|సంవత్సరం|సంవత్సరాలు|సంవత్సరాలుగా|నిన్న|ఈరోజు|ఈ రోజు|ఉదయం|రాత్రి|ఇప్పటి నుంచి|నుంచి|నుండి)",
        user_text or "",
    ):
        slots["duration"] = True
    if re.search(
        r"\b(left|right|back|front|side|behind|upper|lower|whole|all over|center|middle|abdomen|abdominal|stomach|chest|head|throat)\b",
        text,
    ):
        slots["location"] = True
    if re.search(r"\b(mild|moderate|severe|svere|very severe|pain scale|intense|unbearable|difficult)\b", text):
        slots["severity"] = True
    # Telugu severity hints: mild/moderate/severe equivalents
    if re.search(r"(స్వల్పం|తక్కువ|మధ్యస్థం|మోస్తరు|తీవ్రం|చాలా|అత్యంత)", user_text or ""):
        slots["severity"] = True
    if re.search(r"\b(nausea|vomit|vomiting|fever|cough|cold|dizziness|wheezing|tightness|weakness|sweating)\b", text):
        slots["associated"] = True
    if re.search(r"\b(when|after|during|walking|climbing|exercise|lying down|night|morning|food|cold air)\b", text):
        slots["trigger"] = True
    if re.search(
        r"\b(continuous|on and off|intermittent|comes and goes|frequent|frequently|times|again and again|repeating)\b",
        text,
    ):
        slots["pattern"] = True
    return slots


def _focus_question(slot, focus, telugu=False):
    questions = {
        "duration": (
            "ఈ లక్షణం ఎప్పటి నుంచి ఉంది?"
            if telugu
            else "How long have you been experiencing this symptom?"
        ),
        "location": (
            "లక్షణం ఏ భాగంలో ఎక్కువగా ఉంది?"
            if telugu
            else "Where exactly do you feel this symptom most?"
        ),
        "severity": (
            "తీవ్రత ఎంత? స్వల్పం, మధ్యస్థం, లేక తీవ్రంగా ఉందా?"
            if telugu
            else "How severe is it: mild, moderate, or severe?"
        ),
        "associated": (
            "ఇతర సంబంధిత లక్షణాలు ఉన్నాయా? (ఉదాహరణకు జ్వరం, వాంతులు, దగ్గు)"
            if telugu
            else "Do you have any associated symptoms (for example fever, vomiting, cough)?"
        ),
        "trigger": (
            "ఇది ఎప్పుడు ఎక్కువగా అవుతుంది? నడిచినప్పుడు లేదా పని చేసినప్పుడు పెరుగుతుందా?"
            if telugu
            else "When does it get worse, such as while walking or exertion?"
        ),
        "pattern": (
            "ఇది నిరంతరంగా ఉందా లేక మధ్య మధ్యలో వస్తుందా?"
            if telugu
            else "Is it continuous or does it come and go?"
        ),
    }
    if focus == "headache" and slot == "location":
        return (
            "ఈ తలనొప్పి తలలో ఏ భాగంలో ఉంది: ఎడమ, కుడి, వెనుక భాగం లేదా మొత్తం తలలోనా?"
            if telugu
            else "For the headache, where is it located: left side, right side, back of head, or all over?"
        )
    if focus in {"breathing", "chest"} and slot == "associated":
        return (
            "ఉపిరి సమస్యతో పాటు ఛాతిలో బిగుతు, వీజింగ్ లేదా మాట్లాడేటప్పుడు ఇబ్బంది ఉందా?"
            if telugu
            else "Along with this, do you have chest tightness, wheezing, or trouble speaking full sentences?"
        )
    return questions.get(slot, questions["associated"])


def _clean_weight(value, unit):
    if not value:
        return ""
    unit = (unit or "kg").lower()
    if unit in {"lb", "lbs", "pound", "pounds"}:
        return f"{value} lbs"
    return f"{value} kg"


def _extract_demographics(user_text, profile):
    lowered = _normalize_spaces(user_text).lower()
    cleaned_original = _normalize_spaces(user_text)

    # Handle compact space-separated input:
    # "Samira 23 54 8 3 1 7 6 0 2 9 8 4" or "Samira 23 54 8317602984"
    tokenized = cleaned_original.split()
    if len(tokenized) >= 4:
        candidate_name = tokenized[0]
        trailing_tokens = tokenized[1:]
        numeric_tokens = [t for t in trailing_tokens if re.fullmatch(r"\d+", t)]
        if (
            (re.fullmatch(r"[A-Za-z][A-Za-z\s]{1,40}", candidate_name) or re.fullmatch(r"[\u0C00-\u0C7F]{2,40}", candidate_name))
            and len(numeric_tokens) >= 3
        ):
            if not profile["patient_name"]:
                profile["patient_name"] = candidate_name.capitalize() if re.fullmatch(r"[A-Za-z]+", candidate_name) else candidate_name
            if not profile["age"] and re.fullmatch(r"\d{1,3}", numeric_tokens[0]):
                age_val = int(numeric_tokens[0])
                if 0 < age_val <= 120:
                    profile["age"] = str(age_val)
            if not profile["weight"] and re.fullmatch(r"\d{2,3}", numeric_tokens[1]):
                profile["weight"] = _clean_weight(numeric_tokens[1], "kg")
            if not profile["phone"]:
                joined_phone = "".join(numeric_tokens[2:])
                if len(joined_phone) >= 10:
                    profile["phone"] = joined_phone

    # Handle compact CSV-like input: "name, age, weight, phone"
    if "," in cleaned_original:
        parts = [p.strip() for p in cleaned_original.split(",") if p.strip()]
        if len(parts) >= 4:
            candidate_name = parts[0]
            if re.fullmatch(r"[A-Za-z][A-Za-z\s]{1,40}", candidate_name) and not profile["patient_name"]:
                profile["patient_name"] = " ".join(piece.capitalize() for piece in candidate_name.split())

            if not profile["age"] and re.fullmatch(r"\d{1,3}", parts[1]):
                age = int(parts[1])
                if 0 < age <= 120:
                    profile["age"] = str(age)

            if not profile["weight"]:
                weight_match_csv = re.search(r"(\d{2,3}(?:\.\d+)?)\s*(kg|kgs|kilograms|lb|lbs|pounds)?", parts[2], re.IGNORECASE)
                if weight_match_csv:
                    profile["weight"] = _clean_weight(weight_match_csv.group(1), weight_match_csv.group(2))

            if not profile["phone"]:
                phone_digits = re.sub(r"\D", "", parts[3])
                if len(phone_digits) >= 10:
                    profile["phone"] = phone_digits

    name_match = re.search(r"\b(?:my name is|i am|i'm)\s+([a-z][a-z\s]{1,40})\b", lowered)
    if name_match and not profile["patient_name"]:
        candidate = " ".join(part.capitalize() for part in name_match.group(1).split())
        if all(token not in {"years", "year", "old"} for token in candidate.lower().split()):
            profile["patient_name"] = candidate

    age_match = re.search(r"\b(?:age\s*(?:is)?|i am|i'm)\s*(\d{1,3})\b", lowered)
    if age_match:
        age = int(age_match.group(1))
        if 0 < age <= 120:
            profile["age"] = str(age)

    weight_match = re.search(
        r"\b(?:weight|wt)\s*(?:is)?\s*(\d{2,3}(?:\.\d+)?)\s*(kg|kgs|kilograms|lb|lbs|pounds)?\b",
        lowered,
    )
    if weight_match:
        profile["weight"] = _clean_weight(weight_match.group(1), weight_match.group(2))

    phone_match = re.search(r"(\+?\d[\d\s\-]{8,14}\d)", user_text or "")
    if phone_match:
        digits = re.sub(r"\D", "", phone_match.group(1))
        if len(digits) >= 10:
            profile["phone"] = digits

    # Telugu demographics parsing.
    tel_name_match = re.search(r"(?:నేను|నా పేరు)\s*([\u0C00-\u0C7F\s]{2,40})", user_text or "")
    if tel_name_match and not profile["patient_name"]:
        candidate = _normalize_spaces(tel_name_match.group(1))
        # Remove trailing demographic keywords if present in same sentence.
        candidate = re.split(r"(వయసు|ఏజ్|బరువు|వెయిట్|ఫోన్|నెంబర్)", candidate)[0].strip()
        if candidate:
            profile["patient_name"] = candidate

    tel_age_match = re.search(r"(?:వయసు|ఏజ్)\s*(\d{1,3})", user_text or "")
    if tel_age_match:
        age = int(tel_age_match.group(1))
        if 0 < age <= 120:
            profile["age"] = str(age)

    tel_weight_match = re.search(
        r"(?:బరువు|వెయిట్)\s*(\d{2,3}(?:\.\d+)?)\s*(kg|kgs|కిలో|కిలోలు|lb|lbs|పౌండ్లు)?",
        user_text or "",
        re.IGNORECASE,
    )
    if tel_weight_match:
        profile["weight"] = _clean_weight(tel_weight_match.group(1), tel_weight_match.group(2))

    # If the bot asked for name and user simply typed "ravi", accept it.
    simple_name = _normalize_spaces(user_text)
    if (
        not profile["patient_name"]
        and re.fullmatch(r"[A-Za-z][A-Za-z\s]{1,40}", simple_name or "")
        and not re.search(r"\b(i have|pain|fever|cough|age|weight|phone)\b", simple_name.lower())
    ):
        profile["patient_name"] = " ".join(piece.capitalize() for piece in simple_name.split())

    # If the bot asked for name and user typed a simple Telugu name, accept it.
    telugu_simple_name = _normalize_spaces(user_text)
    if (
        not profile["patient_name"]
        and re.fullmatch(r"[\u0C00-\u0C7F][\u0C00-\u0C7F\s]{1,40}", telugu_simple_name or "")
    ):
        profile["patient_name"] = telugu_simple_name

    # Numeric-only step replies when bot asks details one by one.
    numeric_only = _normalize_spaces(user_text)
    if re.fullmatch(r"\d{1,3}", numeric_only or "") and not profile["age"]:
        age = int(numeric_only)
        if 0 < age <= 120:
            profile["age"] = str(age)
    elif re.fullmatch(r"\d{2,3}", numeric_only or "") and profile.get("age") and not profile["weight"]:
        profile["weight"] = _clean_weight(numeric_only, "kg")

    if not profile["phone"]:
        digits_only = re.sub(r"\D", "", user_text or "")
        if len(digits_only) >= 10:
            profile["phone"] = digits_only


def _apply_awaiting_field_capture(state, user_text):
    """Permanent fix: map short replies using last asked field."""
    field = state.get("awaiting_field")
    if not field:
        return

    text = _normalize_spaces(user_text)

    if field == "patient_name" and not state["profile"].get("patient_name"):
        if re.fullmatch(r"[A-Za-z][A-Za-z\s]{1,40}", text or ""):
            state["profile"]["patient_name"] = " ".join(piece.capitalize() for piece in text.split())
            state["awaiting_field"] = None
            return
        if re.fullmatch(r"[\u0C00-\u0C7F][\u0C00-\u0C7F\s]{1,40}", text or ""):
            state["profile"]["patient_name"] = text
            state["awaiting_field"] = None
            return

    if field == "age" and not state["profile"].get("age"):
        if re.fullmatch(r"\d{1,3}", text or ""):
            age = int(text)
            if 0 < age <= 120:
                state["profile"]["age"] = str(age)
                state["awaiting_field"] = None
                return

    if field == "weight" and not state["profile"].get("weight"):
        m = re.fullmatch(r"(\d{2,3}(?:\.\d+)?)\s*(kg|kgs|kilograms|కిలో|కిలోలు|lb|lbs|పౌండ్లు)?", text or "", re.IGNORECASE)
        if m:
            state["profile"]["weight"] = _clean_weight(m.group(1), m.group(2))
            state["awaiting_field"] = None
            return

    if field == "phone" and not state["profile"].get("phone"):
        digits = re.sub(r"\D", "", user_text or "")
        if len(digits) >= 10:
            state["profile"]["phone"] = digits
            state["awaiting_field"] = None
            return


def _apply_awaiting_slot_capture(state, user_text):
    """Permanent fix: map short replies using last asked intake slot."""
    slot = state.get("awaiting_slot")
    if not slot:
        return

    text = _normalize_spaces(user_text)
    if not text:
        return

    # Basic validations to avoid marking random "ok" as filled.
    lowered = text.lower()

    if slot == "duration":
        if re.search(r"\d", lowered) or re.search(r"(రోజు|రోజులు|వారం|వారాలు|నెల|నెలలు|నిన్న|ఈరోజు|ఉదయం|రాత్రి|నుంచి|నుండి)", text):
            state["detail_slots"]["duration"] = True
            state["awaiting_slot"] = None
        return

    if slot == "severity":
        if re.search(r"\b(mild|moderate|severe|svere|intense|unbearable|difficult)\b", lowered) or re.search(
            r"(స్వల్పం|తక్కువ|మధ్యస్థం|మోస్తరు|తీవ్రం|చాలా|అత్యంత)",
            text,
        ):
            state["detail_slots"]["severity"] = True
            state["awaiting_slot"] = None
        return

    if slot == "location":
        # Accept short but meaningful location phrases.
        if len(text) >= 3:
            state["detail_slots"]["location"] = True
            state["awaiting_slot"] = None
        return

    if slot in {"associated", "trigger", "pattern"}:
        # For these, any non-empty descriptive answer counts.
        if len(text.split()) >= 1:
            state["detail_slots"][slot] = True
            state["awaiting_slot"] = None
        return


def _extract_complaint_and_symptoms(user_text, profile):
    cleaned = _normalize_spaces(user_text)
    if not cleaned:
        return

    symptoms = extractor.extract(cleaned) if extractor else []
    lowered = cleaned.lower()

    # Heuristic synonym mapping for critical respiratory/chest terms.
    # This ensures triage is safer even when free-text doesn't exactly match dataset tokens.
    if any(term in lowered for term in ("breathing problem", "breathing issue", "shortness of breath", "breathless")):
        symptoms.append("breathlessness")
    if any(term in lowered for term in ("chest tightness", "chest pressure", "tight chest")):
        symptoms.append("chest pain")
    for en_term, mapped in ENGLISH_SYMPTOM_MAP.items():
        if en_term in lowered:
            symptoms.append(mapped)

    # Telugu free-text symptom mapping.
    for tel_term, mapped in TELUGU_SYMPTOM_MAP.items():
        if tel_term in cleaned:
            symptoms.append(mapped)

    for symptom in symptoms:
        if symptom not in profile["symptoms"]:
            profile["symptoms"].append(symptom)

    # Keep complaint from first symptom-focused user line.
    if not profile["chief_complaint"]:
        complaint_match = re.search(
            r"(?:i have|i am having|i feel|suffering from|problem is)\s+(.+)",
            cleaned,
            flags=re.IGNORECASE,
        )
        if complaint_match:
            profile["chief_complaint"] = complaint_match.group(1).strip(" .")
        elif _looks_like_symptom_detail(cleaned):
            # Accept concise symptom-only replies like "severe body pains".
            profile["chief_complaint"] = cleaned.strip(" .")
        elif symptoms:
            profile["chief_complaint"] = ", ".join(symptoms[:3])
        elif _is_telugu_script(cleaned):
            # Telugu complaint capture (e.g., "నాకు బాగా జ్వరంగా ఉంది")
            telugu_complaint_match = re.search(
                r"(?:నాకు|నాకి|నన్ను)\s*(.+?)(?:ఉంది|ఉన్నది|అవుతోంది|వస్తోంది|గా ఉంది)?$",
                cleaned,
            )
            if telugu_complaint_match and telugu_complaint_match.group(1).strip():
                profile["chief_complaint"] = telugu_complaint_match.group(1).strip(" .")
            elif any(term in cleaned for term in TELUGU_SYMPTOM_MAP.keys()):
                profile["chief_complaint"] = cleaned

    profile["notes"].append(cleaned)
    profile["history_of_present_illness"] = " ".join(profile["notes"][-6:])
    risk_score, triage_level, reasons = risk_scorer.score(profile)
    profile["risk_score"] = risk_score
    profile["triage_level"] = triage_level
    profile["risk_reasons"] = reasons


def _has_demographics(profile):
    return all(profile.get(k) for k in ("patient_name", "age", "weight", "phone"))


def _is_intake_complete(state):
    profile = state["profile"]
    focus = state.get("intake_focus", "general")
    plan = INTAKE_PLANS.get(focus, INTAKE_PLANS["general"])
    answered = state.get("detail_slots", {})
    # Require chief complaint + first 3 core slots of focus plan.
    required_slots = plan[:3]
    enough_symptom_detail = bool(profile["chief_complaint"]) and all(answered.get(slot) for slot in required_slots)
    return _has_demographics(profile) and enough_symptom_detail


def _first_question_only(text):
    text = (text or "").strip()
    if not text:
        return "Could you tell me more about your symptoms?"
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    merged = " ".join(lines)
    q_idx = merged.find("?")
    if q_idx == -1:
        return merged
    prefix = merged[: q_idx + 1]
    # Drop additional trailing questions if the model generated several.
    return prefix


def _contains_latin(text):
    return bool(re.search(r"[A-Za-z]", text or ""))


def _intake_completion_message(profile, telugu=False):
    if telugu:
        return (
            "ధన్యవాదాలు. మీ నమోదు వివరాలు భద్రపరచబడ్డాయి. "
            "నిర్వాహక డాష్‌బోర్డ్‌లో మీ రికార్డు ఇప్పుడు అందుబాటులో ఉంది."
        )
    return (
        "Thank you. Your intake details are recorded and shared with the clinical admin team. "
        "Your record is now available in the Admin Dashboard."
    )


def _emergency_alert_message(telugu=False):
    if telugu:
        return (
            "అత్యవసర హెచ్చరిక: మీ లక్షణాలు ప్రమాద సూచనలుగా గుర్తించబడ్డాయి. "
            "దయచేసి వెంటనే సమీప అత్యవసర వైద్య సేవలను సంప్రదించండి లేదా ఎమర్జెన్సీ నంబర్‌కి కాల్ చేయండి."
        )
    return (
        "Emergency alert: your symptoms match high-risk warning signs. "
        "Please seek immediate emergency care or call emergency services right now."
    )


def _build_emergency_summary(profile, emergency_symptoms):
    return {
        "status": "Escalated",
        "patient_name": profile.get("patient_name", "Unknown"),
        "age": profile.get("age", "Unknown"),
        "weight": profile.get("weight", "Unknown"),
        "phone": profile.get("phone", "Unknown"),
        "chief_complaint": profile.get("chief_complaint", "Not provided"),
        "history_of_present_illness": profile.get("history_of_present_illness", "Not provided"),
        "triage_level": "Critical",
        "risk_score": max(90, int(profile.get("risk_score", 0) or 0)),
        "risk_reasons": profile.get("risk_reasons", []) + [
            f"Emergency rule triggered by: {', '.join(emergency_symptoms)}"
        ],
        "symptoms": profile.get("symptoms", []),
        "emergency_triggered": True,
        "emergency_symptoms": emergency_symptoms,
        "decision_path": "rule_engine:emergency",
    }


def _build_preliminary_prediction(profile, telugu=False):
    symptoms = profile.get("symptoms", []) or []
    if len(symptoms) < 2 or predictor is None:
        return None, None

    try:
        result = predictor.predict(symptoms)
        disease = result.get("disease", "Undetermined")
        description = result.get("description", "Medical description unavailable.")
        precautions = result.get("precautions", "Consult a doctor for further guidance.")

        if telugu:
            message = (
                "ప్రాథమిక AI అంచనా: మీరు తెలిపిన లక్షణాల ఆధారంగా **"
                f"{disease}"
                "** అనే అవకాశం కనిపిస్తోంది. ఇది తుది నిర్ధారణ కాదు. "
                f"సంక్షిప్త వివరణ: {description} "
                f"జాగ్రత్తలు: {precautions}"
            )
        else:
            message = (
                "Preliminary AI assessment: based on your reported symptoms, a possible condition is **"
                f"{disease}"
                "**. This is not a final diagnosis. "
                f"Brief note: {description} "
                f"Precautions: {precautions}"
            )

        payload = {
            "disease": disease,
            "description": description,
            "precautions": precautions,
            "symptoms_used": symptoms,
        }
        return message, payload
    except Exception:
        return None, None


def _next_intake_question(state, telugu=False):
    profile = state["profile"]
    focus = state.get("intake_focus", "general")
    answered = state.get("detail_slots", {})

    if not profile.get("patient_name"):
        state["awaiting_field"] = "patient_name"
        return "మీ పూర్తి పేరు చెప్పగలరా?" if telugu else "Could you please share your full name?"
    if not profile.get("age"):
        state["awaiting_field"] = "age"
        return "మీ వయస్సు ఎంత?" if telugu else "What is your age?"
    if not profile.get("weight"):
        state["awaiting_field"] = "weight"
        return "మీ బరువు ఎంత (కిలోలు లేదా పౌండ్లు)?" if telugu else "What is your weight (kg or lbs)?"
    if not profile.get("phone"):
        state["awaiting_field"] = "phone"
        return "మీ ఫోన్ నంబర్ చెప్పగలరా?" if telugu else "Could you share your phone number?"
    if not profile.get("chief_complaint"):
        state["awaiting_field"] = None
        state["awaiting_slot"] = None
        return (
            "ఇప్పుడు ప్రధానంగా ఏ సమస్య వల్ల వచ్చారు?"
            if telugu
            else "What is the main symptom or problem bothering you right now?"
        )
    plan = INTAKE_PLANS.get(focus, INTAKE_PLANS["general"])
    for slot in plan:
        if not answered.get(slot):
            state["awaiting_slot"] = slot
            return _focus_question(slot, focus, telugu)
    return (
        "ధన్యవాదాలు. కొద్ది సేపట్లో మీ intake పూర్తి చేస్తాను."
        if telugu
        else "Thank you. I will complete your intake now."
    )


def _looks_like_symptom_detail(text):
    normalized = _normalize_spaces(text).lower()
    if not normalized:
        return False

    # Direct complaint patterns
    if re.search(r"\b(i have|i am having|i'm having|i feel|suffering from|problem is)\b", normalized):
        return True

    # Typical symptom terms for fallback mode (works even if symptom dataset fails to load)
    keywords = (
        "pain", "ache", "fever", "vomit", "nausea", "cough", "cold", "diarrhea",
        "headache", "stomach", "abdomen", "abdomen", "lower abdomen", "chest pain",
        "burning", "dizziness", "fatigue", "weakness", "swelling", "cramp", "cramps"
    )
    if any(term in normalized for term in keywords):
        return True
    # Telugu symptom keyword hints
    return any(term in (text or "") for term in TELUGU_SYMPTOM_MAP.keys())


def _looks_like_followup_detail(text):
    normalized = _normalize_spaces(text).lower()
    if not normalized:
        return False

    # Duration/frequency patterns should count as valid follow-up details.
    if re.search(
        r"\b(since|for|from|times|time|daily|week|weeks|month|months|year|years|frequent|frequently|continuous|on and off)\b",
        normalized,
    ):
        return True

    # Numeric temporal hints such as "3 times this week".
    if re.search(r"\b\d+\b", normalized) and re.search(r"\b(day|days|week|weeks|month|months|year|years|times)\b", normalized):
        return True

    # Location/quality clues, useful for headache and pain triage.
    if re.search(
        r"\b(left|right|back|front|side|behind|whole|severe|svere|mild|throbbing|pressure|sharp|dull|difficult|difficulty|breathless|wheezing|tightness)\b",
        normalized,
    ):
        return True

    # Generic descriptive details with enough words after chief complaint is captured.
    return len(normalized.split()) >= 4

@chat_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400
        
    user_message = data['message']
    session_id = data.get('session_id', 'default_session')
    ui_language = (data.get('ui_language') or data.get('lang') or 'auto')
    if isinstance(ui_language, str):
        ui_language = ui_language.strip().lower()
    else:
        ui_language = 'auto'

    if session_id not in sessions:
        sessions[session_id] = _new_state()
    state = sessions[session_id]
    profile = state["profile"]
    if ui_language in ('en', 'te'):
        state['lang_pref'] = ui_language
    elif user_message:
        _resolve_lang_pref(state, user_message)
    lang_pref = state.get('lang_pref', 'en')
    telugu_mode = lang_pref == 'te'

    _apply_awaiting_field_capture(state, user_message)
    _apply_awaiting_slot_capture(state, user_message)
    _extract_demographics(user_message, profile)
    _extract_complaint_and_symptoms(user_message, profile)
    state["intake_focus"] = _detect_focus(profile)
    for slot, value in _extract_detail_slots(user_message).items():
        if value:
            state["detail_slots"][slot] = True

    # Keep numeric counter in sync for backward compatibility with saved sessions.
    state["post_demo_details_count"] = max(
        state.get("post_demo_details_count", 0),
        len(state.get("detail_slots", {})),
    )
    if _has_demographics(profile) and (
        _looks_like_symptom_detail(user_message)
        or (
            bool(profile.get("chief_complaint"))
            and state["post_demo_details_count"] < 4
            and _looks_like_followup_detail(user_message)
        )
    ):
        state["post_demo_details_count"] += 1

    # Rule-first triage: emergency symptoms bypass model/chat and escalate immediately.
    is_emergency, emergency_symptoms = risk_scorer.detect_emergency(profile)
    if is_emergency:
        profile["triage_level"] = "Critical"
        profile["risk_score"] = max(90, int(profile.get("risk_score", 0) or 0))
        profile["risk_reasons"] = profile.get("risk_reasons", []) + [
            f"Emergency rule triggered by: {', '.join(emergency_symptoms)}"
        ]
        summary_data = _build_emergency_summary(profile, emergency_symptoms)
        if not state["saved"]:
            save_patient_record(summary_data)
            state["saved"] = True
        return jsonify({
            "response": _emergency_alert_message(telugu_mode),
            "is_complete": True,
            "summary_data": summary_data,
            "emergency_alert": True,
            "decision_path": "rule_engine:emergency",
        })

    # Fast deterministic intake mode (default): avoids slow LLM latency.
    if not USE_LLM_CHAT:
        return process_response(_next_intake_question(state, telugu_mode), state, user_message, telugu_mode)

    # --- OPTIONAL: TRY OLLAMA FIRST ---
    if USE_OLLAMA_FIRST:
        try:
            import ollama  # Lazy import to avoid startup crash on incompatible environments
            state["history"].append({"role": "user", "content": user_message})
            ollama_response = ollama.chat(model="llama3.2", messages=state["history"])
            response_text = _first_question_only(ollama_response["message"]["content"])
            if telugu_mode and _contains_latin(response_text):
                response_text = _next_intake_question(state, True)
            state["history"].append({"role": "assistant", "content": response_text})
            return process_response(response_text, state, user_message, telugu_mode)
        except Exception as ollama_err:
            print(f"[OLLAMA] Error: {ollama_err}. Falling back to Gemini...")

    # --- FALLBACK TO GEMINI ---
    if not api_key or not client:
        return process_fallback(user_message, "Gemini API Key missing and LLM disabled/offline.", state, telugu_mode)

    chat_session_key = f"{session_id}_gemini"
    if chat_session_key not in sessions:
        config = types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.2)
        sessions[chat_session_key] = client.chats.create(model="gemini-2.5-flash", config=config)
    chat_session = sessions[chat_session_key]
    
    try:
        response = chat_session.send_message(user_message)
        response_text = _first_question_only(response.text)
        if telugu_mode and _contains_latin(response_text):
            response_text = _next_intake_question(state, True)
        state["history"].append({"role": "assistant", "content": response_text})
        return process_response(response_text, state, user_message, telugu_mode)
        
    except Exception as e:
        return process_fallback(user_message, str(e), state, telugu_mode)

def process_response(response_text, state, user_message, telugu_mode=None):
    """Build completion state from backend profile extraction, not LLM formatting."""
    profile = state["profile"]
    is_complete = _is_intake_complete(state)
    summary_data = None
    if telugu_mode is None:
        telugu_mode = state.get("lang_pref", "en") == "te"

    if is_complete and not state["saved"]:
        prediction_text, prediction_data = _build_preliminary_prediction(profile, telugu_mode)
        summary_data = {
            "status": "Waiting",
            "patient_name": profile.get("patient_name", "Unknown"),
            "age": profile.get("age", "Unknown"),
            "weight": profile.get("weight", "Unknown"),
            "phone": profile.get("phone", "Unknown"),
            "chief_complaint": profile.get("chief_complaint", "Not provided"),
            "history_of_present_illness": profile.get("history_of_present_illness", "Not provided"),
            "triage_level": profile.get("triage_level", "Medium"),
            "risk_score": profile.get("risk_score", 0),
            "risk_reasons": profile.get("risk_reasons", []),
            "symptoms": profile.get("symptoms", []),
            "preliminary_prediction": prediction_data,
            "decision_path": "rule_engine:clear -> ml_model",
        }
        save_patient_record(summary_data)
        state["saved"] = True
        response_text = _intake_completion_message(profile, telugu_mode)
        if prediction_text:
            response_text = f"{response_text}\n\n{prediction_text}"
    elif not response_text:
        response_text = _next_intake_question(state, telugu_mode)

    decision_path = "rule_engine:clear -> intake"
    if is_complete:
        decision_path = "rule_engine:clear -> ml_model"

    return jsonify({
        "response": response_text,
        "is_complete": is_complete,
        "summary_data": summary_data,
        "emergency_alert": False,
        "decision_path": decision_path,
    })

def save_patient_record(summary_data):
    PATIENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    patients = _load_patients()
            
    summary_data["timestamp"] = datetime.now().isoformat()
    summary_data["id"] = "PT-" + str(len(patients) + 1).zfill(4)
    summary_data["status"] = "Waiting"
    
    patients.append(summary_data)
    _save_patients(patients)


def _load_patients():
    if not PATIENTS_FILE.exists():
        return []
    with PATIENTS_FILE.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []


def _save_patients(patients):
    PATIENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with PATIENTS_FILE.open("w", encoding="utf-8") as f:
        json.dump(patients, f, indent=4)

def process_fallback(user_message, original_error, state, telugu_mode=None):
    """Fallback logic when all AI engines fail."""
    print(f"[FALLBACK] Error: {original_error}")

    profile = state["profile"]
    if telugu_mode is None:
        telugu_mode = state.get("lang_pref", "en") == "te"
    is_complete = _is_intake_complete(state)
    summary_data = None
    if is_complete and not state["saved"]:
        summary_data = {
            "patient_name": profile.get("patient_name", "Unknown"),
            "age": profile.get("age", "Unknown"),
            "weight": profile.get("weight", "Unknown"),
            "phone": profile.get("phone", "Unknown"),
            "chief_complaint": profile.get("chief_complaint", f"Input: {user_message}"),
            "history_of_present_illness": profile.get("history_of_present_illness", "Processed in fallback mode."),
            "triage_level": profile.get("triage_level", "Medium"),
            "risk_score": profile.get("risk_score", 0),
            "risk_reasons": profile.get("risk_reasons", []),
            "symptoms": profile.get("symptoms", []),
        }
        save_patient_record(summary_data)
        state["saved"] = True
        mock_response = _intake_completion_message(profile, telugu_mode)
    else:
        mock_response = _next_intake_question(state, telugu_mode)
    
    return jsonify({
        "response": mock_response,
        "is_complete": is_complete,
        "summary_data": summary_data,
    })

@chat_bp.route('/patients', methods=['GET'])
def get_patients():
    """Endpoint for the Admin Portal to fetch all patient records."""
    return jsonify(_load_patients()), 200


@chat_bp.route('/patients/<patient_id>/status', methods=['PATCH'])
def update_patient_status(patient_id):
    data = request.get_json(silent=True) or {}
    new_status = data.get("status", "").strip()
    if new_status not in ALLOWED_STATUSES:
        return jsonify({
            "error": "Invalid status.",
            "allowed_statuses": sorted(ALLOWED_STATUSES),
        }), 400

    patients = _load_patients()
    for patient in patients:
        if patient.get("id") == patient_id:
            patient["status"] = new_status
            patient["status_updated_at"] = datetime.now().isoformat()
            _save_patients(patients)
            return jsonify(patient), 200

    return jsonify({"error": "Patient not found."}), 404


@chat_bp.route('/patients/insights', methods=['GET'])
def get_patient_insights():
    patients = _load_patients()
    total = len(patients)

    triage_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    status_counts = {status: 0 for status in sorted(ALLOWED_STATUSES)}
    risk_values = []

    for p in patients:
        triage = p.get("triage_level")
        if triage in triage_counts:
            triage_counts[triage] += 1
        status = p.get("status", "Waiting")
        if status not in status_counts:
            status_counts[status] = 0
        status_counts[status] += 1

        try:
            risk_values.append(float(p.get("risk_score", 0)))
        except Exception:
            pass

    avg_risk_score = round(sum(risk_values) / len(risk_values), 2) if risk_values else 0
    high_risk_count = triage_counts["Critical"] + triage_counts["High"]
    high_risk_ratio = round((high_risk_count / total) * 100, 2) if total else 0

    return jsonify({
        "total_patients": total,
        "triage_distribution": triage_counts,
        "status_distribution": status_counts,
        "average_risk_score": avg_risk_score,
        "high_risk_count": high_risk_count,
        "high_risk_ratio_percent": high_risk_ratio,
        "generated_at": datetime.now().isoformat(),
    }), 200


@chat_bp.route('/evaluation/report', methods=['GET'])
def evaluation_report():
    try:
        report = model_evaluator.generate_report()
        PERFORMANCE_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with PERFORMANCE_REPORT_FILE.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)
        return jsonify(report), 200
    except Exception as e:
        return jsonify({"error": f"Failed to generate report: {str(e)}"}), 500


