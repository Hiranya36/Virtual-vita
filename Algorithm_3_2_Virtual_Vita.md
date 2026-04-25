# 3.2 Algorithm - Virtual Vita Clinical Intake and Decision Support

## Overview

This document explains the complete algorithm used by **Virtual Vita** for clinical intake, risk assessment, and preliminary disease prediction.  
The flow is designed as a **rule-first, safety-oriented pipeline** with optional LLM assistance for natural conversation.

The objective is to ensure that:
- patient details are captured consistently,
- follow-up questions are clinically relevant,
- risk is computed with explainable reasons,
- prediction remains preliminary and non-diagnostic,
- admin receives prioritizable patient records.

---

## High-Level Algorithm (8 Steps)

1. Receive patient message and active session context  
2. Extract demographic information from patient input  
3. Identify symptom focus area  
4. Use slot-based questioning logic to collect missing details  
5. Extract and normalize symptoms  
6. Compute risk score  
7. Generate disease prediction  
8. Assign triage category and store output

---

## Detailed Step-by-Step Explanation

### Step 1: Receive patient message and active session context

When a user sends a message to `/api/chat`, Virtual Vita:
- reads `message` and `session_id`,
- initializes a session state if it does not exist,
- loads current intake profile:
  - name, age, weight, phone
  - chief complaint
  - symptom list
  - risk score/reasons
  - slot completion state

This makes intake stateful and allows multi-turn conversations.

---

### Step 2: Extract demographic information from patient input

Virtual Vita applies multilingual parsing logic to detect:
- **Name**
- **Age**
- **Weight**
- **Phone number**

It supports:
- CSV-style compact input (example: `ravi, 34, 68, 9876231451`)
- English free-text patterns
- Telugu patterns (`నేను`, `వయసు`, `వెయిట్`, `ఫోన్ నెంబర్`)
- fallback simple-name capture (single-word name response)

The system continuously updates profile fields turn-by-turn; it does not require all demographics in one message.

---

### Step 3: Identify symptom focus area

After complaint/symptom extraction begins, Virtual Vita determines a **focus category**:
- `headache`
- `breathing`
- `chest`
- `abdominal`
- `fever`
- `general` (default)

Focus detection uses complaint text + normalized symptom terms.

This is important because each focus has different clinically useful follow-up questions.

---

### Step 4: Use slot-based questioning logic to collect missing details

Instead of fixed repetitive questions, Virtual Vita uses a **slot plan** per focus.

Common slots:
- `duration`
- `location`
- `severity`
- `associated`
- `trigger`
- `pattern`

Example plans:
- headache -> duration, location, severity, associated
- breathing -> duration, severity, associated, trigger
- abdominal -> duration, location, severity, associated

Algorithm behavior:
1. parse current user message for slot evidence,
2. mark detected slots as filled,
3. ask only the next missing slot question.

This prevents repeated or irrelevant questions and improves completeness.

---

### Step 5: Extract and normalize symptoms

Virtual Vita combines:
- dataset-based symptom extraction (`SymptomExtractor`)
- synonym mapping (English colloquial phrases)
- Telugu symptom mapping

Examples:
- `breathing problem` -> `breathlessness`
- `chest tightness` -> `chest pain`
- `body pains` -> `muscle pain`
- `జ్వరంగా ఉంది` -> `fever`

All symptoms are normalized into canonical terms before risk and prediction.

---

### Step 6: Compute risk score

Risk is computed by `RiskScorer` using:
- symptom severity weights (`Symptom-severity.csv`)
- high-alert symptom detection (e.g., chest pain, breathlessness)
- intensity clues from notes (`severe`, `intense`, etc.)
- age modifiers
- multi-symptom factor

Output:
- `risk_score` (0 to 100)
- `risk_reasons` (explainable text reasons)

This explanation is used directly in Admin Dashboard for clinical transparency.

---

### Step 7: Generate disease prediction

On intake completion (minimum detail quality reached), Virtual Vita:
- creates binary symptom vector,
- runs `DiseasePredictor` (Random Forest model),
- gets probable disease + description + precautions.

Important safety behavior:
- output is labeled as **Preliminary AI Assessment**
- not presented as confirmed diagnosis
- includes clear recommendation for clinical confirmation

---

### Step 8: Assign triage category and store output

From risk score, triage is assigned:
- `Low`
- `Medium`
- `High`
- `Critical`

Patient record is persisted with:
- demographics
- chief complaint + HPI notes
- symptoms
- risk score + reasons
- triage level
- preliminary prediction
- workflow status (`Waiting`, etc.)

This record is used by admin for queue prioritization and action.

---

## End-to-End Pseudocode

