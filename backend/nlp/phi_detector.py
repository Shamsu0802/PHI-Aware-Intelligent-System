# phi_detector.py
import re
import spacy
from presidio_analyzer import AnalyzerEngine
from nlp.disease_ner import detect_diseases

# -------------------- INIT (LOAD ONCE) --------------------

print("Loading NLP models...")

nlp = spacy.load("en_core_web_sm")
presidio_analyzer = AnalyzerEngine()

print("spaCy and Presidio initialized successfully")

# -------------------- CONFIG --------------------

WEAK_TEMPORAL_TERMS = {
    "this week","last week","next week",
    "yesterday","today","tomorrow",
    "last night","tonight",
    "this month","last month"
}

PHI_CATEGORIES = {
    "PERSON":"DIRECT_IDENTIFIER",
    "MRN":"DIRECT_IDENTIFIER",
    "POLICY_NUMBER":"DIRECT_IDENTIFIER",
    "PHONE":"DIRECT_IDENTIFIER",
    "RECORD_ID":"DIRECT_IDENTIFIER",
    "PAN":"DIRECT_IDENTIFIER",
    "AADHAR":"DIRECT_IDENTIFIER",
    "EMAIL_ADDRESS":"DIRECT_IDENTIFIER",
    "DISEASE":"CLINICAL_PHI",
    "DATE_TIME":"QUASI_IDENTIFIER"
}

PHI_RISK_WEIGHTS = {
    "PERSON":0.38,
    "POLICY_NUMBER":0.42,
    "MRN":0.40,
    "PHONE":0.35,
    "RECORD_ID":0.30,
    "AADHAR":0.50,
    "EMAIL_ADDRESS":0.33,
    "DISEASE":0.15,
    "DATE_TIME":0.10
}

NON_PHI_ENTITY_TYPES = {
    "ORG","GPE","LOC","FACILITY",
    "CARDINAL","PRODUCT","WORK_OF_ART",
    "LAW","EVENT","LANGUAGE"
}

GENERIC_MEDICAL_WORDS = {
    "instructions","medication","treatment","therapy",
    "dosage","tablet","recent","capsule"
}

# -------------------- FILTERS --------------------

def is_weak_temporal(text:str)->bool:
    return text.lower().strip() in WEAK_TEMPORAL_TERMS


def is_medical_measurement(text:str)->bool:

    text=text.lower().strip()

    if re.match(r'^\d+(\.\d+)?%?$',text):
        return True

    if re.search(r'(mg/dl|mmhg|bpm|ml|kg|cm|mg)',text):
        return True

    if re.match(r'^\d{1,2}\s?(am|pm)$',text):
        return True

    return False


def is_real_phi(entity_text:str,entity_type:str):

    text=entity_text.lower().strip()

    if re.match(r'^\d{1,3}\s?years?\s?old$',text):
        return False

    if re.match(r'^\d+(\.\d+)?%?$',text):
        return False

    if re.match(r'^\d{1,2}\s?(am|pm)$',text):
        return False

    if text in {"uncontrolled","mild","moderate","severe"}:
        return False

    return True


def is_contextual_false_positive(text:str):

    t=text.lower().strip()

    if re.search(r'\b\d+\s?(days?|weeks?|months?|years?)\b',t):
        return True

    if re.match(r'^(19|20)\d{2}$',t):
        return True

    if re.search(r'₹|\$|rs\.?|inr',t):
        return True

    NON_PHI_CONTEXT={
        "biopsy","chemotherapy","radiotherapy","surgery",
        "oncology","cardiology","neurology","cycle",
        "treatment","therapy","procedure","scan","confirmed"
    }

    if t in NON_PHI_CONTEXT:
        return True

    if t in {"monday","tuesday","wednesday","thursday","friday","saturday","sunday"}:
        return True

    return False


def get_phi_category(entity_type:str):
    return PHI_CATEGORIES.get(entity_type)


def get_risk_weight(entity_type:str):
    return PHI_RISK_WEIGHTS.get(entity_type,0.0)


def get_linkable_group(entity_type:str):

    if entity_type in {
        "PERSON","MRN","POLICY_NUMBER","AADHAR","EMAIL_ADDRESS","PAN","PHONE","RECORD_ID"
    }:
        return "IDENTITY_CLUSTER"

    if entity_type=="DISEASE":
        return "CLINICAL_CLUSTER"

    return None


def span_overlaps(span,seen_spans):

    s1,e1=span

    for s2,e2 in seen_spans:

        if s1<e2 and e1>s2:
            return True

    return False


# -------------------- MAIN DETECTION --------------------

