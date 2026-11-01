import fitz

from app.utils.skill_dictionary import CANONICAL_SKILLS, canonicalize_skill


def extract_text_from_pdf_bytes(data: bytes) -> str:
    doc = fitz.open(stream=data, filetype="pdf")
    parts: list[str] = []
    for page in doc:
        parts.append(page.get_text())
    doc.close()
    return "\n".join(parts)


def extract_skills_from_text(text: str) -> list[str]:
    lowered = text.lower()
    found: set[str] = set()
    for skill in CANONICAL_SKILLS:
        if skill in lowered:
            canon = canonicalize_skill(skill)
            if canon:
                found.add(canon)
    # token-ish scan for aliases
    for token in lowered.replace("/", " ").replace(",", " ").split():
        canon = canonicalize_skill(token)
        if canon:
            found.add(canon)
    return sorted(found)
