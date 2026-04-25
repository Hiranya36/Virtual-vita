import hmac
import os
import subprocess

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import requests
import streamlit as st

PAGE_KEYS = ("patient", "admin", "eval")
LEGACY_PAGE = {
    "Patient Intake Chat": "patient",
    "Admin Dashboard": "admin",
    "Evaluation & Reports": "eval",
}


def normalize_page_key(p):
    if p in PAGE_KEYS:
        return p
    return LEGACY_PAGE.get(str(p), "patient")


def texts(lang: str) -> dict:
    return STRINGS["te" if lang == "te" else "en"]


def get_auth_passwords() -> Tuple[str, str, bool]:
    """
    (user_password, admin_password, using_demo)
    Set VV_USER_PASSWORD and VV_ADMIN_PASSWORD, or in .streamlit/secrets.toml: user_password / admin_password.
    """
    u = a = None
    try:
        s = st.secrets
        u = s.get("user_password")
        a = s.get("admin_password")
    except Exception:
        pass
    u = (u or os.environ.get("VV_USER_PASSWORD") or "").strip()
    a = (a or os.environ.get("VV_ADMIN_PASSWORD") or "").strip()
    if u and a:
        return u, a, False
    return "vita_user", "vita_admin", True


def _same_password(entered: str, expected: str) -> bool:
    if not expected:
        return False
    if not entered:
        return False
    try:
        return hmac.compare_digest(entered.encode("utf-8"), expected.encode("utf-8"))
    except Exception:
        return False


def transcribe_audio_blob(blob: bytes, lang: str) -> Optional[str]:
    if not blob:
        return None
    try:
        import speech_recognition as sr
    except ImportError:
        return None
    r = sr.Recognizer()
    path = None
    try:
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.write(fd, blob)
        os.close(fd)
        with sr.AudioFile(path) as source:
            audio_data = r.record(source)
        code = "te-IN" if lang == "te" else "en-IN"
        return r.recognize_google(audio_data, language=code)
    except Exception:
        return None
    finally:
        if path:
            try:
                os.unlink(path)
            except OSError:
                pass


