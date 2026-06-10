#risk_engine.py
from typing import List, Dict

# ============================================================
# CONTENT WEIGHTS (PHI CATEGORY SENSITIVITY)
# ============================================================

CATEGORY_WEIGHTS = {
    "NAME": 0.15,
    "CONTACT": 0.20,
    "ID": 0.20,
    "LOCATION": 0.25,
    "FINANCIAL": 0.25,
    "DIAGNOSIS": 0.15,
}

SENSITIVE_DIAGNOSIS_KEYWORDS = {
    "cancer",
    "carcinoma",
    "hiv",
    "aids",
    "pregnancy",
    "gestational",
}

# Masked entities contribute minimal risk
MASKED_DISCOUNT = 0.05


# ============================================================
# CONTENT RISK (Mixed Sensitivity Score)
# ============================================================

def compute_content_risk(phi_entities: List[Dict]):

    score = 0.0
    factors = []

    for entity in phi_entities:

        category = entity.get("category")
        text = entity.get("entity", "").lower()
        masked = entity.get("masked", False)

        if category not in CATEGORY_WEIGHTS:
            continue

        weight = CATEGORY_WEIGHTS[category]

        # Extra severity for highly sensitive diagnoses
        if category == "DIAGNOSIS":
            if any(k in text for k in SENSITIVE_DIAGNOSIS_KEYWORDS):
                weight += 0.05

        # Reduce contribution if masked
        if masked:
            weight *= MASKED_DISCOUNT

        score += weight
        factors.append(category)

    return min(score, 1.0), factors


# ============================================================
# IDENTITY EXPOSURE RISK (New Explicit Score)
# ============================================================

def compute_identity_risk(phi_entities: List[Dict]):

    score = 0.0

    for e in phi_entities:

        if e.get("masked"):
            continue

        category = e.get("category")

        if category in {"NAME", "CONTACT", "ID", "FINANCIAL", "LOCATION"}:
            score += 0.2

    return round(min(score, 1.0), 3)


# ============================================================
# CLINICAL SENSITIVITY RISK (New Explicit Score)
# ============================================================

def compute_clinical_risk(phi_entities: List[Dict]):

    score = 0.0

    for e in phi_entities:

        category = e.get("category")
        text = e.get("entity", "").lower()

        if category == "DIAGNOSIS":
            score += 0.25

            if any(k in text for k in SENSITIVE_DIAGNOSIS_KEYWORDS):
                score += 0.10

    return round(min(score, 1.0), 3)


# ============================================================
# CONTEXT RISK
# ============================================================

def compute_context_risk(recipient_type: str, time: str, attachment: bool):

    score = 0.0
    factors = []

    if recipient_type == "external":
        score += 0.15
        factors.append("external_communication")

    if time == "late_night":
        score += 0.20
        factors.append("after_hours")

    if attachment:
        score += 0.20
        factors.append("attachment_present")

    return min(score, 1.0), factors


# ============================================================
# REIDENTIFICATION RISK
# ============================================================

def compute_reidentification_risk(phi_entities: List[Dict]):

    categories = []

    for e in phi_entities:

        if e.get("masked"):
            continue

        categories.append(e.get("category"))

    has_name = "NAME" in categories
    has_contact = "CONTACT" in categories
    has_location = "LOCATION" in categories
    has_id = "ID" in categories
    has_financial = "FINANCIAL" in categories
    has_diagnosis = "DIAGNOSIS" in categories

    if has_name and has_id:
        return 0.9

    if has_name and has_location:
        return 0.7

    if has_name and has_contact:
        return 0.6

    if has_name and has_diagnosis:
        return 0.5

    if has_name:
        return 0.3
    
    

    return 0.0


# ============================================================
# COMBINATION ATTACK BONUS
# ============================================================

def compute_combination_bonus(phi_entities: List[Dict], recipient_type):

    categories = []

    for e in phi_entities:

        if e.get("masked"):
            continue

        categories.append(e.get("category"))

    bonus = 0.0
    factors = []

    if "NAME" in categories and "CONTACT" in categories:
        bonus += 0.05
        factors.append("name_contact_link")

    if "NAME" in categories and "DIAGNOSIS" in categories:
        bonus += 0.05
        factors.append("identity_medical_link")

    if "DIAGNOSIS" in categories and "FINANCIAL" in categories:
        bonus += 0.08
        factors.append("medical_insurance_link")

    if "LOCATION" in categories and "CONTACT" in categories:
        bonus += 0.08
        factors.append("address_contact_link")

    if recipient_type == "external" and "CONTACT" in categories:
        bonus += 0.10
        factors.append("external_contact_risk")

    return min(bonus, 0.2), factors


# ============================================================
# FUSION ENGINE (Overall Transmission Risk)
# ============================================================

def fusion_engine(
    content_score,
    context_score,
    reid_score,
    behavior_score
):

    final_score = (
        0.40 * content_score +
        0.25 * context_score +
        0.25 * reid_score +
        0.10 * behavior_score
    )

    return min(final_score, 1.0)


# ============================================================
# MAIN RISK FUNCTION
# ============================================================

def compute_transmission_risk(
    phi_entities: List[Dict],
    recipient_type: str,
    time: str,
    attachment: bool,
    behavioral_score: float = 0.0
):

    # Core components
    content_risk, content_factors = compute_content_risk(phi_entities)
    context_risk, context_factors = compute_context_risk(
        recipient_type,
        time,
        attachment
    )
    reid_risk = compute_reidentification_risk(phi_entities)
    combo_bonus, combo_factors = compute_combination_bonus(
        phi_entities,
        recipient_type
    )

    # New separated scores
    identity_risk = compute_identity_risk(phi_entities)
    clinical_risk = compute_clinical_risk(phi_entities)

    # Overall risk
    fused_score = fusion_engine(
        content_risk,
        context_risk,
        reid_risk,
        behavioral_score
    )

    final_risk = round(min(fused_score + combo_bonus, 1.0), 3)

    # Classification
    if final_risk >= 0.90:
        risk_level = "Critical"
    elif final_risk >= 0.70:
        risk_level = "High"
    elif final_risk >= 0.40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    explain_factors = list(
        set(content_factors + context_factors + combo_factors)
    )

    return {
        "final_risk_score": final_risk,
        "risk_level": risk_level,
        "identity_risk": identity_risk,
        "clinical_risk": clinical_risk,
        "risk_factors": explain_factors,
        "components": {
            "content_risk": round(content_risk, 3),
            "context_risk": round(context_risk, 3),
            "reidentification_risk": round(reid_risk, 3),
            "behavioral_risk": round(behavioral_score, 3),
            "combination_bonus": round(combo_bonus, 3)
        }
    }