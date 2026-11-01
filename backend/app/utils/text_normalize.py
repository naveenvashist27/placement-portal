import re


def normalize_question_text(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t)
    replacements = {
        "explain": "what is",
        "describe": "what is",
        "define": "what is",
        "tell me about": "what is",
    }
    for src, dst in replacements.items():
        if t.startswith(src + " "):
            t = dst + t[len(src) :]
    return t.strip()


def normalize_skill_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())