STRINGS = {
    "en": {
        "subtitle": "AI-powered clinical intake, triage, and decision support",
        "nav": "Navigation",
        "settings": "Settings",
        "theme_caption": "Theme: Glass UI",
        "lang_label": "App language",
        "page_patient": "Patient Intake Chat",
        "page_admin": "Admin Dashboard",
        "page_eval": "Evaluation & Reports",
        "greeting": (
            "Hello! I am Virtual Vita, your AI Intake Nurse. Please share your Name, Age, Weight, "
            "and Phone number before we begin discussing your symptoms."
        ),
        "patient_title": "Patient Intake Chat",
        "chat_placeholder": "Message Virtual Vita…",
        "restart_help": "New chat (clears this conversation)",
        "mic_help": "Voice message — record, review transcript, then send to the chat",
        "voice_popover_hint": "Record a short clip, then add it to the chat. Internet access may be required for transcription.",
        "voice_label": " ",
        "no_response": "Sorry, I couldn’t generate a response.",
        "backend_error": "Backend error",
        "send_transcript": "Send transcript to chat",
        "voice_pkg": "Install SpeechRecognition: pip install SpeechRecognition",
        "voice_unclear": "Could not transcribe clearly. Try again or type your message.",
        "voice_upgrade": "Upgrade Streamlit (>=1.33) for microphone recording in the browser.",
        "admin_title": "Admin Dashboard",
        "load_fail": "Failed to load patients",
        "m_total": "Total",
        "m_high": "High Risk",
        "m_high_pct": "High Risk %",
        "m_avg": "Avg Risk",
        "queue": "Patient Queue",
        "click_row": "Click a row to view details",
        "sel_id": "Select Patient ID",
        "intake_summary": "Intake Summary",
        "k_triage": "Triage",
        "k_risk": "Risk",
        "k_status": "Status",
        "k_cc": "Chief Complaint",
        "k_hpi": "HPI / Notes",
        "actions": "Actions",
        "upd_status": "Update workflow status",
        "save": "Save",
        "saved": "Saved. Status",
        "save_fail": "Failed to save",
        "eval_title": "Evaluation & Reports",
        "refresh": "Refresh report",
        "updated": "Updated.",
        "gen_graphs": "Generate graphs",
        "graphs_ok": "Graphs generated.",
        "graphs_fail": "Graph generation failed",
        "eval_cap": "Graphs and metrics are generated from stored evaluation results.",
        "report_fail": "Failed to load report",
        "tab_sum": "Summary",
        "tab_json": "Raw JSON",
        "tab_graphs": "Graphs",
        "m_acc": "Accuracy",
        "m_f1": "Macro F1",
        "m_p95": "P95 Latency",
        "m_max": "Max Latency",
        "eval_note": "This section summarizes evaluation results. (Perfect scores may occur on highly structured datasets.)",
        "graphs_missing": "Graphs not found yet. Click 'Generate graphs'.",
        "cap_g1": "Model quality metrics",
        "cap_g2": "Response time across runs (simulated)",
        "cap_g3": "Triage distribution",
        "cap_g4": "Workflow status distribution",
        "cap_g5": "Before/After handling time reduction (simulated)",
        "col_id": "ID",
        "col_name": "Patient",
        "col_triage": "Triage",
        "col_risk": "Risk",
        "col_status": "Status",
        "col_cc": "Chief complaint",
        "tri": {
            "Critical": "Critical",
            "High": "High",
            "Medium": "Medium",
            "Low": "Low",
        },
        "st": {
            "Waiting": "Waiting",
            "In Review": "In Review",
            "Escalated": "Escalated",
            "Closed": "Closed",
        },
        "login_title": "Sign in to Virtual Vita",
        "login_as": "Sign in as",
        "login_user": "User",
        "login_admin": "Admin",
        "password": "Password",
        "sign_in": "Sign in",
        "bad_password": "Incorrect password.",
        "demo_login_hint": "Demo mode: set VV_USER_PASSWORD and VV_ADMIN_PASSWORD in the environment, or add user_password / admin_password in .streamlit/secrets.toml. Default demo passwords: user **vita_user** / admin **vita_admin** (change in production).",
        "logout": "Log out",
        "signed_in": "Signed in as",
        "admin_only": "You need the Admin sign-in to open that page. Switched to Patient chat.",
    },
    "te": {
        "subtitle": "AI ఆధారిత క్లినికల్ ఇంటేక్, ట్రయాజ్ మరియు నిర్ణయ మద్దతు",
        "nav": "నావిగేషన్",
        "settings": "సెట్టింగ్‌లు",
        "theme_caption": "థీమ్: గ్లాస్ UI",
        "lang_label": "అనువాద భాష",
        "page_patient": "రోగి స్వీకార చాట్",
        "page_admin": "నిర్వాహక డాష్‌బోర్డ్",
        "page_eval": "మూల్యాంకనం & నివేదికలు",
        "greeting": (
            "నమస్కారం! నేను వర్చువల్ విటా, మీ AI ఇంటేక్ నర్స్. మీ లక్షణాల గురించి మాట్లాడే ముందు "
            "దయచేసి మీ పేరు, వయస్సు, బరువు మరియు ఫోన్ నంబర్ ఇవ్వండి."
        ),
        "patient_title": "రోగి స్వీకార చాట్",
        "chat_placeholder": "వర్చువల్ విటాకు సందేశం…",
        "restart_help": "కొత్త చాట్ (చాట్ శుభ్రం)",
        "mic_help": "వాయిస్ — రికార్డ్ చేసి, ట్రాన్స్‌క్రిప్ట్‌ని చాట్‌లోకి పంపండి",
        "voice_popover_hint": "చిన్న క్లిప్ రికార్డ్ చేసి, చాట్‌లోకి కలపండి. ట్రాన్స్‌క్రిప్షన్ కోసం నెట్‌వర్క్ అవసరం కావచ్చు.",
        "voice_label": " ",
        "no_response": "స్పందన రాలేదు. మళ్లీ ప్రయత్నించండి.",
        "backend_error": "బ్యాకెండ్ లోపం",
        "send_transcript": "ట్రాన్స్‌క్రిప్ట్‌ని చాట్‌కు పంపు",
        "voice_pkg": "SpeechRecognition ఇన్‌స్టాల్: pip install SpeechRecognition",
        "voice_unclear": "స్పష్టంగా ట్రాన్స్‌క్రైబ్ చేయలేకపోయాం. మళ్లీ లేదా టైప్ చేయండి.",
        "voice_upgrade": "మైక్రోఫోన్ కోసం Streamlit ను 1.33+ కు అప్‌గ్రేడ్ చేయండి.",
        "admin_title": "నిర్వాహక డాష్‌బోర్డ్",
        "load_fail": "రోగుల డేటా లోడ్ విఫలమైంది",
        "m_total": "మొత్తం",
        "m_high": "అధిక ప్రమాదం",
        "m_high_pct": "అధిక ప్రమాదం %",
        "m_avg": "సగటు ప్రమాదం",
        "queue": "రోగుల క్యూ",
        "click_row": "వివరాల కోసం వరుస క్లిక్ చేయండి",
        "sel_id": "రోగి ID ఎంచుకోండి",
        "intake_summary": "స్వీకార సారాంశం",
        "k_triage": "ట్రయాజ్",
        "k_risk": "ప్రమాదం",
        "k_status": "స్థితి",
        "k_cc": "ప్రధాన ఫిర్యాదు",
        "k_hpi": "HPI / గమనికలు",
        "actions": "చర్యలు",
        "upd_status": "వర్క్‌ఫ్లో స్థితి నవీకరించండి",
        "save": "సేవ్",
        "saved": "సేవ్ అయింది. స్థితి",
        "save_fail": "సేవ్ విఫలమైంది",
        "eval_title": "మూల్యాంకనం & నివేదికలు",
        "refresh": "నివేదిక రిఫ్రెష్",
        "updated": "నవీకరించబడింది.",
        "gen_graphs": "గ్రాఫ్‌లు రూపొందించు",
        "graphs_ok": "గ్రాఫ్‌లు సిద్ధం.",
        "graphs_fail": "గ్రాఫ్‌లు విఫలమయ్యాయి",
        "eval_cap": "గ్రాఫ్‌లు మరియు మెట్రిక్‌లు నిల్వ చేసిన మూల్యాంకనం నుండి వస్తాయి.",
        "report_fail": "నివేదిక లోడ్ విఫలమైంది",
        "tab_sum": "సారాంశం",
        "tab_json": "Raw JSON",
        "tab_graphs": "గ్రాఫ్‌లు",
        "m_acc": "ఖచ్చితత్వం",
        "m_f1": "Macro F1",
        "m_p95": "P95 విలంబం",
        "m_max": "గరిష్ట విలంబం",
        "eval_note": "ఈ విభాగం మూల్యాంకన ఫలితాలను సారాంశపరుస్తుంది.",
        "graphs_missing": "గ్రాఫ్‌లు లేవు. 'గ్రాఫ్‌లు రూపొందించు' క్లిక్ చేయండి.",
        "cap_g1": "నమూనా నాణ్యత మెట్రిక్‌లు",
        "cap_g2": "ప్రతిస్పందన సమయం (సిమ్యులేటెడ్)",
        "cap_g3": "ట్రయాజ్ పంపిణీ",
        "cap_g4": "వర్క్‌ఫ్లో స్థితి పంపిణీ",
        "cap_g5": "ముందు/తర్వాత హ్యాండ్లింగ్ సమయ తగ్గింపు (సిమ్యులేటెడ్)",
        "col_id": "ID",
        "col_name": "రోగి",
        "col_triage": "ట్రయాజ్",
        "col_risk": "ప్రమాదం",
        "col_status": "స్థితి",
        "col_cc": "ప్రధాన ఫిర్యాదు",
        "tri": {
            "Critical": "గురుతరం",
            "High": "అధికం",
            "Medium": "మధ్యస్థం",
            "Low": "తక్కువ",
        },
        "st": {
            "Waiting": "వేచి",
            "In Review": "సమీక్షలో",
            "Escalated": "ఎస్కలేట్",
            "Closed": "మూసివేయబడింది",
        },
        "login_title": "Virtual Vita లో సైన్ ఇన్",
        "login_as": "గా సైన్ ఇన్",
        "login_user": "యూజర్",
        "login_admin": "అడ్మిన్",
        "password": "పాస్‌వర్డ్",
        "sign_in": "సైన్ ఇన్",
        "bad_password": "తప్పు పాస్‌వర్డ్.",
        "demo_login_hint": "డెమో: VV_USER_PASSWORD / VV_ADMIN_PASSWORD లేదా secrets.toml. డిఫాల్ట్ vita_user / vita_admin (ప్రొడక్షన్‌లో మార్చండి).",
        "logout": "లాగ్ అవుట్",
        "signed_in": "సైన్ ఇన్:",
        "admin_only": "అడ్మిన్ పేజీ కోసం అడ్మిన్ లాగిన్ కావాలి. రోగి చాట్‌కు మార్చబడింది.",
    },
}