```text
function CHAT_HANDLER(message, session_id):
    state = get_or_create_session(session_id)
    profile = state.profile

    # 1) Demographics extraction
    extract_demographics(message, profile)

    # 2) Complaint + symptoms
    extract_complaint_and_symptoms(message, profile)

    # 3) Focus detection
    state.intake_focus = detect_focus(profile)

    # 4) Slot extraction
    newly_detected_slots = extract_detail_slots(message)
    state.detail_slots.update(newly_detected_slots)

    # 5) Risk update (incremental)
    risk_score, triage_level, reasons = risk_scorer.score(profile)
    profile.risk_score = risk_score
    profile.triage_level = triage_level
    profile.risk_reasons = reasons

    if intake_complete(state):
        prediction = predictor.predict(profile.symptoms)
        record = build_patient_record(profile, prediction)
        save_patient(record)
        return completion_message + safe_prediction_message
    else:
        next_q = next_question_by_focus_and_slots(state)
        return next_q
```

---

## Representative Core Sample Code (Project-Level)

```python
def chat():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Message is required"}), 400

    user_message = data["message"]
    session_id = data.get("session_id", "default_session")

    # Session bootstrap
    if session_id not in sessions:
        sessions[session_id] = _new_state()
    state = sessions[session_id]
    profile = state["profile"]

    # Language preference (English / Telugu)
    lang_pref = _resolve_lang_pref(state, user_message)
    telugu_mode = lang_pref == "te"

    # 1) Demographic extraction
    _extract_demographics(user_message, profile)

    # 2) Symptom + complaint extraction with multilingual mapping
    _extract_complaint_and_symptoms(user_message, profile)

    # 3) Detect symptom focus for dynamic questioning
    state["intake_focus"] = _detect_focus(profile)

    # 4) Fill detail slots from current user text
    detected_slots = _extract_detail_slots(user_message)
    for slot, ok in detected_slots.items():
        if ok:
            state["detail_slots"][slot] = True

    # Keep backward-compatible numeric counter
    state["post_demo_details_count"] = max(
        state.get("post_demo_details_count", 0),
        len(state.get("detail_slots", {})),
    )

    # 5) Recompute explainable risk each turn
    risk_score, triage_level, risk_reasons = risk_scorer.score(profile)
    profile["risk_score"] = risk_score
    profile["triage_level"] = triage_level
    profile["risk_reasons"] = risk_reasons

    # 6) Decide next action
    is_complete = _is_intake_complete(state)

    if is_complete and not state["saved"]:
        # 7) Run preliminary disease prediction (non-diagnostic wording)
        prediction_text, prediction_payload = _build_preliminary_prediction(profile, telugu_mode)

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
            "preliminary_prediction": prediction_payload,
        }

        save_patient_record(summary_data)
        state["saved"] = True

        completion_msg = _intake_completion_message(profile, telugu_mode)
        if prediction_text:
            completion_msg = f"{completion_msg}\n\n{prediction_text}"

        return jsonify({
            "response": completion_msg,
            "is_complete": True,
            "summary_data": summary_data
        })

    # 8) Ask next missing slot question (rule-based deterministic flow)
    next_q = _next_intake_question(state, telugu_mode)
    return jsonify({
        "response": next_q,
        "is_complete": False,
        "summary_data": None
    })
```

This code captures the main project behavior:
- stateful chat intake
- multilingual extraction
- rule-based slot completion
- explainable risk scoring
- preliminary prediction generation
- patient record persistence for admin triage

---

## How We Used This in Virtual Vita

### A) For patient-facing intake reliability
- deterministic slot engine is default,
- avoids dependency on LLM uptime/latency,
- ensures minimum data quality before prediction.

### B) For multilingual behavior
- English and Telugu parsing rules are integrated in extraction and symptom mapping,
- prevents complaint-loss in Telugu messages.

### C) For risk-aware prioritization
- risk is recomputed every turn,
- high-alert and severe-intensity clues can increase urgency quickly,
- explainable risk reasons are saved for doctors.

### D) For clinical workflow
- structured record is pushed to admin side,
- triage + risk score controls queue order,
- status lifecycle supports operations (`Waiting -> In Review -> Escalated -> Closed`).

### E) For safe AI usage
- disease prediction is preliminary only,
- wording avoids deterministic diagnosis claims,
- clinician remains final decision-maker.

---

## Algorithm Strengths

- Explainable and auditable (risk reasons + slot state)
- Robust to noisy user input (synonym maps, typo handling)
- Works even when LLM is unavailable
- Supports multilingual intake (English/Telugu)
- Easy to extend with new symptom focus plans

---

## Current Limitations and Future Enhancements

1. Rule base can still miss rare colloquial expressions  
2. Disease model quality depends on dataset representativeness  
3. Prediction confidence calibration can be improved  
4. Future version can add:
   - larger medical phrase dictionary,
   - confidence thresholds,
   - clinical red-flag override rules,
   - richer specialty routing.

---

## Conclusion

The Virtual Vita algorithm combines deterministic intake control, explainable risk computation, and ML-based preliminary prediction in a single pipeline.  
This architecture is practical for real-world high-load scenarios because it is stable, fast, and clinically interpretable while keeping final diagnosis authority with healthcare professionals.

