# Content Intelligence Platform

A lightweight, AI-assisted web application that accelerates content marketing workflows. This platform allows teams to paste long-form content (articles, reports, announcements) and instantly extract insights (summaries, keywords, topics) or repurpose the text into alternate formats (FAQs, social media posts, emails, press releases) using Generative AI.

**[Read the Full Project Report PDF included in this repository](Project_Report_Content_Intelligence.pdf)**

## 🚀 Features

- **Instant AI Analysis:** Generate summaries, key points, topics, keywords, and suggested tags in a single pass.
- **Content Transformation:** Repurpose source text into Social Media Posts, FAQs, Email Summaries, and Press Releases.
- **Human-in-the-Loop (HITL):** AI outputs are generated as previews. Users must review and edit the text before saving to the database.
- **Non-Destructive Processing:** The original source text is kept immutable and separate from generated derivative content.
- **Fast & Lightweight:** Built using Streamlit, FastAPI, and SQLite.

## 🛠️ Tech Stack

- **Frontend:** Streamlit (Python)
- **Backend:** FastAPI (Python)
- **Database:** SQLite & SQLAlchemy (ORM)
- **AI Integration:** Groq API (`qwen/qwen3.8-27b`) for ultra-low latency inference

## 💻 How to Run Locally

### 1. Setup Environment
Ensure you have Python 3.12+ installed.
```bash
# Clone the repository
git clone https://github.com/Suhaniination/Content-Intelligence-Platform.git
cd Content-Intelligence-Platform

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys
Create a `.env` file in the root directory and add your Groq API key:
```env
AI_PROVIDER=groq
GROQ_API_KEY=gsk_your_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b
```

### 3. Start the Backend
Open a terminal and start the FastAPI server:
```bash
uvicorn backend.main:app --reload
```
The API will run at `http://localhost:8000` (Docs available at `http://localhost:8000/docs`).

### 4. Start the Frontend
Open a second terminal and start the Streamlit UI:
```bash
streamlit run frontend/app.py
```
The web app will open automatically at `http://localhost:8501`.

## 📁 Repository Structure

```
├── backend/
│   ├── ai.py         # LLM prompting and API integration
│   ├── crud.py       # Database operations
│   ├── database.py   # SQLite connection
│   ├── main.py       # FastAPI routing
│   ├── models.py     # SQLAlchemy models
│   └── schemas.py    # Pydantic validation schemas
├── frontend/
│   └── app.py        # Streamlit multi-page interface
├── Project_Report_Content_Intelligence.pdf # Detailed Architecture & Approach
├── requirements.txt  # Python dependencies
└── README.md         
```
