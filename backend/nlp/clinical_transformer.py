#clinical_transformer.py
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

MODEL_NAME = "StanfordAIMI/stanford-deidentifier-base"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForTokenClassification.from_pretrained(MODEL_NAME)

ner_pipeline = pipeline(
    "ner",
    model=model,
    tokenizer=tokenizer,
    aggregation_strategy="simple"
)

def detect_transformer_phi(text, offset=0):

    results = ner_pipeline(text)
    entities = []

    for r in results:
        entities.append({
            "entity": r["word"],
            "type": r["entity_group"],
            "source": "ClinicalTransformer",
            "masked": False,
            "phi_relevant": True,
            "start": r["start"] + offset,
            "end": r["end"] + offset
        })

    return entities