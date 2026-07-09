"""
suggestions.py
--------------
Generates actionable, human-readable resume improvement suggestions based
on the ATS scoring result and basic resume metadata (email/phone presence).
"""

from utils import get_score_label


def get_resume_suggestions(
    score,
    missing_skills,
    matched_skills=None,
    similarity_score=None,
    email=None,
    phone=None,
):
    """
    Generate resume improvement suggestions.

    Args:
        score: final ATS score (0-100).
        missing_skills: list of JD skills not found in the resume.
        similarity_score: (optional) TF-IDF content-similarity score (0-100).
        email: (optional) extracted email string, or "Not Found".
        phone: (optional) extracted phone string, or "Not Found".

    Returns:
        list[str] of suggestion messages, ready to display one-per-line.
    """
    suggestions = []

    # --- Contact info checks (independent of ATS score) -----------------
    if email is not None and email == "Not Found":
        suggestions.append(
            "📧 No email address was detected. Add a professional email "
            "address near the top of your resume so recruiters can reach you."
        )

    if phone is not None and phone == "Not Found":
        suggestions.append(
            "📞 No phone number was detected. Add a contact number so "
            "recruiters have more than one way to reach you."
        )

    # --- No JD skills to compare against ---------------------------------
    if score == 0 and not missing_skills and not (matched_skills or []):
        suggestions.append(
            "⚠️ No recognizable skills were found in the Job Description. "
            "Please upload a Job Description that lists specific required skills."
        )
        return suggestions

    # --- Perfect skill match ----------------------------------------------
    if score == 100:
        suggestions.append(
            "🎉 Excellent! Your resume matches the Job Description very well."
        )
        return suggestions

    label, _ = get_score_label(score)
    suggestions.append(f"📊 Overall match: {label} ({score}%).")

    if missing_skills:
        suggestions.append(
            "Improve your resume by adding the following skills if you have them:"
        )
        for skill in missing_skills:
            suggestions.append(f"✔ {skill.title()}")

    # --- Similarity-aware feedback (only if we have this signal) ---------
    if similarity_score is not None:
        if similarity_score < 30 and not missing_skills:
            suggestions.append(
                "📌 Your listed skills match well, but your resume's overall "
                "wording doesn't closely reflect the Job Description's language. "
                "Consider rephrasing experience bullet points to mirror key "
                "responsibilities mentioned in the JD."
            )
        elif similarity_score >= 70 and missing_skills:
            suggestions.append(
                "📌 Your resume's overall content is highly relevant to this "
                "role — focus specifically on adding the missing skills above "
                "to close the remaining gap."
            )

    suggestions.append("📌 Add relevant projects showcasing your key skills.")
    suggestions.append("📌 Mention certifications related to these technologies.")
    suggestions.append("📌 Quantify your achievements whenever possible.")

    return suggestions
