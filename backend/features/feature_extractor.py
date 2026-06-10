#feature_extractor.py
import json
import math
from collections import Counter


def extract_features(row):

    try:
        entities = row.get("entities", [])

        if isinstance(entities, str):
            entities = json.loads(entities)

    except Exception:
        entities = []

    # Ensure entities list
    if not isinstance(entities, list):
        entities = []

    num_entities = len(entities)

    # Normalize categories
    categories = [
        (e.get("category") or "").upper()
        for e in entities
    ]

    num_names = categories.count("NAME")
    num_contacts = categories.count("CONTACT")
    num_ids = categories.count("ID")
    num_locations = categories.count("LOCATION")
    num_financial = categories.count("FINANCIAL")
    num_diagnosis = categories.count("DIAGNOSIS")

    masked_ratio = 0.0

    if num_entities > 0:

        masked_count = sum(
            1 for e in entities
            if any(ch in str(e.get("entity", "")) for ch in {"X", "*"})
        )

        masked_ratio = masked_count / max(num_entities, 1)

    content = row.get("content", "") or ""

    word_count = len(content.split())

    phi_density = 0.0

    if word_count > 0:
        phi_density = num_entities / max(word_count, 1)

    identifier_total = num_ids + num_contacts + num_financial

    identifier_density = 0.0

    if num_entities > 0:
        identifier_density = identifier_total / max(num_entities, 1)

    # Identity linkage (name + identifiers)
    identity_linkage = min(
        1.0,
        (num_names * identifier_total) / 4.0
    )

    # Medical identity coupling (diagnosis + identifiers)
    medical_identity_coupling = min(
        1.0,
        (num_diagnosis * (num_names + identifier_total)) / 6.0
    )

    entropy = 0.0

    if categories:

        counts = Counter(categories)

        total = sum(counts.values())

        if total > 0:

            entropy = -sum(
                (c / total) * math.log((c / total) + 1e-9)
                for c in counts.values()
            )

    # Context features
    recipient_external = 1.0 if row.get("recipient_type") == "external" else 0.0

    attachment_present = 1.0 if row.get("attachment_present") else 0.0

    late_night = 1.0 if row.get("time_of_day") == "late_night" else 0.0

    # Clamp numerical ranges (stability)
    phi_density = min(phi_density, 1.0)
    identifier_density = min(identifier_density, 1.0)
    masked_ratio = min(masked_ratio, 1.0)

    # EXACTLY 13 FEATURES (MODEL COMPATIBLE)

    return [

        float(num_entities),
        float(num_names),
        float(num_contacts),
        float(num_ids),
        float(num_locations),
        float(num_financial),
        float(num_diagnosis),
        float(masked_ratio),
        float(phi_density),
        float(identifier_density),
        float(identity_linkage),
        float(recipient_external),
        float(late_night)
    ]