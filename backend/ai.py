"""
ai.py — AI integration for the Content Intelligence Platform.

Supports:
  - Groq  (default): llama-3.1-8b-instant via the groq SDK
  - OpenAI (fallback): gpt-4o-mini

Set AI_PROVIDER=groq or AI_PROVIDER=openai in .env.
"""

import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

AI_PROVIDER = os.getenv("AI_PROVIDER", "groq").lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _get_client():
    if AI_PROVIDER == "groq":
        from groq import Groq
        return Groq(api_key=GROQ_API_KEY), GROQ_MODEL
    else:
        from openai import OpenAI
        return OpenAI(api_key=OPENAI_API_KEY), OPENAI_MODEL


def _chat(messages: list[dict], temperature: float = 0.3) -> str:
    client, model = _get_client()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def _extract_json(text: str) -> dict:
    """Extract the first JSON object from an LLM response, tolerating markdown fences."""
    # Strip markdown code fences if present
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    # Find first {...}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No JSON object found in LLM response:\n{text}")


# ─── Core Analysis ────────────────────────────────────────────────────────────

ANALYSIS_SYSTEM = """You are a content intelligence assistant. 
Analyze the provided text and return ONLY a valid JSON object with these exact keys:
{
  "summary": "2-3 sentence summary of the content",
  "key_points": ["point 1", "point 2", "point 3"],
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "topics": ["Topic/Category 1", "Topic/Category 2"],
  "suggested_tags": ["tag1", "tag2", "tag3", "tag4"]
}
Return ONLY the JSON. No explanation, no markdown, no extra text."""


def run_ai_analysis(text: str) -> dict:
    """
    Run full AI analysis on the given text.

    Returns a dict with keys:
      summary, key_points, keywords, topics, suggested_tags
    """
    messages = [
        {"role": "system", "content": ANALYSIS_SYSTEM},
        {"role": "user", "content": f"Analyze this content:\n\n{text[:8000]}"},
    ]
    raw = _chat(messages)
    result = _extract_json(raw)

    # Normalize list fields to comma-joined strings for storage
    def to_str(val):
        if isinstance(val, list):
            return ", ".join(str(v) for v in val)
        return str(val)

    return {
        "summary": str(result.get("summary", "")),
        "key_points": to_str(result.get("key_points", [])),
        "keywords": to_str(result.get("keywords", [])),
        "topics": to_str(result.get("topics", [])),
        "suggested_tags": to_str(result.get("suggested_tags", [])),
    }


# ─── Content Transformation ───────────────────────────────────────────────────

TRANSFORM_PROMPTS = {
    "faq": (
        "You are a content writer. Convert the following content into a clear FAQ format. "
        "Generate 5-7 relevant questions and concise answers. "
        "Format as:\nQ: <question>\nA: <answer>\n\nReturn only the FAQ, no preamble."
    ),
    "social_post": (
        "You are a social media expert. Write a compelling, engaging social media post "
        "(LinkedIn/Twitter-style, max 280 characters for the hook, followed by 2-3 bullet points) "
        "based on the following content. Include 3-5 relevant hashtags at the end. "
        "Return only the post, no preamble."
    ),
    "email_summary": (
        "You are a professional writer. Convert the following content into a concise email summary "
        "with: a subject line, a 1-sentence opening, 3-5 bullet-point key takeaways, "
        "and a brief closing sentence. Format clearly with labels. Return only the email, no preamble."
    ),
    "press_release": (
        "You are a PR writer. Convert the following content into a short press release blurb "
        "(2-3 paragraphs). Include: a headline, dateline, main announcement paragraph, "
        "supporting details paragraph, and a brief boilerplate sentence. "
        "Return only the press release, no preamble."
    ),
}


def transform_content(text: str, format: str) -> str:
    """
    Transform content into a target format.

    format: faq | social_post | email_summary | press_release
    Returns the transformed text string.
    """
    system_prompt = TRANSFORM_PROMPTS.get(format)
    if not system_prompt:
        raise ValueError(f"Unknown transform format: {format!r}. "
                         f"Supported: {list(TRANSFORM_PROMPTS.keys())}")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Content to transform:\n\n{text[:8000]}"},
    ]
    return _chat(messages, temperature=0.5)

TRANSFORM_ALL_SYSTEM = """You are a content intelligence assistant.
Analyze the provided text and transform it into three formats.
Return ONLY a valid JSON object with these exact keys:
{
  "summary": "A concise overview or short summary of the source content.",
  "faq": "A list of relevant questions and answers based on the content. Format as Q: ... A: ...",
  "social_media_post": "A short, engaging version suitable for social media, including a hook and a few hashtags."
}
Return ONLY the JSON. No explanation, no markdown, no extra text."""

def run_ai_transform_all(text: str) -> dict:
    "\""
    Run full AI transformation on the given text to get summary, faq, and social media post in one shot.
    "\""
    messages = [
        {"role": "system", "content": TRANSFORM_ALL_SYSTEM},
        {"role": "user", "content": f"Content to transform:\n\n{text[:8000]}"},
    ]
    raw = _chat(messages, temperature=0.4)
    result = _extract_json(raw)

    return {
        "summary": str(result.get("summary", "")),
        "faq": str(result.get("faq", "")),
        "social_media_post": str(result.get("social_media_post", "")),
    }
