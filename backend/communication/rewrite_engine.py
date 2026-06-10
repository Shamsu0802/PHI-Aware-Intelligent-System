#rewrite_engine.py
import re

# ============================================================
# HIGH RISK TYPES
# ============================================================

HIGH_RISK = {
    "PHONE",
    "EMAIL",
    "AADHAAR",
    "PAN",
    "ADDRESS"
}

# ============================================================
# CONFIGURATION FLAGS
# ============================================================

ALLOW_MRN_EXTERNAL = True
ENABLE_GENERALIZATION = True


# ============================================================
# NAME MASKING
# ============================================================

def mask_name(name: str):

    parts = name.split()
    masked = []

    for p in parts:

        if re.match(r"^[A-Z]\.$", p):
            masked.append(p)
            continue

        if len(p) <= 2:
            masked.append(p[0] + "X")
        else:
            masked.append(p[0] + "****")

    return " ".join(masked)


# ============================================================
# CLEAN PERSON ENTITY
# ============================================================

def clean_person_entity(name):

    name = re.sub(
        r"^(Husband|Wife|Son|Daughter|Spouse|Father|Mother)\s+",
        "",
        name,
        flags=re.IGNORECASE
    )

    return name.strip()


# ============================================================
# MASK PATIENT NAMES
# ============================================================

def mask_patient_names(original_text, text):

    names = re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", original_text)

    for name in names:
        parts = name.split()
        masked = parts[0][0] + "**** " + parts[1][0] + "****"
        text = re.sub(r"\b" + re.escape(name) + r"\b", masked, text)

    return text


# ============================================================
# MASK PATIENT ID
# ============================================================

def mask_patient_id(text):

    return re.sub(
        r"(Patient ID[:\s]*)([A-Za-z0-9\-]+)",
        lambda m: m.group(1) + m.group(2)[:2] + "XXXX" + m.group(2)[-2:],
        text
    )


# ============================================================
# MASK POLICY NUMBER
# ============================================================

def mask_policy(text):

    def repl(match):

        policy = match.group()

        if len(policy) < 6:
            return policy

        return policy[:2] + "XXXX" + policy[-2:]

    return re.sub(r"\b[A-Z]{2,5}-\d{4,}\b", repl, text)


# ============================================================
# REMOVE PHONE
# ============================================================

def remove_phone(text):

    return re.sub(
        r"\b[6-9]\d{9}\b",
        "[contact removed]",
        text
    )


# ============================================================
# REMOVE EMAIL
# ============================================================

def remove_email(text):

    return re.sub(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "the hospital communication portal",
        text
    )


# ============================================================
# REMOVE AADHAAR
# ============================================================

def remove_aadhaar(text):

    return re.sub(
        r"\b\d{4}[- ]?\d{4}[- ]?\d{4}\b",
        "[Removed for privacy compliance]",
        text
    )


# ============================================================
# MASK PAN
# ============================================================

