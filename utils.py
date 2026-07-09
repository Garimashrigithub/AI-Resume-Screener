"""
utils.py
--------
Shared text-processing helpers used across the AI Resume Screening System:
- Text cleaning
- Contact info extraction (email / phone)
- Skill extraction from free text
- Shared score-labeling logic (used by the UI, the suggestions engine, and the report)

These functions are intentionally dependency-free (no streamlit / fitz imports)
so they can be unit-tested in isolation.
"""

import re

# ---------------------------------------------------------------------------
# Skill vocabulary
# ---------------------------------------------------------------------------
# Canonical (lowercase) skill list. This is the single source of truth for
# every skill the system knows how to recognize. Add new skills here only.
SKILLS_DB = [
    "python",
    "java",
    "c++",
    "sql",
    "mysql",
    "mongodb",
    "machine learning",
    "deep learning",
    "tensorflow",
    "keras",
    "pandas",
    "numpy",
    "matplotlib",
    "power bi",
    "excel",
    "streamlit",
    "flask",
    "django",
    "git",
    "github",
    "html",
    "css",
    "javascript",
    # --- Soft skills (added: JD files frequently list these, and the
    #     original skill list had no way to ever match them) ---
    "communication",
    "teamwork",
    "leadership",
    "problem solving",
    "time management",
    "adaptability",
    "critical thinking",
]

# How each canonical skill should be *displayed* to the user.
# Falls back to .title() automatically if a skill isn't listed here,
# so adding a new skill to SKILLS_DB never breaks display formatting.
SKILL_DISPLAY_NAMES = {
    "sql": "SQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "html": "HTML",
    "css": "CSS",
    "c++": "C++",
    "power bi": "Power BI",
    "tensorflow": "TensorFlow",
    "numpy": "NumPy",
    "github": "GitHub",
    "javascript": "JavaScript",
}

# Small, deliberately conservative alias map: only abbreviations that are
# very unlikely to appear as false positives inside other words.
# (We do NOT alias things like "bi" or "ml" alone without context to avoid
# matching unrelated words.)
SKILL_ALIASES = {
    "ml": "machine learning",
    "js": "javascript",
    "py": "python",
    "dl": "deep learning",
}


def _display_name(skill: str) -> str:
    """Return the properly capitalized display name for a canonical skill."""
    return SKILL_DISPLAY_NAMES.get(skill, skill.title())


def preprocess_text(text: str) -> str:
    """
    Clean extracted resume/JD text for display purposes.

    Removes URLs, email addresses, and phone-like number sequences so the
    "preview" shown to the user isn't cluttered with raw contact details,
    and lowercases + collapses whitespace for readability.
    """
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"http\S+|www\S+", "", text)          # URLs
    text = re.sub(r"\S+@\S+", "", text)                  # emails
    text = re.sub(r"\+?\d[\d\s\-]{8,}\d", "", text)       # phone-like numbers
    text = re.sub(r"\s+", " ", text)                      # collapse whitespace

    return text.strip()


def extract_email(text: str) -> str:
    """
    Extract the first email address found in raw resume text.
    Returns "Not Found" if no email is present (e.g. missing-email test case).
    """
    if not text:
        return "Not Found"

    matches = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return matches[0] if matches else "Not Found"


def extract_phone(text: str) -> str:
    """
    Extract a plausible phone number from raw resume text.

    Tightened compared to the original: requires digit-grouping that looks
    like a real phone number (optional country code + 9-14 digits total,
    allowing spaces/hyphens/parentheses as separators) instead of matching
    any long run of digits, which previously could false-positive on dates,
    zip codes, or course/reference numbers.
    """
    if not text:
        return "Not Found"

    pattern = r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?){2,4}\d{2,4}"
    candidates = re.findall(pattern, text)

    for candidate in candidates:
        digit_count = len(re.sub(r"\D", "", candidate))
        # A real phone number has roughly 9-14 digits. This filters out
        # short numeric noise (e.g. "2024", "100%") and overly long strings.
        if 9 <= digit_count <= 14:
            return candidate.strip()

    return "Not Found"


def extract_skills(text: str) -> list:
    """
    Extract known technical/soft skills from free text.

    Uses word-boundary-aware matching (fixes the original bug where "java"
    would incorrectly match inside "javascript"), and normalizes common
    abbreviations (ML, JS, PY, DL) to their canonical skill name.

    Returns a sorted list of properly-cased skill names, e.g. ["Python", "SQL"].
    """
    if not text:
        return []

    text = text.lower()
    found = set()

    # 1. Match canonical skills with word boundaries so "java" doesn't
    #    match inside "javascript", "css" doesn't match inside "cssie", etc.
    for skill in SKILLS_DB:
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
        if re.search(pattern, text):
            found.add(skill)

    # 2. Match conservative abbreviations/aliases and map them to the
    #    canonical skill (e.g. standalone "ML" -> "machine learning").
    for alias, canonical in SKILL_ALIASES.items():
        pattern = r"(?<!\w)" + re.escape(alias) + r"(?!\w)"
        if re.search(pattern, text, flags=re.IGNORECASE if alias.isupper() else 0):
            # Only match aliases as an all-caps/standalone token to reduce
            # false positives, e.g. avoid matching "py" inside "happy".
            if re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text):
                found.add(canonical)

    return sorted(_display_name(skill) for skill in found)


def get_score_label(score: int) -> tuple:
    """
    Shared scoring-tier logic used by the UI, the suggestions engine, and
    the downloadable report, so the "what counts as a good score" rule
    lives in exactly one place.

    Returns (label, streamlit_status) where streamlit_status is one of
    "success", "info", "warning" — safe to feed directly to getattr(st, status).
    """
    if score >= 85:
        return "Excellent Match", "success"
    if score >= 60:
        return "Good Match", "info"
    if score >= 35:
        return "Fair Match", "warning"
    return "Needs Improvement", "error"
