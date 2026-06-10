#rewrite_explainer.py
def explain_rewrite(phi_entities):

    explanation_flags = {
        "PERSON": False,
        "PHONE": False,
        "EMAIL": False,
        "POLICY_NUMBER": False
    }

    for e in phi_entities:

        entity_type = e.get("type")

        if entity_type in explanation_flags:
            explanation_flags[entity_type] = True

    explanations = []

    if explanation_flags["PERSON"]:
        explanations.append(
            "Patient name masked to reduce identity disclosure risk"
        )

    if explanation_flags["PHONE"]:
        explanations.append(
            "Phone number removed to prevent direct contact exposure"
        )

    if explanation_flags["EMAIL"]:
        explanations.append(
            "Email address removed to prevent direct external transmission"
        )

    if explanation_flags["POLICY_NUMBER"]:
        explanations.append(
            "Insurance identifier removed to prevent financial data exposure"
        )

    # This is always true for external communication rewrites
    explanations.append(
        "External medical document sharing redirected to secure hospital communication portal"
    )

    return explanations