def mask_pan(text):

    def mask(match):

        pan = match.group()

        return pan[:2] + "XXXXXX" + pan[-2:]

    return re.sub(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", mask, text)


# ============================================================
# REMOVE ADDRESS
# ============================================================

def remove_address(text):

    return re.sub(
        r"\d{1,4}[^,]*\b(Road|Street|Lane|Avenue|Nagar|Colony)\b[^,]*\d{6}",
        "[address removed]",
        text,
        flags=re.IGNORECASE
    )


# ============================================================
# ANONYMIZE CONTACTS
# ============================================================

def anonymize_contacts(text):

    return re.sub(
        r"\b(Emergency Contact|Spouse|Husband|Wife|Son|Daughter)\b[^,.]*",
        r"\1: [Family Contact]",
        text,
        flags=re.IGNORECASE
    )


# ============================================================
# GENERALIZATION
# ============================================================

def generalize_age(text):

    def age_band(age):
        age = int(age)
        lower = (age // 10) * 10
        upper = lower + 9
        return f"{lower}–{upper} years"

    # Convert "62 years old"
    text = re.sub(
        r"\b(\d{1,3})\s*years?\s*old\b",
        lambda m: age_band(m.group(1)),
        text,
        flags=re.IGNORECASE
    )

    # Convert "Age: 62"
    text = re.sub(
        r"Age:\s*(\d{1,3})",
        lambda m: f"Age: {age_band(m.group(1))}",
        text,
        flags=re.IGNORECASE
    )

    return text

def generalize_admission_date(text):

    return re.sub(
        r"Admission Date:\s*(\d{2})/(\d{2})/(\d{4})",
        lambda m: f"Admission: {m.group(2)}/{m.group(3)}",
        text
    )


# ============================================================
# INTERNAL MASKING
# ============================================================

def apply_internal_masking(original_text, text):

    text = mask_patient_names(original_text, text)
    text = mask_patient_id(text)
    text = remove_phone(text)
    text = remove_email(text)
    text = remove_aadhaar(text)
    text = remove_address(text)
    text = mask_policy(text)
    text = mask_pan(text)
    text = anonymize_contacts(text)

    if ENABLE_GENERALIZATION:

        text = generalize_age(text)
        text = generalize_admission_date(text)

    return text


# ============================================================
# SAFE CHANNEL ENFORCEMENT
# ============================================================

def enforce_safe_channel(text):

    return re.sub(
        r"reports?\s+to\s+be\s+emailed.*",
        "Reports should be shared through the hospital communication portal using registered EMR contact channels.",
        text,
        flags=re.IGNORECASE
    )


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text):

    text = re.sub(r"\n\s*\n", "\n", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+\.", ".", text)
    text = re.sub(r"\.\.", ".", text)
    text = re.sub(r"\s+,", ",", text)

    return text.strip()

def get_rewrite_strength(recipient_type, risk_level):

    if recipient_type == "internal":
        if risk_level in ["safe", "low"]:
            return "light"
        else:
            return "moderate"

    if recipient_type == "external":
        if risk_level == "safe":
            return "light"
        elif risk_level in ["low", "medium"]:
            return "moderate"
        else:
            return "strong"
# ============================================================
# MAIN SAFE REWRITE ENGINE
# ============================================================

def generate_safe_rewrite(original_text, recipient_type, risk_level):

    rewritten = original_text

    strength = get_rewrite_strength(recipient_type, risk_level)

    # ---------------- ALWAYS REMOVE DIRECT IDENTIFIERS ----------------
    rewritten = remove_phone(rewritten)
    rewritten = remove_email(rewritten)
    rewritten = remove_aadhaar(rewritten)
    rewritten = remove_address(rewritten)

    # ---------------- LIGHT MASKING ----------------
    if strength == "light":

        rewritten = mask_patient_names(original_text, rewritten)
        rewritten = mask_policy(rewritten)

    # ---------------- MODERATE MASKING ----------------
    elif strength == "moderate":

        rewritten = mask_patient_names(original_text, rewritten)

        # Partial MRN
        rewritten = re.sub(
            r"\bMRN\s*([A-Z0-9]+)\b",
            lambda m: f"MRN ****{m.group(1)[-2:]}",
            rewritten
        )

        # Partial policy
        rewritten = re.sub(
            r"\bPOL[A-Z0-9]+\b",
            lambda m: "Insurance policy [partially masked]",
            rewritten
        )

    # ---------------- STRONG MASKING (EXTERNAL HIGH) ----------------
    elif strength == "strong":

        rewritten = mask_patient_names(original_text, rewritten)
        
        # FULL REMOVE MRN
        rewritten = re.sub(
            r"\bMRN\s*[A-Z0-9]+\b",
            "MRN [masked]",
            rewritten
        )
        
        # FORCE REMOVE ANY POLICY NUMBER
        rewritten = re.sub(
            r"\bPOL[A-Z0-9]+\b",
            "Insurance details [masked]",
            rewritten
        )

        # Rewrite sensitive sentence
        rewritten = re.sub(
            r"Insurance policy .*? approved for .*?\.",
            "Insurance approval confirmed. Details available via secure system.",
            rewritten,
            flags=re.IGNORECASE
        )
        
        rewritten = re.sub(
            r"Reports? are attached\.?",
            "Reports should be shared through the hospital communication portal.",
            rewritten,
            flags=re.IGNORECASE
        )
        
        rewritten = re.sub(
            r"Please confirm next steps.*",
            "Please confirm next steps through secure communication channels.",
            rewritten,
            flags=re.IGNORECASE
        )

        rewritten = enforce_safe_channel(rewritten)

    # ---------------- FINAL CLEAN ----------------
    rewritten = clean_text(rewritten)

    if not rewritten or len(rewritten.split()) < 5:
        return original_text

    return rewritten
# ============================================================
# VALIDATION
# ==========================================================
def validate_rewrite(text):
    """
    Ensures no high-risk PHI remains in rewritten output
    """

    # Simple regex-based validation (no heavy NLP)

    patterns = [
        r"\b[6-9]\d{9}\b",  # phone
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # email
        r"\b\d{4}[- ]?\d{4}[- ]?\d{4}\b",  # aadhaar
        r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",  # PAN
    ]

    for p in patterns:
        if re.search(p, text):
            return False

    return True