#app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# -------------------- SECURE COMMUNICATION IMPORTS --------------------

from core.risk_engine import compute_transmission_risk
from communication.rewrite_engine import generate_safe_rewrite, validate_rewrite
import os
import joblib
import numpy as np
from database.db import get_connection, init_db
from datetime import datetime
from collections import defaultdict
import json
from screen_privacy.privacy_controller import is_screen_guard_running


from nlp.phi_detector import detect_phi
from features.feature_extractor import extract_features
from nlp.explainability import generate_explanation

# 🔐 SCREEN PRIVACY IMPORTS (ADDED)

from screen_privacy.privacy_controller import (
    start_screen_guard,
    stop_screen_guard,
    get_privacy_state,
    get_privacy_reason
)

# -------------------- APP SETUP --------------------

app = FastAPI(title="PHI Leakage Tracing Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- LOAD MODELS --------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONTENT_MODEL_PATH = os.path.join(BASE_DIR, "models", "content_sensitivity_model.pkl")
BEHAVIOR_MODEL_PATH = os.path.join(BASE_DIR, "models", "isolation_forest.pkl")

content_model = joblib.load(CONTENT_MODEL_PATH)

artifact = joblib.load(BEHAVIOR_MODEL_PATH)
behavior_model = artifact["model"]
behavior_scaler = artifact["scaler"]
baseline_stats = artifact.get("baseline_stats", {})

FEATURE_NAMES = baseline_stats.get("feature_names", [])
# -------------------- DATABASE SETUP --------------------



# initialize database on startup
init_db()

# -------------------- HELPERS (🔥 CRITICAL FIX) --------------------

def is_valid_policy_number(value: str) -> bool:
    """
    POLICY_NUMBER must contain at least one digit.
    Prevents semantic words like 'insurance' from being treated as PHI.
    """
    return any(char.isdigit() for char in value)

# -------------------- REQUEST SCHEMA --------------------

class AnalyzeRequest(BaseModel):
    text: str
    recipient_type: str
    time: str
    attachment: bool

class SecureCommunicationRequest(BaseModel):
    text: str
    recipient_type: str
    time: str
    attachment: bool

# -------------------- ANALYZE ENDPOINT --------------------

@app.post("/analyze")
def analyze_content(request: AnalyzeRequest):

    # 1️⃣ PHI Detection
    phi_entities = detect_phi(request.text)

    # 🔒 HARD FILTER
    phi_relevant_entities = []
    for e in phi_entities:

        if not e.get("phi_relevant", True):
            continue

        if e.get("type") == "POLICY_NUMBER" and not is_valid_policy_number(
            e.get("entity", "")
        ):
            continue

        phi_relevant_entities.append(e)

    valid_phi = [
        e for e in phi_relevant_entities
        if e.get("type") in ["PERSON", "MRN", "PHONE", "POLICY_NUMBER", "DISEASE"]
    ]

    if len(valid_phi) == 0:
        return {
            "risk_level": "Safe",
            "composite_risk_score": 0.0,
            "risk_breakdown": {
                "content": 0.0,
                "context": 0.0,
                "behavior": 0.0,
                "percentages": {
                    "content": 0,
                    "context": 0,
                    "behavior": 0
                }
            },
            "phi_entities": [],
            "phi_attribution": [],
            "reidentification_risk": 0.0,
            "behavior_explanation": {
                "anomaly_score": 0.0,
                "status": "Normal",
                "percentage": 0,
                "feature_deviations": [
                    {
                        "feature": "Overall",
                        "interpretation": "No PHI detected; behavior considered safe"
                    }
                ]
            },
            "explanation": [
                "No sensitive health information detected in the communication",
                "The message is considered safe with negligible privacy risk"
            ]
        }

    TYPE_TO_CATEGORY = {
        "PERSON": "NAME",
        "PHONE": "CONTACT",
        "EMAIL_ADDRESS": "CONTACT",
        "DATE_TIME": "DATE",
        "MRN": "ID",
        "AADHAR": "ID",
        "PAN": "ID",
        "POLICY_NUMBER": "FINANCIAL",
        "RECORD_ID": "ID",
        "DISEASE": "DIAGNOSIS"
    }

    feature_entities = []

    for e in phi_relevant_entities:
        mapped_category = TYPE_TO_CATEGORY.get(e.get("type"))

        feature_entities.append({
            "entity": e.get("entity"),
            "category": mapped_category,
            "masked": e.get("masked", False)
        })

    feature_row = {
        "entities": feature_entities,
        "recipient_type": request.recipient_type,
        "attachment_present": request.attachment,
        "time_of_day": request.time,
        "content": request.text
    }

    content_score = float(
        content_model.predict_proba([request.text])[0][1]
    )

    raw_features = np.array([extract_features(feature_row)])
    raw_features = np.nan_to_num(raw_features)

    scaled_features = behavior_scaler.transform(raw_features)

    anomaly_raw = float(
        behavior_model.decision_function(scaled_features)[0]
    )

    behavior_score = min(1.0, max(0.0, -anomaly_raw))

    context_score = (
        0.5 * float(request.recipient_type == "external") +
        0.3 * float(request.attachment) +
        0.2 * float(request.time == "late_night")
    )

    w_content, w_context, w_behavior = 0.5, 0.3, 0.2

    phi_count = len(phi_relevant_entities)

    if phi_count >= 5:
        content_score += 0.10
    elif phi_count >= 3:
        content_score += 0.05

    content_score = min(content_score, 1.0)

    composite_score = round(
        w_content * content_score +
        w_context * context_score +
        w_behavior * behavior_score,
        3
    )

    if composite_score >= 0.80:
        risk_level = "Critical"
    elif composite_score >= 0.60:
        risk_level = "High"
    elif composite_score >= 0.35:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    total = (
        w_content * content_score +
        w_context * context_score +
        w_behavior * behavior_score
    ) or 1e-6

    content_pct = round((w_content * content_score) / total * 100)
    context_pct = round((w_context * context_score) / total * 100)
    behavior_pct = 100 - content_pct - context_pct

    attribution = []
    total_phi_weight = sum(
        e.get("risk_weight", 0.0) for e in phi_relevant_entities
    ) or 1e-6

    for e in phi_relevant_entities:
        attribution.append({
            "entity": e["entity"],
            "type": e["type"],
            "category": e.get("phi_category"),
            "masked": e.get("masked"),
            "contribution_pct": round(
                (e.get("risk_weight", 0.0) / total_phi_weight) * 100, 1
            )
        })

    linkage = defaultdict(list)
    for e in phi_relevant_entities:
        if e.get("linkable_group"):
            linkage[e["linkable_group"]].append(e)

    identity_count = len(linkage.get("IDENTITY_CLUSTER", []))
    clinical_count = len(linkage.get("CLINICAL_CLUSTER", []))

    reidentification_risk = round(
        min(1.0, (identity_count * clinical_count) / 4.0),
        3
    )

    behavior_explanation = {
        "anomaly_score": round(behavior_score, 3),
        "status": "Deviated" if behavior_score > 0.4 else "Normal",
        "percentage": behavior_pct,
        "feature_deviations": []
    }

    if baseline_stats:
        means = baseline_stats["mean"]
        stds = baseline_stats["std"]

        for idx, fname in enumerate(FEATURE_NAMES):
            observed = float(scaled_features[0][idx])
            mean = means[idx]
            std = stds[idx]

            if abs(observed - mean) > 1.5 * std:
                behavior_explanation["feature_deviations"].append({
                    "feature": fname,
                    "observed": round(observed, 2),
                    "baseline_mean": round(mean, 2),
                    "interpretation": f"{fname.replace('_', ' ').title()} deviates from typical behavior"
                })

    if not behavior_explanation["feature_deviations"]:
        behavior_explanation["feature_deviations"].append({
            "feature": "Overall",
            "interpretation": "Behavior aligns with normal communication patterns"
        })

    explanation = generate_explanation(
        content_score=content_score,
        context_score=context_score,
        behavior_score=behavior_score,
        composite_score=composite_score,
        content_pct=content_pct,
        context_pct=context_pct,
        behavior_pct=behavior_pct
    )

    types_present = {e.get("type") for e in phi_relevant_entities}
    components = []
    risk_lines = []

    if "PERSON" in types_present:
        components.append("patient identity")

    if "MRN" in types_present:
        components.append("medical record identifiers")

    if "POLICY_NUMBER" in types_present:
        components.append("financial details")

    if "PHONE" in types_present:
        components.append("contact information")

    if "DISEASE" in types_present:
        components.append("medical condition details")

    if "MRN" in types_present and "PERSON" in types_present:
        risk_lines.append(
            "Patient identity + MRN → Risk of re-identification & unauthorized record access"
        )

    if "POLICY_NUMBER" in types_present:
        risk_lines.append(
            "Policy number exposure → Financial misuse / fraudulent claim activities"
        )

    if "PHONE" in types_present:
        risk_lines.append(
            "Contact details → increases susceptibility to impersonation or targeted social engineering attacks"
        )

    if request.recipient_type == "external":
        risk_lines.append(
            "External sharing → increases the likelihood of unauthorized data access outside controlled systems"
        )

    if "DISEASE" in types_present:
        risk_lines.append(
            "Exposure of medical condition details → risk of privacy violation and potential discrimination"
        )

    if len(types_present) >= 3:
        risk_lines.append(
            "The presence of multiple sensitive identifiers within a single communication significantly amplifies overall exposure risk"
        )

    explanation = [
        line for line in explanation
        if not line.lower().startswith("the risk is primarily")
    ]

    if components:
        main_line = (
            f"The risk is primarily driven by content sensitivity ({content_pct}%), "
            f"resulting from the presence of multiple sensitive entities "
            f"({', '.join(components)}) in the communication"
        )
        explanation.insert(0, main_line)

    if explanation:
        explanation = [explanation[0]] + risk_lines + explanation[1:]

    top_entities = sorted(
        phi_relevant_entities,
        key=lambda x: x.get("risk_weight", 0.0),
        reverse=True
    )[:3]

    for e in top_entities:
        explanation.append(
            f"{e.get('type')} ({e.get('entity')}) significantly contributed to the overall risk"
        )

    # -------------------- SAVE TO DATABASE --------------------
    try:
        conn = get_connection()
        cursor = conn.cursor()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save to risk_logs
        cursor.execute("""
            INSERT INTO risk_logs
            (timestamp, risk_level, composite_score, phi_count, recipient_type, attachment, time_of_day, explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            risk_level,
            composite_score,
            len(phi_relevant_entities),
            request.recipient_type,
            int(request.attachment),
            request.time,
            json.dumps(explanation)
        ))

        # Save to incident_logs
        cursor.execute("""
            INSERT INTO incident_logs
            (timestamp, module, event_type, risk_level, details, action_taken)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            "Module 1",
            "PHI Detection",
            risk_level,
            f"{len(phi_relevant_entities)} PHI entities detected | Recipient={request.recipient_type} | Attachment={request.attachment}",
            "Transmission Blocked"
            if risk_level in ["High", "Critical"]
            else "Alert Raised"
            if risk_level == "Medium"
            else "Logged"
        ))

        conn.commit()

        print("✅ Risk log inserted successfully")
        print("✅ Incident log inserted successfully")

    except Exception as e:
        print("❌ Database logging error:", str(e))

    finally:
        try:
            conn.close()
        except:
            pass

    return {
        "risk_level": risk_level,
        "composite_risk_score": composite_score,
        "risk_breakdown": {
            "content": round(content_score, 3),
            "context": round(context_score, 3),
            "behavior": round(behavior_score, 3),
            "percentages": {
                "content": content_pct,
                "context": context_pct,
                "behavior": behavior_pct
            }
        },
        "phi_entities": phi_relevant_entities,
        "phi_attribution": attribution,
        "reidentification_risk": reidentification_risk,
        "behavior_explanation": behavior_explanation,
        "explanation": explanation
    }
