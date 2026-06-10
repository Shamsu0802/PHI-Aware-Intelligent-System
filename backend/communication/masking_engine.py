#masking_engine.py
from typing import List, Dict

# ============================================================
# CONFIGURATION
# ============================================================

VALID_MASK_TYPES = {
    "PERSON",
    "PHONE",
    "EMAIL",
    "MRN",
    "POLICY_NUMBER",
    "AADHAAR",
    "PAN",
    "ADDRESS",
    "DIAGNOSIS",
    "DATE_OF_BIRTH"
}

# ============================================================
# TOKEN GENERATION
# ============================================================

def generate_mask_token(entity_type: str) -> str:
    """
    Standardized masking token.
    """
    return f"<{entity_type}>"


# ============================================================
# ENTITY FILTERING
# ============================================================

def _filter_valid_entities(phi_entities: List[Dict], text_length: int) -> List[Dict]:
    """
    Keep only valid PHI types and valid span boundaries.
    """

    valid = []

    for e in phi_entities:
        entity_type = e.get("type")
        start = e.get("start")
        end = e.get("end")

        if entity_type not in VALID_MASK_TYPES:
            continue

        if start is None or end is None:
            continue

        if not (0 <= start < end <= text_length):
            continue

        valid.append(e)

    return valid


# ============================================================
# OVERLAP RESOLUTION
# ============================================================

def _remove_overlaps(entities: List[Dict]) -> List[Dict]:
    """
    Remove overlapping spans.
    Prefer longer spans.
    """

    # Sort by span length descending
    entities = sorted(
        entities,
        key=lambda x: (x["end"] - x["start"]),
        reverse=True
    )

    selected = []
    occupied = set()

    for e in entities:
        span_range = set(range(e["start"], e["end"]))

        if span_range & occupied:
            continue

        selected.append(e)
        occupied.update(span_range)

    return selected


# ============================================================
# MAIN MASK FUNCTION
# ============================================================

def mask_text(text: str, phi_entities: List[Dict]) -> str:
    """
    Mask PHI using safe span replacement.

    Steps:
    1. Filter valid PHI types
    2. Remove overlapping spans
    3. Replace right-to-left
    """

    if not phi_entities:
        return text

    text_length = len(text)

    # Step 1: Filter valid types
    entities = _filter_valid_entities(phi_entities, text_length)

    if not entities:
        return text

    # Step 2: Deduplicate identical spans
    unique_spans = {}
    for e in entities:
        key = (e["start"], e["end"])
        if key not in unique_spans:
            unique_spans[key] = e

    entities = list(unique_spans.values())

    # Step 3: Remove overlaps
    entities = _remove_overlaps(entities)

    # Step 4: Sort right-to-left
    entities = sorted(
        entities,
        key=lambda x: x["start"],
        reverse=True
    )

    masked_text = text

    for entity in entities:
        start = entity["start"]
        end = entity["end"]
        entity_type = entity["type"]

        replacement = generate_mask_token(entity_type)

        # Defensive slicing
        masked_text = (
            masked_text[:start] +
            replacement +
            masked_text[end:]
        )

    return masked_text