def inject_css():
    st.markdown(
        """
        <style>
          .stApp {
            background:
              radial-gradient(1000px 500px at 10% -10%, rgba(99,102,241,0.28), transparent 60%),
              radial-gradient(900px 500px at 90% 0%, rgba(16,185,129,0.22), transparent 60%),
              radial-gradient(1200px 700px at 50% 120%, rgba(236,72,153,0.18), transparent 60%),
              linear-gradient(180deg, #070b18 0%, #090f22 50%, #060914 100%);
          }
          .vv-title {
            font-size: 2.35rem;
            font-weight: 900;
            letter-spacing: -0.03em;
            margin: 0.1rem 0 0.55rem 0;
            background: linear-gradient(92deg, #7dd3fc, #a5b4fc, #c4b5fd, #6ee7b7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 30px rgba(165,180,252,0.28);
          }
          .vv-subtitle {
            color: rgba(209,213,219,0.88);
            margin-top: -0.5rem;
            margin-bottom: 0.6rem;
          }
          .vv-card {
            border: 1px solid rgba(255,255,255,0.14);
            background: linear-gradient(135deg, rgba(255,255,255,0.12), rgba(255,255,255,0.03));
            backdrop-filter: blur(10px);
            border-radius: 18px;
            padding: 14px 14px;
            box-shadow:
              0 18px 42px rgba(0,0,0,0.34),
              inset 0 1px 0 rgba(255,255,255,0.2);
          }
          .vv-badge {
            display:inline-block;
            padding: 0.22rem 0.6rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 700;
            border: 1px solid rgba(255,255,255,0.2);
            background: linear-gradient(120deg, rgba(99,102,241,0.25), rgba(16,185,129,0.22));
            box-shadow: 0 6px 16px rgba(0,0,0,0.2);
          }
          .vv-legend {
            display:flex;
            gap:10px;
            flex-wrap:wrap;
            margin: 8px 0 14px 0;
          }
          .vv-chip {
            padding: 0.28rem 0.7rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 800;
            border: 1px solid rgba(255,255,255,0.2);
            box-shadow: 0 6px 14px rgba(0,0,0,0.2);
          }
          .vv-critical { background: linear-gradient(120deg, rgba(239,68,68,0.35), rgba(220,38,38,0.28)); }
          .vv-high { background: linear-gradient(120deg, rgba(251,146,60,0.35), rgba(249,115,22,0.28)); }
          .vv-medium { background: linear-gradient(120deg, rgba(250,204,21,0.35), rgba(234,179,8,0.28)); }
          .vv-low { background: linear-gradient(120deg, rgba(74,222,128,0.35), rgba(34,197,94,0.28)); }
          .vv-waiting { background: linear-gradient(120deg, rgba(59,130,246,0.35), rgba(37,99,235,0.28)); }
          .vv-review { background: linear-gradient(120deg, rgba(168,85,247,0.35), rgba(147,51,234,0.28)); }
          .vv-escalated { background: linear-gradient(120deg, rgba(244,63,94,0.35), rgba(225,29,72,0.28)); }
          .vv-closed { background: linear-gradient(120deg, rgba(107,114,128,0.35), rgba(75,85,99,0.28)); }
          .vv-row {
            display:flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 10px;
          }
          .vv-kv {
            flex: 1 1 220px;
            border-radius: 16px;
            padding: 10px 12px;
            border: 1px solid rgba(255,255,255,0.14);
            background: linear-gradient(140deg, rgba(255,255,255,0.08), rgba(255,255,255,0.025));
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.12);
          }
          .vv-k { color: rgba(156,163,175,0.95); font-size: 0.78rem; margin-bottom: 6px; }
          .vv-v { font-weight: 800; font-size: 1.05rem; }
          .vv-small { font-size: 0.85rem; color: rgba(209,213,219,0.85); }
          section[data-testid="stSidebar"] {
            background: linear-gradient(160deg, rgba(255,255,255,0.12), rgba(255,255,255,0.03)) !important;
            backdrop-filter: blur(14px) saturate(1.2);
            border-right: 1px solid rgba(255,255,255,0.14);
            box-shadow: inset -1px 0 0 rgba(255,255,255,0.08);
          }
          .stRadio > label { font-weight: 800; color: rgba(241,245,249,0.95); }
          .vv-nav-btn {
            width: 100%;
            border: 1px solid rgba(255,255,255,0.14);
            background: linear-gradient(130deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));
            color: rgba(241,245,249,0.96);
            border-radius: 12px;
            padding: 10px 12px;
            margin-bottom: 8px;
            font-weight: 700;
            box-shadow: 0 8px 18px rgba(0,0,0,0.22), inset 0 1px 0 rgba(255,255,255,0.15);
          }
          .vv-nav-btn-active {
            border: 1px solid rgba(147,197,253,0.6);
            background: linear-gradient(130deg, rgba(59,130,246,0.35), rgba(16,185,129,0.28));
            box-shadow: 0 10px 22px rgba(37,99,235,0.35), inset 0 1px 0 rgba(255,255,255,0.18);
          }
          div[data-testid="stDataFrame"] {
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.14);
            box-shadow: 0 12px 30px rgba(0,0,0,0.25);
          }
          button[kind="primary"] {
            border: 1px solid rgba(255,255,255,0.22) !important;
            background: linear-gradient(130deg, #7c3aed, #2563eb, #0891b2) !important;
            box-shadow: 0 12px 22px rgba(37,99,235,0.35), inset 0 1px 0 rgba(255,255,255,0.25);
            border-radius: 12px !important;
            transform: translateY(0);
            transition: all .2s ease;
          }
          button[kind="primary"]:hover { transform: translateY(-1px); filter: brightness(1.06); }
          .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: rgba(255,255,255,0.04);
            padding: 6px;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
          }
          .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            padding: 10px 16px;
          }
          .stTabs [aria-selected="true"] {
            background: linear-gradient(120deg, rgba(59,130,246,0.25), rgba(16,185,129,0.2)) !important;
            border: 1px solid rgba(255,255,255,0.15) !important;
          }
          [data-testid="stMetric"] {
            background: linear-gradient(140deg, rgba(255,255,255,0.1), rgba(255,255,255,0.02));
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 14px;
            padding: 8px 10px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
          }
          div[data-testid="stChatMessage"]:has(.user-msg-marker) {
            flex-direction: row-reverse;
            background: linear-gradient(135deg, rgba(236,72,153,0.15), rgba(244,63,94,0.1));
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 20px;
            border-bottom-right-radius: 4px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.25);
            padding: 1.2rem;
            margin-bottom: 1.5rem;
            backdrop-filter: blur(12px);
          }
          div[data-testid="stChatMessage"]:has(.user-msg-marker) div[data-testid="chatAvatarIcon-user"] {
            margin-left: 1rem;
            margin-right: 0;
          }
          div[data-testid="stChatMessage"]:has(.ai-msg-marker) {
            background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(16,185,129,0.1));
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 20px;
            border-bottom-left-radius: 4px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.25);
            padding: 1.2rem;
            margin-bottom: 1.5rem;
            backdrop-filter: blur(12px);
          }
          button[kind="secondary"] {
            background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.03)) !important;
            border: 1px solid rgba(255,255,255,0.15) !important;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.25), inset 0 -3px 0 rgba(0,0,0,0.2) !important;
            border-radius: 14px !important;
            backdrop-filter: blur(12px) !important;
            color: rgba(255,255,255,0.95) !important;
            transform: translateY(0);
            transition: all 0.2s ease;
          }
          button[kind="secondary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.35), inset 0 -3px 0 rgba(0,0,0,0.2) !important;
          }
          button[kind="secondary"]:active {
            transform: translateY(1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1), inset 0 1px 0 rgba(255,255,255,0.1), inset 0 2px 0 rgba(0,0,0,0.3) !important;
          }
          button[kind="secondary"] p {
            font-size: 1.05rem;
            font-weight: 700;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def api_base() -> str:
    return os.getenv("VIRTUAL_VITA_API_BASE", "http://localhost:8000").rstrip("/")


def api_get(path: str):
    r = requests.get(f"{api_base()}{path}", timeout=20)
    r.raise_for_status()
    return r.json()


def api_post(path: str, payload: dict):
    r = requests.post(f"{api_base()}{path}", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def api_patch(path: str, payload: dict):
    r = requests.patch(f"{api_base()}{path}", json=payload, timeout=20)
    r.raise_for_status()
    return r.json()


def login_page():
    if "ui_lang" not in st.session_state:
        st.session_state.ui_lang = "en"
    T0 = texts(st.session_state.ui_lang)
    st.markdown(
        f'<div class="vv-title" style="text-align:center">Virtual Vita</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="vv-subtitle" style="text-align:center;margin:0 0 1rem 0;">{T0["subtitle"]}</p>',
        unsafe_allow_html=True,
    )
    lang = st.selectbox(
        T0["lang_label"],
        options=["en", "te"],
        index=0 if st.session_state.ui_lang == "en" else 1,
        format_func=lambda x: "English" if x == "en" else "తెలుగు",
        key="pre_login_ui_lang",
    )
    if lang != st.session_state.ui_lang:
        st.session_state.ui_lang = lang
        st.rerun()
    T = texts(st.session_state.ui_lang)
    u_pwd, a_pwd, demo = get_auth_passwords()

    st.markdown("<br/>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👥 Patient Intake (No Login)", use_container_width=True):
            st.session_state.auth_role = "user"
            st.rerun()
            
    with col2:
        if st.button("🛡️ Admin Portal", use_container_width=True):
            st.session_state.show_admin_login = True
            st.rerun()

    if st.session_state.get("show_admin_login"):
        st.markdown(f"<br/>### Admin Access", unsafe_allow_html=True)
        
        import json
        import os
        ADMIN_FILE = "admin_users.json"
        
        def load_admins():
            if os.path.exists(ADMIN_FILE):
                try:
                    with open(ADMIN_FILE, "r") as f:
                        return json.load(f)
                except:
                    return {}
            return {}
            
        def save_admins(admins):
            with open(ADMIN_FILE, "w") as f:
                json.dump(admins, f)

        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        
        with tab1:
            with st.form("admin_login_form"):
                email = st.text_input("Email", key="login_email")
                pwd = st.text_input(T["password"], type="password", key="login_pw")
                if st.form_submit_button(T["sign_in"], use_container_width=True, type="primary"):
                    admins = load_admins()
                    if email in admins and admins[email] == pwd:
                        st.session_state.auth_role = "admin"
                        st.rerun()
                    elif demo and email == "admin" and pwd == a_pwd:
                        # Fallback for demo
                        st.session_state.auth_role = "admin"
                        st.rerun()
                    else:
                        st.error(T["bad_password"])
                        
        with tab2:
            with st.form("admin_signup_form"):
                new_email = st.text_input("New Email", key="signup_email")
                new_pwd = st.text_input("New Password", type="password", key="signup_pw")
                if st.form_submit_button("Sign Up", use_container_width=True, type="primary"):
                    if not new_email or not new_pwd:
                        st.error("Please provide both email and password")
                    else:
                        admins = load_admins()
                        if new_email in admins:
                            st.error("Email already registered")
                        else:
                            admins[new_email] = new_pwd
                            save_admins(admins)
                            st.success("Registered successfully! Please sign in via the Sign In tab.")

    if demo and st.session_state.get("show_admin_login"):
        st.info("Demo Mode Active: You can also use email 'admin' and password 'vita_admin'")


def render_voice_recording(T, lang: str) -> None:
    st.caption(T["voice_popover_hint"])
    if hasattr(st, "audio_input"):
        audio = st.audio_input(
            T["voice_label"] or " ",
            label_visibility="collapsed",
        )
        if audio is not None:
            blob = audio.getvalue() if hasattr(audio, "getvalue") else audio.read()
            h = hash(blob)
            if st.session_state.get("_vv_audio_hash") != h:
                st.session_state._vv_audio_hash = h
                try:
                    import speech_recognition  # noqa: F401
                except ImportError:
                    st.session_state._vv_transcript = None
                    st.warning(T["voice_pkg"])
                else:
                    st.session_state._vv_transcript = transcribe_audio_blob(blob, lang)
        tr = st.session_state.get("_vv_transcript")
        if tr:
            st.info(tr)
            if st.button(T["send_transcript"], key="vv_send_tr_pop", use_container_width=True):
                st.session_state.vv_flush_chat_message = tr
                st.session_state._vv_transcript = None
                st.session_state._vv_audio_hash = None
                st.rerun()
    else:
        st.caption(T["voice_upgrade"])


def init_state(T: dict, lang: str):
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"st_{datetime.now().timestamp()}"
    prev = st.session_state.get("_vv_chat_lang")
    if "messages" not in st.session_state or prev != lang:
        st.session_state._vv_chat_lang = lang
        st.session_state.messages = [{"role": "assistant", "content": T["greeting"]}]


def _reset_patient_session():
    st.session_state.pop("messages", None)
    st.session_state.pop("_vv_chat_lang", None)
    st.session_state.session_id = f"st_{datetime.now().timestamp()}"
    st.session_state._vv_transcript = None
    st.session_state._vv_audio_hash = None


def patient_chat():
    lang = st.session_state.get("ui_lang", "en")
    T = texts(lang)
    t_col, r_col = st.columns([0.9, 0.1])
    with t_col:
        st.subheader(T["patient_title"])
    with r_col:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("↻", key="vv_new_chat_top", help=T["restart_help"]):
            _reset_patient_session()
            st.rerun()
    init_state(T, lang)

    for msg in st.session_state.messages:
        with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
            if msg["role"] == "assistant":
                st.markdown('<span class="ai-msg-marker"></span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="user-msg-marker"></span>', unsafe_allow_html=True)
            st.write(msg["content"])

    flush = st.session_state.pop("vv_flush_chat_message", None)
    with st.container():
        mic_c, text_c = st.columns([0.12, 0.99])
        with mic_c:
            st.markdown(
                """
                <style> section[data-testid="stPopover"] > button, div.vv-mic-fallback { min-height: 2.5rem; } </style>
                """,
                unsafe_allow_html=True,
            )
            if hasattr(st, "popover"):
                with st.popover("🎤", use_container_width=True, help=T["mic_help"]):
                    render_voice_recording(T, lang)
            else:
                st.markdown('<div class="vv-mic-fallback">', unsafe_allow_html=True)
                if st.button("🎤", key="vv_mic_narrow", use_container_width=True, help=T["mic_help"]):
                    st.session_state._vv_expanded = not st.session_state.get("_vv_expanded", False)
                if st.session_state.get("_vv_expanded"):
                    render_voice_recording(T, lang)
                st.markdown("</div>", unsafe_allow_html=True)
        with text_c:
            raw = st.chat_input(
                T["chat_placeholder"],
                key="vv_chat_in",
            )
    user_text = flush or raw
    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown('<span class="user-msg-marker"></span>', unsafe_allow_html=True)
            st.write(user_text)

        try:
            data = api_post(
                "/api/chat",
                {
                    "message": user_text,
                    "session_id": st.session_state.session_id,
                    "ui_language": lang,
                },
            )
            bot_text = data.get("response") or T["no_response"]
            st.session_state.messages.append({"role": "assistant", "content": bot_text})
            with st.chat_message("assistant"):
                st.markdown('<span class="ai-msg-marker"></span>', unsafe_allow_html=True)
                st.write(bot_text)
        except Exception as e:
            with st.chat_message("assistant"):
                st.markdown('<span class="ai-msg-marker"></span>', unsafe_allow_html=True)
                st.error(f"{T['backend_error']}: {e}")


def admin_dashboard():
    lang = st.session_state.get("ui_lang", "en")
    T = texts(lang)
    st.subheader(T["admin_title"])

    try:
        insights = api_get("/api/patients/insights")
        patients = api_get("/api/patients")
    except Exception as e:
        st.error(f"{T['load_fail']}: {e}")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(T["m_total"], insights.get("total_patients", len(patients)))
    c2.metric(T["m_high"], insights.get("high_risk_count", 0))
    c3.metric(T["m_high_pct"], f"{insights.get('high_risk_ratio_percent', 0)}%")
    c4.metric(T["m_avg"], f"{insights.get('average_risk_score', 0)}/100")

    tri_meta = (
        ("Critical", "vv-critical"),
        ("High", "vv-high"),
        ("Medium", "vv-medium"),
        ("Low", "vv-low"),
    )
    tri_leg = " ".join(
        f'<span class="vv-chip {css}">{T["tri"].get(k, k)}</span>' for k, css in tri_meta
    )
    st.markdown(f'<div class="vv-legend">{tri_leg}</div>', unsafe_allow_html=True)
    st_meta = (
        ("Waiting", "vv-waiting"),
        ("In Review", "vv-review"),
        ("Escalated", "vv-escalated"),
        ("Closed", "vv-closed"),
    )
    st_leg = " ".join(
        f'<span class="vv-chip {css}">{T["st"].get(k, k)}</span>' for k, css in st_meta
    )
    st.markdown(f'<div class="vv-legend">{st_leg}</div>', unsafe_allow_html=True)

    st.write(f"### {T['queue']}")
    triage_priority = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    patients_sorted = sorted(
        patients,
        key=lambda p: (
            triage_priority.get(p.get("triage_level", "Low"), 9),
            -(p.get("risk_score") or 0),
        ),
    )

    view_rows = []
    triage_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
    st_icon = {"Waiting": "⏳", "In Review": "👁", "Escalated": "🚨", "Closed": "✅"}
    for p in patients_sorted:
        tri = p.get("triage_level", "Low")
        stv = p.get("status", "Waiting")
        tri_txt = T["tri"].get(tri, tri)
        st_txt = T["st"].get(stv, stv)
        view_rows.append(
            {
                "id": p.get("id"),
                "name": p.get("patient_name"),
                "triage": f"{triage_icon.get(tri, '⚪')} {tri_txt}",
                "risk": p.get("risk_score", 0),
                "status": f"{st_icon.get(stv, '⚪')} {st_txt}",
                "chief_complaint": p.get("chief_complaint", ""),
            }
        )
    df = pd.DataFrame(view_rows)

    def _triage_style(val):
        s = str(val)
        if s.startswith("🔴"):
            return "color:#fecaca;background-color:rgba(239,68,68,0.25);font-weight:700;border-radius:8px;"
        if s.startswith("🟠"):
            return "color:#fdba74;background-color:rgba(249,115,22,0.22);font-weight:700;border-radius:8px;"
        if s.startswith("🟡"):
            return "color:#fde047;background-color:rgba(234,179,8,0.22);font-weight:700;border-radius:8px;"
        if s.startswith("🟢"):
            return "color:#86efac;background-color:rgba(34,197,94,0.22);font-weight:700;border-radius:8px;"
        return ""

    def _status_style(val):
        s = str(val)
        if s.startswith("⏳"):
            return "color:#bfdbfe;background-color:rgba(37,99,235,0.22);font-weight:700;border-radius:8px;"
        if s.startswith("👁"):
            return "color:#ddd6fe;background-color:rgba(147,51,234,0.22);font-weight:700;border-radius:8px;"
        if s.startswith("🚨"):
            return "color:#fecdd3;background-color:rgba(225,29,72,0.24);font-weight:700;border-radius:8px;"
        if s.startswith("✅"):
            return "color:#d1d5db;background-color:rgba(75,85,99,0.28);font-weight:700;border-radius:8px;"
        return ""

    styled_df = df.style.map(_triage_style, subset=["triage"]).map(_status_style, subset=["status"])
    st.write(f"### {T['click_row']}")

    selection = st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "id": st.column_config.TextColumn(T["col_id"], width="small"),
            "name": st.column_config.TextColumn(T["col_name"], width="medium"),
            "triage": st.column_config.TextColumn(T["col_triage"], width="small"),
            "risk": st.column_config.NumberColumn(T["col_risk"], width="small"),
            "status": st.column_config.TextColumn(T["col_status"], width="small"),
            "chief_complaint": st.column_config.TextColumn(T["col_cc"], width="large"),
        },
    )

    selected = None
    try:
        selected_rows = (selection or {}).get("selection", {}).get("rows", [])
        if selected_rows:
            idx = int(selected_rows[0])
            selected_id = df.iloc[idx]["id"]
            selected = next((p for p in patients_sorted if p.get("id") == selected_id), None)
    except Exception:
        selected = None

    if not selected:
        patient_ids = [p.get("id") for p in patients_sorted if p.get("id")]
        selected_id = st.selectbox(T["sel_id"], options=patient_ids, index=0 if patient_ids else None)
        selected = next((p for p in patients_sorted if p.get("id") == selected_id), None)

    if not selected:
        return

    triage = selected.get("triage_level", "Low")
    risk = selected.get("risk_score", 0)
    status_now = selected.get("status", "Waiting")
    tri_badge = T["tri"].get(triage, triage)
    st_badge = T["st"].get(status_now, status_now)

    st.markdown(f"### {T['intake_summary']}")
    st.markdown(
        f"""
        <div class="vv-card">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;">
            <div>
              <div style="font-size:1.3rem;font-weight:900;">{selected.get("patient_name","Unknown")}</div>
              <div class="vv-small">{selected.get("age","?")}y • {selected.get("weight","?")} • {selected.get("phone","")}</div>
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
              <span class="vv-badge">{T["k_triage"]}: {tri_badge}</span>
              <span class="vv-badge">{T["k_risk"]}: {risk}/100</span>
              <span class="vv-badge">{T["k_status"]}: {st_badge}</span>
            </div>
          </div>
          <div class="vv-row">
            <div class="vv-kv">
              <div class="vv-k">{T["k_cc"]}</div>
              <div class="vv-v" style="font-size:1rem;">{selected.get("chief_complaint","")}</div>
            </div>
            <div class="vv-kv">
              <div class="vv-k">{T["k_hpi"]}</div>
              <div class="vv-small">{selected.get("history_of_present_illness","")}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"### {T['actions']}")
    a1, a2 = st.columns([2, 1])
    status_opts = ["Waiting", "In Review", "Escalated", "Closed"]
    with a1:
        status = st.selectbox(
            T["upd_status"],
            status_opts,
            index=status_opts.index(status_now) if status_now in status_opts else 0,
            format_func=lambda s: T["st"].get(s, s),
        )
    with a2:
        if st.button(T["save"], type="primary", use_container_width=True):
            try:
                updated = api_patch(f"/api/patients/{selected.get('id')}/status", {"status": status})
                st.success(f"{T['saved']}: {updated.get('status')}")
                st.rerun()
            except Exception as e:
                st.error(f"{T['save_fail']}: {e}")


