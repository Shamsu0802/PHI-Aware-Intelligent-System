import re
import random


# --------------------------------------------------------
# PHONE OBFUSCATION ATTACKS
# --------------------------------------------------------

def phone_variants(phone):

    variants = []

    variants.append(phone)
    variants.append(phone[:5] + " " + phone[5:])
    variants.append(phone[:3] + "-" + phone[3:6] + "-" + phone[6:])
    variants.append(phone.replace("9", "(9)"))

    return variants


# --------------------------------------------------------
# EMAIL OBFUSCATION ATTACKS
# --------------------------------------------------------

def email_variants(email):

    variants = []

    variants.append(email)

    variants.append(
        email.replace("@", " [at] ")
    )

    variants.append(
        email.replace(".", " dot ")
    )

    variants.append(
        email.replace("@", "(at)")
    )

    return variants


# --------------------------------------------------------
# NAME OBFUSCATION ATTACKS
# --------------------------------------------------------

def name_variants(name):

    parts = name.split()

    variants = []

    variants.append(name)

    variants.append(
        " ".join(p[0] + "." for p in parts)
    )

    variants.append(
        "_".join(parts)
    )

    return variants


# --------------------------------------------------------
# MAIN ATTACK GENERATOR
# --------------------------------------------------------

def generate_attack_variants(text):

    variants = [text]

    phones = re.findall(r"\b[6-9]\d{9}\b", text)

    emails = re.findall(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        text
    )

    for phone in phones:

        for v in phone_variants(phone):

            variants.append(text.replace(phone, v))

    for email in emails:

        for v in email_variants(email):

            variants.append(text.replace(email, v))

    return list(set(variants))