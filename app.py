"""
app.py
------
AI Resume Screening System — Streamlit front end.

User journey: Upload Resume -> Upload JD -> Analyze -> ATS Score -> Charts ->
Matched Skills -> Missing Skills -> Suggestions -> Download Report.
"""

from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

from ats import calculate_ats_score
from jd_parser import extract_jd_text
from pdf_parser import PDFParsingError, extract_text
from suggestions import get_resume_suggestions
from utils import (
    extract_email,
    extract_phone,
    extract_skills,
    get_score_label,
    preprocess_text,
)

# ---------------------------------------------------------------------------
# Page configuration & styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Resume Screening System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {font-family: 'Inter', sans-serif;}
    h1, h2, h3, .app-header h1 {font-family: 'Poppins', sans-serif;}

    .main .block-container {padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1200px;}

    /* ---------------- Force light theme, ignore OS/browser dark mode ---------------- */
    :root {color-scheme: light only;}
    .stApp {
        background: linear-gradient(180deg, #F5F3FF 0%, #EFF6FF 45%, #FDF4FF 100%) !important;
        color: #1E1B2E !important;
    }
    .stApp, .stApp p, .stApp span, .stApp label, .stApp li,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] li,
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #1E1B2E !important;
    }
    [data-testid="stSidebar"] h3 {color: #4338CA !important;}
    [data-testid="stSidebar"] {color: #1E1B2E !important;}

    /* ---------------- Hide Deploy button & toolbar menu ---------------- */
    [data-testid="stAppDeployButton"],
    [data-testid="stToolbarActions"],
    #MainMenu,
    header [data-testid="stToolbar"] {
        display: none !important;
        visibility: hidden !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 2.5rem;
    }
    footer {visibility: hidden; height: 0;}

    /* ---------------- Header ---------------- */
    .app-header {
        position: relative;
        overflow: hidden;
        padding: 2rem 2.25rem;
        border-radius: 20px;
        background: linear-gradient(120deg, #6366F1 0%, #A855F7 45%, #EC4899 100%);
        background-size: 200% 200%;
        animation: gradientShift 8s ease infinite;
        color: white;
        margin-bottom: 1.75rem;
        box-shadow: 0 10px 30px rgba(124, 58, 237, 0.35);
    }
    @keyframes gradientShift {
        0%   {background-position: 0% 50%;}
        50%  {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    .app-header h1 {
        color: white;
        margin-bottom: 0.35rem;
        font-weight: 800;
        font-size: 2rem;
        letter-spacing: -0.02em;
    }
    .app-header p {color: #F3E8FF; margin: 0; font-size: 1rem;}

    /* ---------------- Metric cards ---------------- */
    .metric-card {
        position: relative;
        background: #FFFFFF;
        border: 1px solid #EEF0F5;
        border-radius: 16px;
        padding: 1.15rem 1.25rem 1rem;
        text-align: center;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.08);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        overflow: hidden;
    }
    .metric-card::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
        background: linear-gradient(90deg, #6366F1, #A855F7, #EC4899, #F59E0B);
        background-size: 300% 100%;
        animation: gradientShift 6s linear infinite;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 24px rgba(124, 58, 237, 0.18);
    }
    [data-testid="stMetricValue"] {
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        background: linear-gradient(120deg, #6366F1, #A855F7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* ---------------- Skill tag pills ---------------- */
    .skill-tag {
        display: inline-block;
        padding: 0.35rem 0.9rem;
        margin: 0.25rem;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 600;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .skill-tag:hover {transform: translateY(-2px) scale(1.04); box-shadow: 0 4px 10px rgba(0,0,0,0.08);}
    .tag-matched   {background: linear-gradient(120deg,#D1FAE5,#A7F3D0); color:#065F46; border:1px solid #6EE7B7;}
    .tag-missing   {background: linear-gradient(120deg,#FEE2E2,#FECACA); color:#991B1B; border:1px solid #FCA5A5;}
    .tag-neutral   {background: linear-gradient(120deg,#E0E7FF,#EDE9FE); color:#4338CA; border:1px solid #C7D2FE;}
    .tag-partial   {background: linear-gradient(120deg,#FEF3C7,#FDE68A); color:#92400E; border:1px solid #FCD34D;}

    /* ---------------- Buttons ---------------- */
    .stButton > button, .stDownloadButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        border: none !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }
    .stButton > button[kind="primary"], .stDownloadButton > button {
        background: linear-gradient(120deg, #6366F1, #A855F7) !important;
        color: white !important;
        box-shadow: 0 6px 16px rgba(124, 58, 237, 0.3) !important;
    }
    .stButton > button[kind="primary"]:hover, .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 22px rgba(124, 58, 237, 0.4) !important;
    }
    .stButton > button:not([kind="primary"]) {
        background: white !important;
        color: #4338CA !important;
        border: 1.5px solid #C7D2FE !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        border-color: #A855F7 !important;
        color: #7C3AED !important;
        transform: translateY(-1px);
    }

    /* ---------------- Tabs ---------------- */
    .stTabs [data-baseweb="tab-list"] {gap: 6px; flex-wrap: wrap;}
    .stTabs [data-baseweb="tab"] {
        border-radius: 999px !important;
        padding: 0.5rem 1.1rem !important;
        background: #F3F0FF;
        font-weight: 600;
        color: #6D28D9;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(120deg, #6366F1, #A855F7) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(124,58,237,0.3);
    }

    /* ---------------- Progress bar ---------------- */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6366F1, #A855F7, #EC4899) !important;
    }

    /* ---------------- File uploader ---------------- */
    [data-testid="stFileUploaderDropzone"] {
        border-radius: 14px !important;
        border: 2px dashed #C7B8FA !important;
        background: #FBFAFF !important;
        transition: border-color 0.2s ease, background 0.2s ease;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #A855F7 !important;
        background: #F5F0FF !important;
    }

    /* ---------------- Sidebar ---------------- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FAF5FF 0%, #F5F3FF 100%);
        border-right: 1px solid #EDE9FE;
    }

    /* ---------------- Alerts ---------------- */
    div[data-testid="stAlert"] {border-radius: 12px;}

    /* ---------------- Scrollbar ---------------- */
    ::-webkit-scrollbar {width: 10px; height: 10px;}
    ::-webkit-scrollbar-track {background: #F3F0FF;}
    ::-webkit-scrollbar-thumb {background: linear-gradient(180deg,#A855F7,#6366F1); border-radius: 10px;}

    /* ---------------- Responsive tweaks ---------------- */
    @media (max-width: 768px) {
        .app-header {padding: 1.35rem 1.25rem; border-radius: 16px;}
        .app-header h1 {font-size: 1.4rem;}
        .app-header p {font-size: 0.85rem;}
        .metric-card {padding: 0.85rem 0.75rem;}
        .main .block-container {padding-left: 0.75rem; padding-right: 0.75rem;}
        .stTabs [data-baseweb="tab"] {padding: 0.4rem 0.75rem !important; font-size: 0.85rem;}
    }
    @media (max-width: 480px) {
        .app-header h1 {font-size: 1.15rem;}
        .skill-tag {font-size: 0.75rem; padding: 0.28rem 0.65rem;}
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
# Storing results here (instead of only inside `if st.button(...)`) is what
# keeps the results visible after the user clicks "Download Report" -- in
# Streamlit, ANY button click reruns the whole script, and without this,
# the Analyze button's own state resets to False on that rerun, wiping the
# entire results view.
if "analysis" not in st.session_state:
    st.session_state.analysis = None


def render_skill_tags(skills, tag_class="tag-neutral", empty_message="None"):
    """Render a list of skills as styled pill tags (avoids repeating
    the same st.success()/st.error() loop pattern for each skill list)."""
    if not skills:
        st.caption(empty_message)
        return

    html = "".join(f'<span class="skill-tag {tag_class}">{s}</span>' for s in skills)
    st.markdown(html, unsafe_allow_html=True)


def build_report(data: dict) -> str:
    """Build the downloadable plain-text ATS report."""
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    label, _ = get_score_label(data["score"])

    lines = [
        "=" * 50,
        "        AI RESUME SCREENING REPORT",
        "=" * 50,
        f"Generated: {generated_at}",
        "",
        "-- Candidate Information --",
        f"Email : {data['email']}",
        f"Phone : {data['phone']}",
        "",
        "-- ATS Score --",
        f"Overall Score       : {data['score']}%  ({label})",
        f"Skill Match Score   : {data['skill_score']}%",
        f"Content Similarity  : {data['similarity_score']}%",
        "",
        "-- Resume Skills --",
        ", ".join(data["skills"]) if data["skills"] else "None detected",
        "",
        "-- Job Description Skills --",
        ", ".join(data["jd_skills"]) if data["jd_skills"] else "None detected",
        "",
        "-- Matched Skills --",
        ", ".join(data["matched_skills"]) if data["matched_skills"] else "None",
        "",
        "-- Missing Skills --",
        ", ".join(data["missing_skills"]) if data["missing_skills"] else "None",
        "",
        "-- Suggestions --",
    ]
    lines += [f"- {s}" for s in data["suggestions"]]
    lines += ["", "=" * 50, "End of Report", "=" * 50]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🤖 About")
    st.write(
        "This tool compares your resume against a job description and "
        "estimates how well it would perform against an ATS (Applicant "
        "Tracking System)."
    )

    with st.expander("ℹ️ How scoring works"):
        st.write(
            "- **Skill Match (75%)**: overlap between skills found in your "
            "resume and the JD, including close/near matches.\n"
            "- **Content Similarity (25%)**: how closely your resume's overall "
            "wording relates to the JD, using TF-IDF text similarity.\n"
            "- Scores of 85%+ are considered an excellent match."
        )

    st.divider()
    if st.button("🔄 Reset / Start Over", use_container_width=True):
        st.session_state.analysis = None
        st.rerun()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="app-header">
        <h1>🤖 AI Resume Screening System</h1>
        <p>Upload your resume and a job description to get an instant ATS match score.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Upload section
# ---------------------------------------------------------------------------
upload_col1, upload_col2 = st.columns(2)

with upload_col1:
    resume = st.file_uploader("📄 Upload Resume", type=["pdf"])
    if resume is not None:
        st.caption(f"✅ {resume.name} ready")

with upload_col2:
    job_description = st.file_uploader("📝 Upload Job Description", type=["txt", "pdf"])
    if job_description is not None:
        st.caption(f"✅ {job_description.name} ready")

analyze_clicked = st.button("🚀 Analyze Resume", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Analysis (runs only when the button is clicked; results are then SAVED to
# session_state so they persist across the reruns caused by other widgets,
# like the download button, further down the page).
# ---------------------------------------------------------------------------
if analyze_clicked:
    if resume is None:
        st.warning("⚠ Please upload a Resume first.")
    else:
        try:
            with st.status("Analyzing resume...", expanded=True) as status:
                st.write("📄 Reading resume...")
                raw_text = extract_text(resume)
                clean_text = preprocess_text(raw_text)

                jd_text = ""
                if job_description is not None:
                    st.write("📝 Reading job description...")
                    jd_text = extract_jd_text(job_description)

                st.write("🔍 Extracting skills & contact details...")
                email = extract_email(raw_text)
                phone = extract_phone(raw_text)
                skills = extract_skills(raw_text)
                jd_skills = extract_skills(jd_text)

                st.write("📊 Calculating ATS score...")
                result = calculate_ats_score(
                    skills, jd_skills, resume_text=clean_text, jd_text=preprocess_text(jd_text)
                )

                resume_suggestions = get_resume_suggestions(
                    result["score"],
                    result["missing_skills"],
                    matched_skills=result["matched_skills"],
                    similarity_score=result["similarity_score"] if jd_text else None,
                    email=email,
                    phone=phone,
                )

                status.update(label="Analysis complete!", state="complete", expanded=False)

            st.session_state.analysis = {
                "resume_name": resume.name,
                "jd_name": job_description.name if job_description else None,
                "clean_text": clean_text,
                "jd_text": jd_text,
                "email": email,
                "phone": phone,
                "skills": skills,
                "jd_skills": jd_skills,
                "score": result["score"],
                "skill_score": result["skill_score"],
                "similarity_score": result["similarity_score"],
                "matched_skills": result["matched_skills"],
                "partial_matches": result["partial_matches"],
                "missing_skills": result["missing_skills"],
                "suggestions": resume_suggestions,
                "jd_uploaded": job_description is not None,
            }

        except PDFParsingError as e:
            st.error(f"❌ {e}")
            st.session_state.analysis = None
        except Exception as e:  # noqa: BLE001 - deliberate catch-all safety net
            st.error(
                "❌ Something unexpected went wrong while analyzing your files. "
                "Please try a different file, or check that it isn't corrupted."
            )
            with st.expander("Technical details (for debugging)"):
                st.code(str(e))
            st.session_state.analysis = None

# ---------------------------------------------------------------------------
# Results (rendered from session_state so they survive reruns from the
# download button, tabs, or any other widget interaction)
# ---------------------------------------------------------------------------
data = st.session_state.analysis

if data:
    st.divider()

    label, status_kind = get_score_label(data["score"])

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Overall ATS Score", f"{data['score']}%", label)
        st.markdown("</div>", unsafe_allow_html=True)
    with m2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Skill Match", f"{data['skill_score']}%")
        st.markdown("</div>", unsafe_allow_html=True)
    with m3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Content Similarity", f"{data['similarity_score']}%")
        st.markdown("</div>", unsafe_allow_html=True)
    with m4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Matched / Missing", f"{len(data['matched_skills'])} / {len(data['missing_skills'])}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.progress(data["score"] / 100)

    if not data["jd_uploaded"]:
        st.info(
            "ℹ️ No Job Description was uploaded, so this score reflects only the "
            "resume's own content. Upload a JD to see a real skill-match comparison."
        )

    tab_overview, tab_skills, tab_suggestions, tab_docs, tab_download = st.tabs(
        ["📊 Overview", "🛠 Skills", "💡 Suggestions", "📄 Documents", "📥 Download"]
    )

    # ---- Overview tab ----------------------------------------------------
    with tab_overview:
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("📋 Candidate Details")
            st.write(f"📧 **Email:** {data['email']}")
            st.write(f"📞 **Phone:** {data['phone']}")

            donut = go.Figure(
                data=[
                    go.Pie(
                        labels=["Matched", "Remaining"],
                        values=[data["score"], max(0, 100 - data["score"])],
                        hole=0.65,
                        marker_colors=["#4F46E5", "#E5E7EB"],
                        textinfo="none",
                    )
                ]
            )
            donut.update_layout(
                showlegend=False,
                margin=dict(t=0, b=0, l=0, r=0),
                height=220,
                annotations=[dict(text=f"{data['score']}%", x=0.5, y=0.5, font_size=28, showarrow=False)],
            )
            st.plotly_chart(donut, use_container_width=True)

        with col_b:
            st.subheader("📊 Skill Match Breakdown")
            bar = go.Figure(
                data=[
                    go.Bar(
                        x=["Matched", "Partial", "Missing"],
                        y=[
                            len(data["matched_skills"]),
                            len(data["partial_matches"]),
                            len(data["missing_skills"]),
                        ],
                        marker_color=["#16A34A", "#D97706", "#DC2626"],
                    )
                ]
            )
            bar.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=280,
                yaxis_title="Number of Skills",
            )
            st.plotly_chart(bar, use_container_width=True)

    # ---- Skills tab --------------------------------------------------------
    with tab_skills:
        st.subheader("🛠 Skills Found in Resume")
        render_skill_tags(data["skills"], "tag-neutral", "No skills detected in the resume.")

        st.divider()
        st.subheader("✅ Matched Skills")
        render_skill_tags(data["matched_skills"], "tag-matched", "No matched skills yet.")

        if data["partial_matches"]:
            st.subheader("🟡 Partial / Near Matches")
            st.caption("These JD skills weren't an exact match but were very close to a skill in your resume.")
            for jd_skill, resume_skill in data["partial_matches"]:
                st.markdown(
                    f'<span class="skill-tag tag-partial">{jd_skill.title()} ≈ {resume_skill.title()}</span>',
                    unsafe_allow_html=True,
                )

        if data["jd_uploaded"]:
            st.divider()
            st.subheader("❌ Missing Skills")
            if data["missing_skills"]:
                render_skill_tags(data["missing_skills"], "tag-missing")
            else:
                st.success("🎉 Excellent! Your resume matches all required skills.")

    # ---- Suggestions tab -----------------------------------------------
    with tab_suggestions:
        st.subheader("💡 Resume Suggestions")
        for suggestion in data["suggestions"]:
            st.info(suggestion)

    # ---- Documents tab ---------------------------------------------------
    with tab_docs:
        with st.expander("📄 Resume Text Preview", expanded=False):
            st.write(data["clean_text"] or "No text extracted.")
        with st.expander("📝 Job Description Preview", expanded=False):
            st.write(data["jd_text"] or "No Job Description uploaded.")

    # ---- Download tab ------------------------------------------------------
    with tab_download:
        st.subheader("📥 Download Your ATS Report")
        st.caption("A plain-text summary of this analysis, ready to save or share.")
        report_text = build_report(data)
        st.text_area("Report preview", report_text, height=300)
        st.download_button(
            label="📥 Download ATS Report (.txt)",
            data=report_text,
            file_name="ATS_Report.txt",
            mime="text/plain",
            use_container_width=True,
        )