# -------------------- SCREEN PRIVACY ROUTES (ADDED) --------------------

@app.get("/screen/start")
def start_screen():
    start_screen_guard()
    return {"status": "Screen Guard started"}


@app.get("/screen/stop")
def stop_screen():
    stop_screen_guard()
    return {"status": "Screen Guard stopped"}


@app.get("/screen/status")
def screen_status():
    state = get_privacy_state()
    reason = get_privacy_reason()

    try:
        conn = get_connection()
        cursor = conn.cursor()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save into screen_logs
        cursor.execute("""
            INSERT INTO screen_logs (timestamp, privacy_state, reason)
            VALUES (?, ?, ?)
        """, (
            timestamp,
            state,
            reason
        ))

        # Save into incident_logs
        cursor.execute("""
            INSERT INTO incident_logs
            (timestamp, module, event_type, risk_level, details, action_taken)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            "Module 3",
            "Screen Privacy Event",
            "High" if state == "BLOCK" else "Low",
            reason,
            "Screen Blurred" if state == "BLOCK" else "Logged"
        ))

        conn.commit()
        print("✅ Screen log inserted successfully")
        print("✅ Module 3 incident log inserted successfully")

    except Exception as e:
        print("❌ Screen log error:", str(e))

    finally:
        try:
            conn.close()
        except:
            pass

    return {
        "privacy_state": state,
        "reason": reason
    }


@app.get("/screen/stream")
def screen_stream():
    from screen_privacy.screen_guard import generate_frames

    # Start automatically if not already running
    if not is_screen_guard_running():
        start_screen_guard()

    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# -------------------- HEALTH CHECK --------------------

@app.get("/")
def root():
    return {"status": "PHI Leakage Tracing Engine running"}
# -------------------- DASHBOARD APIs --------------------

@app.get("/dashboard/summary")
def dashboard_summary():
    conn = get_connection()
    cursor = conn.cursor()

    # total analyzed messages
    cursor.execute("SELECT COUNT(*) FROM risk_logs")
    total_messages = cursor.fetchone()[0]

    # risk levels
    cursor.execute("SELECT COUNT(*) FROM risk_logs WHERE risk_level='High'")
    high_risk = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM risk_logs WHERE risk_level='Medium'")
    medium_risk = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM risk_logs WHERE risk_level='Low'")
    low_risk = cursor.fetchone()[0]

    # screen warnings
    cursor.execute("SELECT COUNT(*) FROM screen_logs WHERE privacy_state='BLOCK'")
    screen_warnings = cursor.fetchone()[0]
    conn.close()

    return {
        "total_messages": total_messages,
        "high_risk": high_risk,
        "medium_risk": medium_risk,
        "low_risk": low_risk,
        "screen_warnings": screen_warnings
    }


@app.get("/dashboard/risk-distribution")
def risk_distribution():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT risk_level, COUNT(*)
        FROM risk_logs
        GROUP BY risk_level
    """)

    data = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()

    return data


