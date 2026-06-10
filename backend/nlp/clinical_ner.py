#clinical_ner.py
import stanza

nlp = stanza.Pipeline("en", processors="tokenize,ner", use_gpu=False)

def detect_stanza_entities(text):
    entities = []
    doc = nlp(text)

    for sentence in doc.sentences:
        for ent in sentence.ents:
            if ent.type in ["PERSON", "ORG", "GPE"]:
                entities.append({
                    "entity": ent.text,
                    "type": ent.type,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "source": "stanza"
                })

    return entities