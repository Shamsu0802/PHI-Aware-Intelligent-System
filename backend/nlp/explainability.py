#explainability.py
def generate_explanation(
    content_score: float,
    context_score: float,
    behavior_score: float,
    composite_score: float,
    content_pct: int,
    context_pct: int,
    behavior_pct: int
):
    """
    Generates model-aligned, human-readable explanations
    strictly derived from numeric model outputs.

    Generates human-readable explanations derived from model outputs 
    combined with deterministic interpretation logic.
    No PHI assumptions.
    Examiner-safe.
    """

    explanations = []

    # -------------------- CONTRIBUTION SUMMARY --------------------

    explanations.append(
        f"Content sensitivity contributes {content_pct}% to the overall risk based on weighted model influence"
    )

    explanations.append(
        f"Contextual factors contribute {context_pct}% to the overall risk based on transmission conditions"
    )

    if behavior_score > 0:
        explanations.append(
            f"Behavioral anomaly patterns contribute {behavior_pct}% "
            f"to the overall risk"
        )
    else:
        explanations.append(
            "No significant behavioral deviation detected in communication patterns"
        )

    # -------------------- WHAT MATTERED MOST --------------------

    dominant_factor = max(
        [
            ("content", content_pct),
            ("context", context_pct),
            ("behavior", behavior_pct),
        ],
        key=lambda x: x[1]
    )[0]

    if dominant_factor == "content":
        explanations.append(
            "The risk is primarily driven by sensitive content within the communication"
        )
    elif dominant_factor == "context":
        explanations.append(
            "The risk is primarily influenced by external communication context and transmission conditions"
        )
    else:
        explanations.append(
            "Unusual communication behavior contributed to the elevated risk"
        )

    # -------------------- WHAT DID NOT MATTER --------------------

    if behavior_pct == 0:
        explanations.append(
            "Behavioral patterns were consistent with normal historical communication"
        )

    if context_pct < 20:
        explanations.append(
            "Contextual signals had limited influence on the final risk assessment"
        )

    # -------------------- FINAL DECISION --------------------
    explanations.append(
        "Contribution percentages are computed using normalized weighted contributions of content sensitivity, contextual exposure, and behavioral anomaly scores in the composite risk model"
    )
    
    explanations.append(
        f"Final composite risk score is {round(composite_score, 3)}"
    )

    return explanations
