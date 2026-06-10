#disease_ner.py
import numpy as np
import os
import pickle
import spacy
import re

from keras.models import load_model
from keras.preprocessing.sequence import pad_sequences
from presidio_analyzer import AnalyzerEngine

# ------------------ LOAD NLP ------------------

nlp = spacy.load("en_core_web_sm")
presidio_analyzer = AnalyzerEngine()

INVALID_DISEASE_WORDS = {
    "was", "is", "were", "are", "has", "have", "had",
    "with", "from", "and", "the", "a", "an", "of",
    "due", "to", "in", "on"
}

# tokens that must never extend disease entities
DISEASE_STOP_WORDS = {
    "send","sent","report","reports","please","confirm",
    "check","forward","share","attached","mail","message",
    "call","contact","doctor","nurse"
}

# words that should never START a disease entity
DISEASE_PREFIX_BLOCK = {
    "uncontrolled","controlled","mild","moderate",
    "severe","acute","chronic","possible"
}

# measurement units incorrectly captured as disease
MEASUREMENT_UNITS = {
    "mg","mg/dl","mmhg","bpm","ml","kg","cm","mm","dl"
}

# ------------------ PATHS ------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "models")

MODEL_PATH = os.path.join(MODEL_DIR, "disease_ner_model.keras")
TOKENIZER_PATH = os.path.join(MODEL_DIR, "tokenizer.pkl")
TAG2IDX_PATH = os.path.join(MODEL_DIR, "tag2idx.npy")
IDX2TAG_PATH = os.path.join(MODEL_DIR, "idx2tag.npy")

# ------------------ SAFE MODEL LOADING ------------------

model = None
tokenizer = None
tag2idx = None
idx2tag = None
MAX_LEN = None

try:
    model = load_model(MODEL_PATH, compile=False, safe_mode=False)

    with open(TOKENIZER_PATH, "rb") as f:
        tokenizer = pickle.load(f)

    tag2idx = np.load(TAG2IDX_PATH, allow_pickle=True).item()
    idx2tag = np.load(IDX2TAG_PATH, allow_pickle=True).item()

    MAX_LEN = model.input_shape[1]

    print("✅ Disease NER model loaded successfully")

except Exception as e:
    print("⚠️ Disease NER model could not be loaded")
    print("Reason:", e)

# ------------------ HELPERS ------------------

def is_valid_word(token: str):
    return bool(re.search(r"[A-Za-z]", token))


def is_measurement(token: str):
    t = token.lower().strip()
    return t in MEASUREMENT_UNITS or re.match(r'^\d+(\.\d+)?$', t)


# ------------------ DISEASE DETECTION ------------------

def detect_diseases(text: str):
    """
    Detect disease entities using trained NER model.
    Returns disease spans with correct token boundaries.
    """

    if model is None or tokenizer is None:
        return []

    doc = nlp(text)

    words = [token.text for token in doc]

    sequence = [
        tokenizer.word_index.get(word.lower(), 1)
        for word in words
    ]

    padded = pad_sequences(
        [sequence],
        maxlen=MAX_LEN,
        padding="post",
        truncating="post"
    )

    preds = model.predict(padded, verbose=0)[0]

    entities = []
    current_tokens = []
    start_char = None

    for token, pred in zip(doc, preds[:len(doc)]):

        tag = idx2tag[np.argmax(pred)]
        token_text = token.text.lower()

        # hard filters
        if (
            not is_valid_word(token_text)
            or token_text in INVALID_DISEASE_WORDS
            or token_text in DISEASE_STOP_WORDS
            or is_measurement(token_text)
        ):

            if current_tokens:
                entities.append({
                    "entity": " ".join(current_tokens),
                    "start": start_char,
                    "end": token.idx
                })
                current_tokens = []
                start_char = None

            continue

        # prevent adjectives starting diseases
        if tag == "B-DISEASE" and token_text in DISEASE_PREFIX_BLOCK:
            continue

        # Begin entity
        if tag == "B-DISEASE":

            if current_tokens:
                entities.append({
                    "entity": " ".join(current_tokens),
                    "start": start_char,
                    "end": token.idx
                })

            current_tokens = [token.text]
            start_char = token.idx

        # Continue entity
        elif tag == "I-DISEASE" and current_tokens:

            if token_text not in DISEASE_PREFIX_BLOCK:
                current_tokens.append(token.text)

        # End entity
        else:

            if current_tokens:
                entities.append({
                    "entity": " ".join(current_tokens),
                    "start": start_char,
                    "end": token.idx
                })

                current_tokens = []
                start_char = None

    # Final entity
    if current_tokens:

        last_token = list(doc)[-1]

        entities.append({
            "entity": " ".join(current_tokens),
            "start": start_char,
            "end": last_token.idx + len(last_token.text)
        })

    # Final cleanup pass
    cleaned_entities = []

    for e in entities:

        text_val = e["entity"].strip().lower()

        if len(text_val) <= 3:
            continue

        if text_val in MEASUREMENT_UNITS:
            continue

        cleaned_entities.append(e)

    return cleaned_entities


# ------------------ PHI DETECTION ------------------

def detect_phi(text: str):

    detected = []

    # ------------------ spaCy NER ------------------

    doc = nlp(text)

    for ent in doc.ents:

        if ent.label_ in ["PERSON", "DATE", "GPE"]:

            detected.append({
                "entity": ent.text.strip(),
                "type": ent.label_,
                "source": "spaCy"
            })

    # ------------------ Presidio ------------------

    presidio_results = presidio_analyzer.analyze(
        text=text,
        language="en"
    )

    for result in presidio_results:

        detected.append({
            "entity": text[result.start:result.end].strip(),
            "type": result.entity_type,
            "source": "Presidio"
        })

    # ------------------ REGEX PHI ------------------

    regex_patterns = {
        "PHONE": r"\b\d{10}\b",
        "MRN": r"\bMRN\d{4,}\b",
        "INSURANCE_NUMBER": r"\bINS\d{4,}\b",
        "POLICY_NUMBER": r"\bPOL\d{4,}\b"
    }

    for label, pattern in regex_patterns.items():

        for match in re.findall(pattern, text):

            detected.append({
                "entity": match,
                "type": label,
                "source": "Regex"
            })

    # ------------------ REMOVE DUPLICATES ------------------

    unique = {}

    for e in detected:

        key = (e["entity"].lower(), e["type"])
        unique[key] = e

    detected = list(unique.values())

    # ------------------ CLEAN PERSON DUPLICATES ------------------

    persons = [e for e in detected if e["type"] == "PERSON"]
    non_persons = [e for e in detected if e["type"] != "PERSON"]

    cleaned_persons = []

    for p in persons:

        if not any(
            p["entity"].lower() != other["entity"].lower()
            and p["entity"].lower() in other["entity"].lower()
            for other in persons
        ):
            cleaned_persons.append(p)

    detected = cleaned_persons + non_persons

    # ------------------ Disease NER ------------------

    disease_entities = detect_diseases(text)

    person_tokens = set()

    for e in cleaned_persons:
        for w in e["entity"].lower().split():
            person_tokens.add(w)

    for disease in disease_entities:

        disease_text = disease["entity"].strip().lower()
        disease_tokens = set(disease_text.split())

        if disease_tokens & person_tokens:
            continue

        if disease_text in INVALID_DISEASE_WORDS:
            continue

        if len(disease_text) <= 3:
            continue

        detected.append({
            "entity": disease["entity"].strip(),
            "type": "DISEASE",
            "source": "Trained NER Model"
        })

    return detected