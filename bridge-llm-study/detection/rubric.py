"""
Deterministic grading rules. Plain-English version lives in GRADING.md.

Each answer gets two labels:
  flagged    — model answered "yes" to the first question
  localized  — model named the actual planted bug (only scored where a bug exists)

Localization requires every group in LOCALIZE[attack][track] to match; within a group,
any one term counts. All matching is case-insensitive substring.
"""

import re

# Markdown emphasis and code ticks are presentation, not content; drop them and collapse
# whitespace so keyword matching sees the words a human reads, not "**0**" or "real\n vault".
def _norm(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[*_`#]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text

# attack -> track -> list of groups; each group is a list of synonyms (any one matches)
LOCALIZE = {
    "v1-mint-confusion": {
        "source": [
            ["lock"],
            ["approved", "collateral", "deposited token", "wrong mint", "any mint",
             "fake mint", "arbitrary mint", "mint confusion", "unverified mint"],
        ],
        "trace": [
            ["mint", "minted", "wrapped"],
            ["no collateral", "without collateral", "real vault", "fake vault",
             "realvault", "fakevault", "fake mint", "worthless", "unbacked",
             "no real", "not the genuine", "not the underlying", "0 tokens", "nothing"],
        ],
    },
    "v5-missing-signer": {
        "source": [
            ["signer", "signature", "is_signer", "signed", "sign the"],
            ["admin", "authority", "set_admin", "privileged"],
        ],
        "trace": [
            ["admin", "authority"],
            ["takeover", "privilege", "escalation", "changed", "change", "transfer",
             "unauthorized", "attacker"],
        ],
    },
}


def flagged_yes(answer: str):
    """First yes/no token answers question 1. Returns True/False, or None if neither found."""
    text = _norm(answer)
    start = text.find("1.")
    if start != -1:
        text = text[start:]
    m = re.search(r"\b(yes|no)\b", text)
    if not m:
        return None
    return m.group(1) == "yes"


def localized_correct(answer: str, attack: str, track: str):
    """True if the answer matches every required group for this attack+track."""
    groups = LOCALIZE.get(attack, {}).get(track)
    if not groups:
        return None
    text = _norm(answer)
    return all(any(term in text for term in group) for group in groups)
