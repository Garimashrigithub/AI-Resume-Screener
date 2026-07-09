# 🤖 ML ATS Resume Screener

A Machine Learning-based ATS (Applicant Tracking System) Resume Screener that evaluates resumes against job descriptions using **TF-IDF similarity**, **skill matching**, and an interactive **Streamlit** interface.

---

## ✨ Features

- 📄 Upload Resume (PDF)
- 📋 Upload Job Description (PDF/TXT)
- 📊 ATS Compatibility Score
- ✅ Matched Skills Detection
- ❌ Missing Skills Analysis
- 📈 TF-IDF Resume Similarity Score
- 📧 Email & Phone Extraction
- 💡 Resume Improvement Suggestions
- ⚡ Interactive Streamlit Dashboard

---

## 🛠️ Tech Stack

- Python
- Streamlit
- Scikit-learn
- PyMuPDF (fitz)
- Plotly

---

## 📂 Project Structure

```text
ML-ATS-Resume-Screener/
│
├── app.py
├── ats.py
├── jd_parser.py
├── pdf_parser.py
├── suggestions.py
├── utils.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🚀 Installation

### Clone the Repository

```bash
git clone https://github.com/Garimashrigithub/ML-ATS-Resume-Screener.git
cd ML-ATS-Resume-Screener
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

**Windows**

```bash
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
streamlit run app.py
```

---

## 📖 How It Works

1. Upload your Resume (PDF).
2. Upload the Job Description (PDF or TXT).
3. Click **Analyze Resume**.
4. View:
   - ATS Score
   - Skill Match
   - Missing Skills
   - Resume Similarity
   - Improvement Suggestions

---

## 📊 ATS Scoring

The final ATS score is calculated using:

- **75% Skill Matching**
- **25% TF-IDF Cosine Similarity**

- 
## 📦 Requirements

```text
streamlit>=1.32,<2.0
PyMuPDF>=1.24,<2.0
plotly>=5.20,<6.0
scikit-learn>=1.3,<2.0
```

---

## 🔮 Future Improvements

- Multi-Resume Comparison
- Resume Ranking
- OCR Support for Scanned PDFs
- Export Analysis Report
- AI-powered Resume Suggestions
- Recruiter Dashboard

---

## 👩‍💻 Author

**Garima Shrivaspat**

B.Tech – Computer Science & Engineering.

