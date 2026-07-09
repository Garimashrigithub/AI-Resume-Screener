"""
ats.py
------
Core ATS (Applicant Tracking System) scoring logic.

Combines two signals:
  1. Skill overlap between resume and JD (exact + fuzzy/near-matches),
     which is explainable and drives the Matched/Missing skill lists.
  2. Optional TF-IDF cosine similarity between the full resume text and
     JD text, which captures contextual relevance beyond a fixed keyword
     list (e.g. rewarding a resume that discusses relevant experience in
     prose, not just as a bullet-listed skill).

If only skill lists are provided (no raw text), the function degrades
gracefully to skill-only scoring — nothing breaks for existing callers.
"""

import difflib

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _SKLEARN_AVAILABLE = True
except ImportError:
    # If scikit-learn isn't installed, the app still works — it just
    # falls back to skill-only scoring instead of crashing on import.
    _SKLEARN_AVAILABLE = False

# Weight given to skill-matching vs. content-similarity in the final score.
SKILL_WEIGHT = 0.75
SIMILARITY_WEIGHT = 0.25

# A near-match must be at least this similar (0-1) to count as a fuzzy match.
FUZZY_MATCH_THRESHOLD = 0.82

# Fuzzy matches count for less than an exact match, since they're a
# lower-confidence signal.
FUZZY_MATCH_WEIGHT = 0.6


def _compute_text_similarity(resume_text: str, jd_text: str) -> float:
    """
    Compute TF-IDF cosine similarity (0-100) between resume and JD text.
    Returns 0.0 if either text is too short/empty or scikit-learn is
    unavailable, rather than raising an error.
    """
    if not _SKLEARN_AVAILABLE:
        return 0.0

    if not resume_text or not jd_text:
        return 0.0

    if len(resume_text.split()) < 3 or len(jd_text.split()) < 3:
        # Too little text for TF-IDF to produce a meaningful vocabulary.
        return 0.0

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform([resume_text, jd_text])
        similarity = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        return round(float(similarity) * 100, 2)
    except ValueError:
        # Can happen if, after stop-word removal, the vocabulary is empty.
        return 0.0


def calculate_ats_score(resume_skills, jd_skills, resume_text: str = "", jd_text: str = ""):
    """
    Compare resume skills with JD skills and calculate an ATS score.

    Args:
        resume_skills: list of skills extracted from the resume.
        jd_skills: list of skills extracted from the job description.
        resume_text: (optional) full cleaned resume text, enables the
            content-similarity component of the score.
        jd_text: (optional) full JD text, enables the content-similarity
            component of the score.

    Returns:
        dict with keys:
            score            (int)   final blended 0-100 score
            skill_score      (int)   0-100 score from skill overlap alone
            similarity_score (float) 0-100 TF-IDF content similarity (0 if unavailable)
            matched_skills   (list)  skills present in both resume and JD
            partial_matches  (list)  (jd_skill, resume_skill) near-matches, not exact
            missing_skills   (list)  JD skills with no match (exact or fuzzy) in resume
    """
    resume_set = {skill.lower() for skill in resume_skills}
    jd_set = {skill.lower() for skill in jd_skills}

    if not jd_set:
        # No JD skills to compare against — score is meaningless, not "0/failed".
        return {
            "score": 0,
            "skill_score": 0,
            "similarity_score": 0.0,
            "matched_skills": [],
            "partial_matches": [],
            "missing_skills": [],
        }

    exact_matched = resume_set & jd_set
    remaining_jd = jd_set - exact_matched

    partial_matches = []
    matched_weight = float(len(exact_matched))

    # For any JD skill not exactly matched, look for a close (fuzzy) match
    # among the resume's skills — catches minor spelling/typo variants.
    still_missing = set()
    for jd_skill in remaining_jd:
        close = difflib.get_close_matches(
            jd_skill, resume_set, n=1, cutoff=FUZZY_MATCH_THRESHOLD
        )
        if close:
            partial_matches.append((jd_skill, close[0]))
            matched_weight += FUZZY_MATCH_WEIGHT
        else:
            still_missing.add(jd_skill)

    skill_score = round((matched_weight / len(jd_set)) * 100)
    skill_score = min(skill_score, 100)

    similarity_score = _compute_text_similarity(resume_text, jd_text)

    if resume_text and jd_text and _SKLEARN_AVAILABLE:
        final_score = round(
            SKILL_WEIGHT * skill_score + SIMILARITY_WEIGHT * similarity_score
        )
    else:
        # No text supplied (or sklearn unavailable) -> skill score is the
        # whole picture, same behavior as the original implementation.
        final_score = skill_score

    final_score = max(0, min(final_score, 100))

    return {
        "score": final_score,
        "skill_score": skill_score,
        "similarity_score": similarity_score,
        "matched_skills": sorted(exact_matched),
        "partial_matches": sorted(partial_matches),
        "missing_skills": sorted(still_missing),
    }
