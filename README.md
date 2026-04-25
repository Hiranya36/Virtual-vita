# Virtual Vita – AI-Powered Clinical Decision Support System

## Overview

Virtual Vita is an intelligent AI-driven Clinical Decision Support System (CDSS) designed to streamline patient intake, automate triage, and assist clinicians with structured, real-time insights.

The system combines **rule-based clinical logic + Large Language Models (LLMs)** to ensure accurate, reliable, and explainable healthcare workflows.

---

## Key Features

* Hybrid AI Architecture (Local + Cloud)
* Multilingual Symptom Intake (English + Telugu)
* Real-time Risk Scoring & Triage Classification
* Emergency Detection & Instant Escalation
* Interactive Admin Dashboard with Analytics
* Privacy-focused Local Inference (Ollama)

---

## System Architecture

The system follows a **multi-layer architecture**:

* **Frontend**: React + Vite (User & Admin Dashboards)
* **Backend**: Flask REST APIs
* **AI Layer**:

  * Ollama (Llama 3.2 – Local Inference)
  * Google Gemini (Cloud Fallback)
* **Rule Engine**: Clinical logic for triage & risk scoring
* **Database**: PostgreSQL

---

## Tech Stack

* Python, Flask
* React, Vite, Tailwind CSS
* PostgreSQL
* Ollama (LLM)
* Google Gemini API
* Streamlit (Deployment UI)

---

## Workflow

1. Patient enters symptoms via chat interface
2. NLP module extracts structured data
3. Rule-based engine computes risk score
4. AI models generate contextual responses
5. System assigns triage level
6. Results stored and visualized for clinicians

---

## Screenshots

<img width="1914" height="915" alt="Screenshot 2026-04-25 094834" src="https://github.com/user-attachments/assets/4bf5fa8f-8e57-4f6c-958d-ba25190b7022" />
<img width="1903" height="911" alt="Screenshot 2026-04-25 110814" src="https://github.com/user-attachments/assets/b26f034e-b5a5-4251-9b71-3b03f7a30f89" />
<img width="1890" height="933" alt="Screenshot 2026-04-25 110828" src="https://github.com/user-attachments/assets/5c5b2c28-8e3b-4451-a2d1-7d049fa1c7e3" />


---

## Installation & Setup

```bash
git clone https://github.com/Hiranya36/Virtual-vita.git
cd Virtual-vita
```

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python run.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## Deployment

The project supports deployment using:

* Streamlit Cloud
* Render / Railway
* AWS (future scalability)

---

## Future Enhancements

* Integration with Hospital EHR/EMR systems
* Advanced predictive analytics
* Cloud-native microservices architecture
* Real-time IoT health monitoring

---

## Disclaimer

This system is intended for **educational and research purposes only** and should not be used for real clinical diagnosis. ([GitHub][1])

---

## Contribution

Contributions, issues, and feature requests are welcome!

---

## If you like this project

Give it a ⭐ on GitHub!

[1]: https://github.com/microsoft/healthcareai-examples?utm_source=chatgpt.com "microsoft/healthcareai-examples"
