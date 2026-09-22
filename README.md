# 🧠 Content Intelligence Platform

AI-powered hackathon MVP for content analysis and transformation. Paste content → get AI summaries, keywords, topics, tags → transform to FAQ, social posts, email summaries, and press releases.

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Streamlit |
| Backend API | FastAPI + Uvicorn |
| AI | Groq (`llama-3.1-8b-instant`) / OpenAI (`gpt-4o-mini`) |
| Database | SQLite (via SQLAlchemy) |

---

## Project Structure

```
Hackathon Project/
├── backend/
│   ├── __init__.py
│   ├── database.py   # SQLAlchemy engine & session
│   ├── models.py     # ORM: User, Content, GeneratedOutput, Tag
│   ├── schemas.py    # Pydantic schemas
│   ├── crud.py       # Database operations
│   ├── ai.py         # Groq/OpenAI integration
│   └── main.py       # FastAPI routes
├── frontend/
│   └── app.py        # Streamlit UI (all 6 screens)
├── .env.example      # Environment variable template
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
# Copy the template
copy .env.example .env

# Edit .env and add your Groq API key:
# GROQ_API_KEY=gsk_your_actual_key_here
```

Get a free Groq API key at: https://console.groq.com

### 3. Start the backend (Terminal 1)

```bash
uvicorn backend.main:app --reload
```

The API will be available at: http://localhost:8000  
Interactive docs: http://localhost:8000/docs

### 4. Start the frontend (Terminal 2)

```bash
streamlit run frontend/app.py
```

The app will open at: http://localhost:8501

---

## User Flow

```
Enter username (sidebar)
    ↓
📝 New Content  →  paste text + title  →  Save
    ↓
🤖 AI Processing  →  Run Analysis  →  Preview results
    ↓
✏️ Review & Edit  →  Edit fields  →  Save to DB
    ↓
🔄 Transform  →  Choose format  →  Generate  →  Edit  →  Save
    ↓
📚 Content History  →  Browse all saved content
🔍 Content Detail   →  View everything in one place
```

---

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/users` | Create or get user by name |
| GET | `/users` | List all users |
| POST | `/content` | Save new content |
| GET | `/content/user/{user_id}` | List user's content |
| GET | `/content/item/{id}` | Get content + outputs + tags |
| DELETE | `/content/{id}` | Delete content |
| POST | `/ai/analyze/{content_id}` | Run AI analysis (no auto-save) |
| POST | `/ai/transform/{content_id}` | Transform to format (no auto-save) |
| POST | `/outputs/{content_id}` | Batch-save outputs |
| PUT | `/outputs/{output_id}` | Edit a saved output |
| POST | `/tags/{content_id}` | Add tag |
| DELETE | `/tags/{tag_id}` | Delete tag |

---

## Transform Formats

| Format Key | Description |
|------------|-------------|
| `faq` | 5-7 Q&A pairs |
| `social_post` | LinkedIn/Twitter-style post with hashtags |
| `email_summary` | Subject + bullet takeaways + closing |
| `press_release` | 2-3 paragraph PR blurb |

---

## Switching to OpenAI

Edit `.env`:
```
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your_key_here
OPENAI_MODEL=gpt-4o-mini
```

---

## Database

SQLite file is created automatically at `content_intel.db` in the project root on first run. No migrations needed — tables are created on startup.

---

## MVP Screens

| Screen | Purpose |
|--------|---------|
| 📝 New Content | Input + save |
| 📚 Content History | Browse + delete |
| 🔍 Content Detail | View all data |
| 🤖 AI Processing | Trigger + preview |
| ✏️ Review & Edit | Edit + save outputs |
| 🔄 Transform | Format conversion |