def detect_phi(text:str):

    detected=[]
    seen_spans=set()

    doc=nlp(text)

    # -------- spaCy --------

    for ent in doc.ents:

        if ent.label_ in NON_PHI_ENTITY_TYPES:
            continue

        if ent.label_=="DATE" and re.search(r"\b(MRN|UHID|ID)\b",ent.text,re.I):
            continue

        if ent.label_=="DATE" and is_weak_temporal(ent.text):
            continue

        if not is_real_phi(ent.text,ent.label_):
            continue

        if is_contextual_false_positive(ent.text):
            continue

        entity_type="DATE_TIME" if ent.label_=="DATE" else ent.label_

        span_key=(ent.start_char,ent.end_char)

        if span_key not in seen_spans:

            detected.append({
                "entity":ent.text.strip(),
                "type":entity_type,
                "source":"spaCy",
                "masked":False,
                "phi_relevant":True,
                "phi_category":get_phi_category(entity_type),
                "risk_weight":get_risk_weight(entity_type),
                "linkable_group":get_linkable_group(entity_type)
            })

            seen_spans.add(span_key)

    # -------- PERSON RULE --------

    name_pattern = r"(?:Patient|Mr|Mrs|Ms|Dr)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+|\s[A-Z]\b)?)"

    for match in re.finditer(name_pattern,text):

        entity_text=match.group(1).strip()
        span_key=(match.start(1),match.end(1))

        if span_overlaps(span_key,seen_spans):
            continue

        detected.append({
            "entity":entity_text,
            "type":"PERSON",
            "source":"Rule",
            "masked":False,
            "phi_relevant":True,
            "phi_category":get_phi_category("PERSON"),
            "risk_weight":get_risk_weight("PERSON"),
            "linkable_group":get_linkable_group("PERSON")
        })

        seen_spans.add(span_key)

    # -------- Presidio --------

    presidio_results=presidio_analyzer.analyze(
        text=text,
        language="en",
        entities=["PHONE_NUMBER","EMAIL_ADDRESS","DATE_TIME"]
    )

    TYPE_MAPPING={
    "PHONE_NUMBER":"PHONE",
    "EMAIL_ADDRESS":"EMAIL_ADDRESS",
    "DATE_TIME":"DATE_TIME"
}

    for result in presidio_results:

        entity_text = text[result.start:result.end].strip()

        mapped_type = TYPE_MAPPING.get(result.entity_type)

        if not mapped_type:
            continue

        if is_medical_measurement(entity_text):
            continue

        if entity_text.lower() in GENERIC_MEDICAL_WORDS:
            continue

        # ✅ FIX: use mapped_type instead of undefined label
        if mapped_type != "PHONE" and is_contextual_false_positive(entity_text):
            continue

        span_key = (result.start, result.end)

        if mapped_type != "PHONE" and span_overlaps(span_key, seen_spans):
            continue

        detected.append({
            "entity": entity_text,
            "type": mapped_type,
            "source": "Presidio",
            "masked": False,
            "phi_relevant": True,
            "phi_category": get_phi_category(mapped_type),
            "risk_weight": get_risk_weight(mapped_type),
            "linkable_group": get_linkable_group(mapped_type)
        })

        seen_spans.add(span_key)

    # -------- REGEX --------

    regex_patterns={

        "PHONE":r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b",

        "MRN":r"\b(?:MRN|UHID|Patient\s?ID|Hospital\s?ID)[:\-\s]?[A-Z]*\d{4,12}\b",

        "RECORD_ID":r"\b(?:invoice|inv|bill\s?no|bill)[:\-\s]?[A-Z]*\d{3,}\b",

        "POLICY_NUMBER": r"\b(?:Policy\s?(?:No|Number)|Insurance\s?(?:No|#)|POL)[\s:\-]?[A-Z]*\d{5,12}\b",

        "AADHAR":r"\b\d{4}\s\d{4}\s\d{4}\b",

        "PAN":r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
    }

    for label,pattern in regex_patterns.items():

        for match in re.finditer(pattern,text,flags=re.IGNORECASE):

            entity_text=match.group().strip()
            span_key=(match.start(),match.end())

            if label=="PHONE":

                digits=re.sub(r"\D","",entity_text)

                if len(digits)!=10:
                    continue

            # 🔥 allow PHONE always
            if label != "PHONE" and not is_real_phi(entity_text, label):
                continue

            # 🔥 CRITICAL FIX: Always allow PHONE even if overlap
            if label != "PHONE" and span_overlaps(span_key, seen_spans):
                continue

            detected.append({
                "entity":entity_text,
                "type":label,
                "source":"Regex",
                "masked":False,
                "phi_relevant":True,
                "phi_category":get_phi_category(label),
                "risk_weight":get_risk_weight(label),
                "linkable_group":get_linkable_group(label)
            })

            seen_spans.add(span_key)

    # -------- DISEASE MODEL --------

    disease_entities=detect_diseases(text)

    for disease in disease_entities:

        start=disease.get("start")
        end=disease.get("end")

        if start is None or end is None:
            continue

        entity_text=text[start:end].strip()

        if entity_text.lower() in GENERIC_MEDICAL_WORDS:
            continue

        span_key=(start,end)

        if span_overlaps(span_key,seen_spans):
            continue

        detected.append({
            "entity":entity_text,
            "type":"DISEASE",
            "source":"Medical NER",
            "masked":False,
            "phi_relevant":True,
            "phi_category":get_phi_category("DISEASE"),
            "risk_weight":get_risk_weight("DISEASE"),
            "linkable_group":get_linkable_group("DISEASE")
        })

        seen_spans.add(span_key)

    return detected