@app.get("/dashboard/recent-activity")
def recent_activity():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp, risk_level, phi_count, recipient_type
        FROM risk_logs
        ORDER BY id DESC
        LIMIT 10
    """)

    rows = cursor.fetchall()
    conn.close()

    activities = []
    for r in rows:
        activities.append({
            "timestamp": r[0],
            "risk_level": r[1],
            "phi_entities": r[2],
            "recipient": r[3]
        })

    return activities


@app.get("/dashboard/incidents")
def dashboard_incidents():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp, module, event_type, risk_level, details, action_taken
        FROM incident_logs
        ORDER BY id DESC
        LIMIT 100
    """)

    rows = cursor.fetchall()
    conn.close()

    incidents = []

    for row in rows:
        incidents.append({
            "time": row[0],
            "module": row[1],
            "event": row[2],
            "risk": row[3],
            "phi": row[4],
            "action": row[5]
        })

    return incidents


@app.get("/dashboard/screen-stats")
def screen_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date(timestamp), COUNT(*)
        FROM screen_logs
        GROUP BY date(timestamp)
        ORDER BY date(timestamp)
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "date": r[0],
            "warnings": r[1]
        }
        for r in rows
    ]# -------------------- SECURE COMMUNICATION MODULE --------------------

@app.post("/secure-communication/analyze")
def secure_communication_analyze(request: SecureCommunicationRequest):

    # 1️⃣ Detect PHI
    phi_entities = detect_phi(request.text)
    print("Detected PHI:", phi_entities)

    # --------------------------------------------------
    # FIXED TYPE MAPPING
    # --------------------------------------------------

    TYPE_TO_CATEGORY = {
        "PERSON": "NAME",
        "EMAIL_ADDRESS": "CONTACT",
        "PHONE": "CONTACT",
        "PAN": "ID",
        "AADHAR": "ID",
        "MRN": "ID",
        "RECORD_ID": "ID",
        "POLICY_NUMBER": "FINANCIAL",
        "DISEASE": "DIAGNOSIS",
        "FAC": "LOCATION",
        "GPE": "LOCATION",
    }

    formatted_entities = []

    for e in phi_entities:

        if not e.get("phi_relevant", True):
            continue

        entity_type = e.get("type")
        mapped_category = TYPE_TO_CATEGORY.get(entity_type)

        if not mapped_category:
            continue

        formatted_entities.append({
            "entity": e.get("entity"),
            "category": mapped_category,
            "masked": e.get("masked", False)
        })

    print("Formatted entities for risk engine:", formatted_entities)

    # --------------------------------------------------
    # 2️⃣ Behavioral score
    # --------------------------------------------------

    feature_row = {
        "entities": formatted_entities,
        "recipient_type": request.recipient_type,
        "attachment_present": request.attachment,
        "time_of_day": request.time,
        "content": request.text
    }

    raw_features = np.array([extract_features(feature_row)])
    raw_features = np.nan_to_num(raw_features)

    scaled_features = behavior_scaler.transform(raw_features)

    anomaly_raw = float(
        behavior_model.decision_function(scaled_features)[0]
    )

    behavior_score = min(1.0, max(0.0, -anomaly_raw))

    # --------------------------------------------------
    # 3️⃣ Compute transmission risk
    # --------------------------------------------------

    risk_result = compute_transmission_risk(
        phi_entities=formatted_entities,
        recipient_type=request.recipient_type,
        time=request.time,
        attachment=request.attachment,
        behavioral_score=behavior_score
    )

    # --------------------------------------------------
    # 4️⃣ Safe rewrite
    # --------------------------------------------------

    rewrite_suggestion = None
    rewrite_valid = True

    if risk_result["risk_level"] in ["Medium", "High", "Critical"]:

        rewrite_suggestion = generate_safe_rewrite(
            request.text,
            request.recipient_type,
            risk_result["risk_level"]
        )

        rewrite_valid = validate_rewrite(rewrite_suggestion)

    # --------------------------------------------------
    # 5️⃣ SAVE TO INCIDENT LOGS (MODULE 2)
    # --------------------------------------------------

    try:
        conn = get_connection()
        cursor = conn.cursor()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        action_taken = (
            "Transmission Blocked"
            if risk_result["risk_level"] in ["High", "Critical"]
            else "Alert Raised"
            if risk_result["risk_level"] == "Medium"
            else "Allowed"
        )

        cursor.execute("""
            INSERT INTO incident_logs
            (timestamp, module, event_type, risk_level, details, action_taken)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            "Module 2",
            "Communication Analysis",
            risk_result["risk_level"],
            f"Recipient={request.recipient_type} | Attachment={request.attachment} | Entities={len(formatted_entities)}",
            action_taken
        ))

        conn.commit()

        print("✅ Module 2 incident log inserted successfully")

    except Exception as e:
        print("❌ Module 2 logging error:", str(e))

    finally:
        try:
            conn.close()
        except:
            pass

    # --------------------------------------------------
    # 6️⃣ RETURN (IMPORTANT: UI expects risk_score)
    # --------------------------------------------------

    return {
        "risk_analysis": {
            "risk_score": risk_result["final_risk_score"],
            "risk_level": risk_result["risk_level"],
            "decision": (
                "BLOCK"
                if risk_result["risk_level"] in ["High", "Critical"]
                else "ALLOW"
            ),
            "components": risk_result["components"],
            "risk_factors": risk_result["risk_factors"]
        },
        "rewrite_suggestion": rewrite_suggestion,
        "rewrite_valid": rewrite_valid
    }
# -------------------- SECURE SEND EMAIL --------------------

from services.email_service import send_email  # make sure this exists

@app.post("/secure-communication/send")
def secure_send_email(data: dict):

    try:
        send_email(
            data["recipient"],
            "Healthcare Communication",
            data["message"]
        )

        return {"status": "sent"}

    except Exception as e:
        print("Email sending error:", e)
        return {"status": "error"}

