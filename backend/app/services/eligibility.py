"""Eligibility rules for a registration form, checked against a student's profile values."""

import json

PROFILE_LABELS = {
    "cgpa": "CGPA",
    "tenth_percentage": "10th %",
    "twelfth_percentage": "12th %",
    "has_atkt": "ATKT status",
    "course": "course",
    "batch": "batch",
    "graduation_year": "passing year",
}


def validate_rules(raw: str | None) -> str | None:
    """Return normalised JSON for storing, or raise ValueError for a malformed rule set."""
    if not raw:
        return None
    try:
        rules = json.loads(raw)
    except ValueError:
        raise ValueError("eligibility_json must be valid JSON")
    if not isinstance(rules, dict):
        raise ValueError("eligibility_json must be an object")
    clean: dict = {}
    for key, upper in (("min_cgpa", 10), ("min_tenth_percentage", 100), ("min_twelfth_percentage", 100)):
        if rules.get(key) not in (None, ""):
            value = float(rules[key])
            if not 0 <= value <= upper:
                raise ValueError(f"{key} must be between 0 and {upper}")
            clean[key] = value
    if rules.get("no_atkt"):
        clean["no_atkt"] = True
    for key in ("courses", "batches"):
        items = [str(x).strip() for x in rules.get(key) or [] if str(x).strip()]
        if items:
            clean[key] = items
    years = [int(x) for x in rules.get("passing_years") or []]
    if years:
        clean["passing_years"] = years
    return json.dumps(clean) if clean else None


def describe(rules: dict) -> list[str]:
    out = []
    if "min_cgpa" in rules:
        out.append(f"CGPA at least {rules['min_cgpa']:g}")
    if "min_tenth_percentage" in rules:
        out.append(f"10th % at least {rules['min_tenth_percentage']:g}")
    if "min_twelfth_percentage" in rules:
        out.append(f"12th % at least {rules['min_twelfth_percentage']:g}")
    if rules.get("no_atkt"):
        out.append("No current ATKT")
    if rules.get("courses"):
        out.append("Course: " + ", ".join(rules["courses"]))
    if rules.get("batches"):
        out.append("Batch: " + ", ".join(rules["batches"]))
    if rules.get("passing_years"):
        out.append("Passing year: " + ", ".join(str(y) for y in rules["passing_years"]))
    return out


def check(rules_json: str | None, values: dict) -> list[str]:
    """Reasons the student does not qualify (empty list = eligible)."""
    if not rules_json:
        return []
    rules = json.loads(rules_json)
    reasons: list[str] = []

    def missing(key: str) -> None:
        reasons.append(f"Add your {PROFILE_LABELS[key]} to your profile")

    for rule, key, label in (
        ("min_cgpa", "cgpa", "CGPA"),
        ("min_tenth_percentage", "tenth_percentage", "10th %"),
        ("min_twelfth_percentage", "twelfth_percentage", "12th %"),
    ):
        if rule in rules:
            have = values.get(key)
            if have is None:
                missing(key)
            elif have < rules[rule]:
                reasons.append(f"{label} must be at least {rules[rule]:g} (yours is {have:g})")
    if rules.get("no_atkt"):
        if values.get("has_atkt") is None:
            missing("has_atkt")
        elif values["has_atkt"]:
            reasons.append("Students with a current ATKT are not eligible")
    for rule, key in (("courses", "course"), ("batches", "batch")):
        if rules.get(rule):
            have = (values.get(key) or "").strip().lower()
            if not have:
                missing(key)
            elif have not in [x.lower() for x in rules[rule]]:
                reasons.append(f"Only for {key}: {', '.join(rules[rule])}")
    if rules.get("passing_years"):
        have = values.get("graduation_year")
        if have is None:
            missing("graduation_year")
        elif have not in rules["passing_years"]:
            reasons.append(f"Only for passing year: {', '.join(str(y) for y in rules['passing_years'])}")
    return reasons
