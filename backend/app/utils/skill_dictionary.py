"""Controlled skill dictionary for resume extraction and normalization."""

SKILL_ALIASES: dict[str, str] = {
    "c plus plus": "c++",
    "cpp": "c++",
    "c#": "c#",
    "csharp": "c#",
    "js": "javascript",
    "ts": "typescript",
    "node": "node.js",
    "nodejs": "node.js",
    "react.js": "react",
    "reactjs": "react",
    "postgresql": "sql",
    "postgres": "sql",
    "mysql": "sql",
    "dbms": "dbms",
    "database management": "dbms",
    "data structures": "dsa",
    "data structure and algorithms": "dsa",
    "machine learning": "machine learning",
    "ml": "machine learning",
    "artificial intelligence": "ai",
    "git version control": "git",
    "tensorflow": "tensorflow",
    "pytorch": "pytorch",
}

CANONICAL_SKILLS: set[str] = {
    "python",
    "c++",
    "c",
    "java",
    "javascript",
    "typescript",
    "react",
    "node.js",
    "sql",
    "dbms",
    "dsa",
    "oop",
    "git",
    "machine learning",
    "ai",
    "tensorflow",
    "pytorch",
    "html",
    "css",
    "docker",
    "kubernetes",
    "aws",
    "linux",
    "operating systems",
    "computer networks",
    "aptitude",
}


def canonicalize_skill(raw: str) -> str | None:
    key = raw.strip().lower()
    key = " ".join(key.split())
    if key in SKILL_ALIASES:
        key = SKILL_ALIASES[key]
    if key in CANONICAL_SKILLS:
        return key.title() if key not in {"c++", "c#", "ai", "dsa", "oop", "sql", "dbms"} else key.upper() if key in {"dsa", "oop", "sql", "dbms", "ai"} else key
    for skill in CANONICAL_SKILLS:
        if skill == key or skill in key.split():
            display = skill.title() if skill not in {"c++", "ai", "dsa", "oop", "sql", "dbms"} else skill.upper()
            return display
    return None