def evaluation_page():
    lang = st.session_state.get("ui_lang", "en")
    T = texts(lang)
    st.subheader(T["eval_title"])

    top1, top2, top3 = st.columns([1, 1, 2])
    with top1:
        if st.button(T["refresh"], type="primary", use_container_width=True):
            try:
                st.session_state.evaluation_report = api_get("/api/evaluation/report")
                st.success(T["updated"])
            except Exception as e:
                st.error(f"{T['load_fail']}: {e}")
    with top2:
        if st.button(T["gen_graphs"], use_container_width=True):
            try:
                root = Path(__file__).resolve().parent
                subprocess.check_call(
                    [sys.executable, str(root / "backend/utils/generate_report_graphs.py")],
                    cwd=str(root),
                )
                st.success(T["graphs_ok"])
            except Exception as e:
                st.error(f"{T['graphs_fail']}: {e}")
    with top3:
        st.caption(T["eval_cap"])

    report = st.session_state.get("evaluation_report")
    if not report:
        try:
            report = api_get("/api/evaluation/report")
            st.session_state.evaluation_report = report
        except Exception as e:
            st.error(f"{T['report_fail']}: {e}")
            return

    t1, t2, t3 = st.tabs([T["tab_sum"], T["tab_json"], T["tab_graphs"]])
    with t1:
        m = report.get("metrics", {})
        r = report.get("response_time", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(T["m_acc"], f"{m.get('accuracy', 0):.2f}")
        c2.metric(T["m_f1"], f"{m.get('macro_f1', 0):.2f}")
        c3.metric(T["m_p95"], f"{r.get('p95_ms', 0)} ms")
        c4.metric(T["m_max"], f"{r.get('max_ms', 0)} ms")
        st.write(T["eval_note"])
    with t2:
        st.json(report)
    with t3:
        graphs_dir = Path(__file__).resolve().parent / "report_assets/graphs"
        imgs = [
            graphs_dir / "graph_1_metrics_bar.png",
            graphs_dir / "graph_2_response_time_line.png",
            graphs_dir / "graph_3_triage_pie.png",
            graphs_dir / "graph_4_status_stacked.png",
            graphs_dir / "graph_5_before_after_reduction.png",
        ]
        missing = [p for p in imgs if not p.exists()]
        if missing:
            st.info(T["graphs_missing"])
        else:
            st.image(str(imgs[0]), caption=T["cap_g1"], use_container_width=True)
            st.image(str(imgs[1]), caption=T["cap_g2"], use_container_width=True)
            st.image(str(imgs[2]), caption=T["cap_g3"], use_container_width=True)
            st.image(str(imgs[3]), caption=T["cap_g4"], use_container_width=True)
            st.image(str(imgs[4]), caption=T["cap_g5"], use_container_width=True)


def main():
    st.set_page_config(page_title="Virtual Vita (Streamlit)", layout="wide")
    if "auth_role" not in st.session_state:
        st.session_state.auth_role = None
    inject_css()
    if st.session_state.auth_role is None:
        login_page()
        st.stop()

    if "ui_lang" not in st.session_state:
        st.session_state.ui_lang = "en"
    if "page" not in st.session_state:
        st.session_state.page = "patient"
    st.session_state.page = normalize_page_key(st.session_state.page)

    role = st.session_state.auth_role
    T = texts(st.session_state.ui_lang)
    if role == "user" and st.session_state.page == "admin":
        st.session_state.page = "patient"
        st.warning(T["admin_only"])

    st.markdown('<div class="vv-title">Virtual Vita</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="vv-subtitle">{T["subtitle"]}</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.write(f"### {T['nav']}")
        full_nav = [
            ("patient", T["page_patient"]),
            ("admin", T["page_admin"]),
            ("eval", T["page_eval"]),
        ]
        nav_items = [n for n in full_nav if role == "admin" or n[0] != "admin"]
        for key, label in nav_items:
            is_active = st.session_state.page == key
            btn_label = f"● {label}" if is_active else label
            if st.button(
                btn_label,
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.page = key
                st.rerun()
        st.caption(
            f"{T['signed_in']}: {T['login_user'] if role == 'user' else T['login_admin']}"
        )
        if st.button(T["logout"], use_container_width=True, type="secondary", key="vv_logout"):
            st.session_state.auth_role = None
            for k in ("messages", "session_id", "evaluation_report", "vv_flush_chat_message"):
                st.session_state.pop(k, None)
            st.rerun()
        st.write("---")
        st.write(f"### {T['settings']}")
        st.caption(T["lang_label"])
        lc1, lc2 = st.columns(2)
        with lc1:
            if st.button("English", use_container_width=True, type="primary" if st.session_state.ui_lang == "en" else "secondary", key="lang_en"):
                st.session_state.ui_lang = "en"
                st.rerun()
        with lc2:
            if st.button("తెలుగు", use_container_width=True, type="primary" if st.session_state.ui_lang == "te" else "secondary", key="lang_te"):
                st.session_state.ui_lang = "te"
                st.rerun()
        st.caption(T["theme_caption"])

    page = st.session_state.page
    if page == "patient":
        patient_chat()
    elif page == "admin":
        admin_dashboard()
    else:
        evaluation_page()


if __name__ == "__main__":
    main()

