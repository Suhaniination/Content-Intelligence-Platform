"""
app.py — Streamlit frontend for the Content Intelligence Platform.

Screens:
  📝 New Content       — paste text, set title, save
  📚 Content History   — browse saved content by user
  🔍 Content Detail    — view original + all outputs + tags
  🤖 AI Processing     — trigger analysis, show live results for review
  ✏️  Review & Edit     — edit any AI-generated field, save to DB
  🔄 Transform         — pick format, generate, edit, save
"""

import streamlit as st
import httpx
import time

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Content Intelligence Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* Sidebar navigation pills */
.nav-pill {
    display: block;
    padding: 0.5rem 1rem;
    margin: 0.25rem 0;
    border-radius: 8px;
    font-weight: 500;
    cursor: pointer;
}
/* Content cards */
.content-card {
    background: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
}
.content-card h4 { margin: 0 0 0.25rem 0; color: #cdd6f4; }
.content-card small { color: #6c7086; }
/* AI output blocks */
.output-block {
    background: #181825;
    border-left: 3px solid #89b4fa;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.75rem;
    white-space: pre-wrap;
    font-family: monospace;
    font-size: 0.9rem;
}
/* Tags */
.tag-pill {
    display: inline-block;
    background: #313244;
    color: #cba6f7;
    border-radius: 999px;
    padding: 0.15rem 0.65rem;
    margin: 0.15rem;
    font-size: 0.82rem;
}
</style>
""", unsafe_allow_html=True)


# ─── Session State Defaults ───────────────────────────────────────────────────

def init_state():
    defaults = {
        "page": "📝 New Content",
        "current_user": None,       # {"id": int, "name": str}
        "selected_content_id": None,
        "pending_ai_results": None, # raw dict from /ai/analyze
        "pending_transform": None,  # {"format": str, "text": str}
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─── API Helpers ──────────────────────────────────────────────────────────────

def api(method: str, path: str, **kwargs):
    """Make an API call and return (data, error_str)."""
    try:
        r = httpx.request(method, f"{API_BASE}{path}", timeout=60, **kwargs)
        r.raise_for_status()
        return r.json(), None
    except httpx.ConnectError:
        return None, "❌ Cannot connect to backend. Is the API running? (`uvicorn backend.main:app --reload`)"
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", str(e)) if e.response.content else str(e)
        return None, f"API error {e.response.status_code}: {detail}"
    except Exception as e:
        return None, f"Unexpected error: {e}"


def get_or_create_user(name: str):
    data, err = api("POST", "/users", json={"name": name})
    return data, err


def nav_to(page: str, content_id: int = None):
    st.session_state.page = page
    if content_id is not None:
        st.session_state.selected_content_id = content_id
    st.rerun()


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🧠 Content Intelligence")
    st.divider()

    # ── User Identity ──
    st.markdown("### 👤 Your Identity")
    username_input = st.text_input(
        "Username",
        value=st.session_state.current_user["name"] if st.session_state.current_user else "",
        placeholder="Enter your name…",
        key="username_input",
    )
    if st.button("Set User", use_container_width=True):
        name = username_input.strip()
        if name:
            user, err = get_or_create_user(name)
            if err:
                st.error(err)
            else:
                st.session_state.current_user = user
                st.success(f"Welcome, {user['name']}!")
        else:
            st.warning("Please enter a name.")

    if st.session_state.current_user:
        st.caption(f"✅ Logged in as **{st.session_state.current_user['name']}**")

    st.divider()

    # ── Navigation ──
    st.markdown("### 🗺️ Navigation")
    pages = [
        "📝 New Content",
        "📚 Content History",
        "🔍 Content Detail",
        "🤖 AI Processing",
        "✏️ Review & Edit",
        "🔄 Transform",
    ]
    for p in pages:
        is_active = st.session_state.page == p
        if st.button(p, use_container_width=True, type="primary" if is_active else "secondary", key=f"nav_{p}"):
            st.session_state.page = p
            st.rerun()

    st.divider()
    st.caption("Powered by Groq · FastAPI · Streamlit")


# ─── Require user helper ──────────────────────────────────────────────────────

def require_user():
    if not st.session_state.current_user:
        st.warning("⚠️ Please set your username in the sidebar first.")
        return False
    return True


def require_content():
    if not st.session_state.selected_content_id:
        st.info("ℹ️ No content selected. Go to **📚 Content History** and select an item.")
        return False
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: 📝 New Content
# ═══════════════════════════════════════════════════════════════════════════════

if st.session_state.page == "📝 New Content":
    st.title("📝 New Content")
    st.caption("Paste or type content to save it for AI processing.")

    if not require_user():
        st.stop()

    with st.form("new_content_form", clear_on_submit=True):
        title = st.text_input("Title / Label", placeholder="e.g. Q3 Earnings Report, Blog Post Draft…")
        original_text = st.text_area(
            "Content",
            height=350,
            placeholder="Paste your article, report, announcement, or any text here…",
        )
        submitted = st.form_submit_button("💾 Save Content", use_container_width=True, type="primary")

    if submitted:
        if not original_text.strip():
            st.error("Content cannot be empty.")
        else:
            payload = {
                "user_id": st.session_state.current_user["id"],
                "title": title.strip() or "Untitled",
                "original_text": original_text.strip(),
            }
            data, err = api("POST", "/content", json=payload)
            if err:
                st.error(err)
            else:
                st.success(f"✅ Content saved! (ID: {data['id']})")
                st.session_state.selected_content_id = data["id"]
                time.sleep(0.8)
                nav_to("🤖 AI Processing")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: 📚 Content History
# ═══════════════════════════════════════════════════════════════════════════════

elif st.session_state.page == "📚 Content History":
    st.title("📚 Content History")

    if not require_user():
        st.stop()

    user_id = st.session_state.current_user["id"]
    items, err = api("GET", f"/content/user/{user_id}")

    if err:
        st.error(err)
        st.stop()

    if not items:
        st.info("No content saved yet. Go to **📝 New Content** to add some!")
        st.stop()

    st.caption(f"{len(items)} item(s) found for **{st.session_state.current_user['name']}**")
    st.divider()

    for item in items:
        col1, col2, col3 = st.columns([5, 1, 1])
        with col1:
            st.markdown(
                f"""<div class="content-card">
                  <h4>{'📄 ' + item['title']}</h4>
                  <small>🕐 {item['created_at'][:19].replace('T', ' ')} &nbsp;|&nbsp; ID: {item['id']}</small>
                </div>""",
                unsafe_allow_html=True,
            )
        with col2:
            if st.button("👁 View", key=f"view_{item['id']}", use_container_width=True):
                nav_to("🔍 Content Detail", item["id"])
        with col3:
            if st.button("🗑 Delete", key=f"del_{item['id']}", use_container_width=True):
                _, err = api("DELETE", f"/content/{item['id']}")
                if err:
                    st.error(err)
                else:
                    st.success("Deleted.")
                    time.sleep(0.5)
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: 🔍 Content Detail
# ═══════════════════════════════════════════════════════════════════════════════

elif st.session_state.page == "🔍 Content Detail":
    st.title("🔍 Content Detail")

    if not require_content():
        st.stop()

    content_id = st.session_state.selected_content_id
    data, err = api("GET", f"/content/item/{content_id}")
    if err:
        st.error(err)
        st.stop()

    # Header
    st.subheader(data["title"])
    st.caption(f"🕐 {data['created_at'][:19].replace('T', ' ')}  |  ID: {data['id']}")

    # Action row
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🤖 Run AI Analysis", use_container_width=True, type="primary"):
            nav_to("🤖 AI Processing", content_id)
    with c2:
        if st.button("🔄 Transform Content", use_container_width=True):
            nav_to("🔄 Transform", content_id)
    with c3:
        if st.button("✏️ Edit Outputs", use_container_width=True):
            nav_to("✏️ Review & Edit", content_id)

    st.divider()

    # Original Text
    with st.expander("📄 Original Text", expanded=True):
        st.markdown(
            f'<div class="output-block">{data["original_text"]}</div>',
            unsafe_allow_html=True,
        )

    # Generated Outputs
    if data["outputs"]:
        st.subheader("🤖 Generated Outputs")

        LABEL_MAP = {
            "summary": "📋 Summary",
            "key_points": "🔑 Key Points",
            "keywords": "🏷️ Keywords",
            "topics": "📂 Topics/Categories",
            "suggested_tags": "💡 Suggested Tags",
            "faq": "❓ FAQ",
            "social_post": "📱 Social Media Post",
            "email_summary": "📧 Email Summary",
            "press_release": "📰 Press Release",
        }

        for output in data["outputs"]:
            label = LABEL_MAP.get(output["output_type"], output["output_type"].replace("_", " ").title())
            with st.expander(label, expanded=False):
                st.markdown(
                    f'<div class="output-block">{output["text"]}</div>',
                    unsafe_allow_html=True,
                )
                st.caption(f"Saved: {output['created_at'][:19].replace('T', ' ')}  |  Output ID: {output['id']}")
    else:
        st.info("No AI outputs generated yet. Click **🤖 Run AI Analysis** to get started.")

    # Tags
    st.subheader("🏷️ Tags")
    tags = data.get("tags", [])
    if tags:
        tags_html = " ".join(f'<span class="tag-pill">{t["label"]}</span>' for t in tags)
        st.markdown(tags_html, unsafe_allow_html=True)
    else:
        st.caption("No tags yet.")

    # Add tag inline
    with st.form("add_tag_form"):
        new_tag = st.text_input("Add a tag", placeholder="e.g. finance, Q3, report")
        if st.form_submit_button("➕ Add Tag"):
            if new_tag.strip():
                _, err = api("POST", f"/tags/{content_id}", json={"label": new_tag.strip()})
                if err:
                    st.error(err)
                else:
                    st.success(f"Tag '{new_tag.strip()}' added!")
                    st.rerun()

    # Delete tags
    if tags:
        st.caption("Remove a tag:")
        cols = st.columns(min(len(tags), 6))
        for i, tag in enumerate(tags):
            with cols[i % 6]:
                if st.button(f"✕ {tag['label']}", key=f"deltag_{tag['id']}"):
                    _, err = api("DELETE", f"/tags/{tag['id']}")
                    if err:
                        st.error(err)
                    else:
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: 🤖 AI Processing
# ═══════════════════════════════════════════════════════════════════════════════

elif st.session_state.page == "🤖 AI Processing":
    st.title("🤖 AI Processing")

    if not require_content():
        st.stop()

    content_id = st.session_state.selected_content_id

    # Load content preview
    data, err = api("GET", f"/content/item/{content_id}")
    if err:
        st.error(err)
        st.stop()

    st.subheader(data["title"])
    with st.expander("📄 Source Content Preview", expanded=False):
        preview = data["original_text"][:500] + ("…" if len(data["original_text"]) > 500 else "")
        st.text(preview)

    st.divider()

    # Show pending results if already fetched
    if st.session_state.pending_ai_results:
        results = st.session_state.pending_ai_results
        st.success("✅ AI analysis complete! Review the results below.")
        st.caption("These results have **not been saved** yet. Proceed to **✏️ Review & Edit** to save.")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📋 Summary**")
            st.info(results.get("summary", ""))

            st.markdown("**🏷️ Keywords**")
            st.info(results.get("keywords", ""))

            st.markdown("**💡 Suggested Tags**")
            st.info(results.get("suggested_tags", ""))

        with col2:
            st.markdown("**🔑 Key Points**")
            st.info(results.get("key_points", ""))

            st.markdown("**📂 Topics/Categories**")
            st.info(results.get("topics", ""))

        st.divider()
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("✏️ Review & Edit → Save", use_container_width=True, type="primary"):
                nav_to("✏️ Review & Edit", content_id)
        with col_b:
            if st.button("🔁 Re-run Analysis", use_container_width=True):
                st.session_state.pending_ai_results = None
                st.rerun()
        with col_c:
            if st.button("🔄 Transform Content", use_container_width=True):
                nav_to("🔄 Transform", content_id)

    else:
        st.markdown(
            """
            Click the button below to send the content to the AI for analysis.
            The model will generate:
            - 📋 **Summary** — concise 2-3 sentence overview
            - 🔑 **Key Points** — main bullet takeaways
            - 🏷️ **Keywords** — important terms
            - 📂 **Topics/Categories** — content classification
            - 💡 **Suggested Tags** — labeling suggestions
            
            *Results are shown for review — nothing is saved automatically.*
            """
        )

        if st.button("🚀 Run AI Analysis", use_container_width=True, type="primary"):
            with st.spinner("⚡ Calling Groq AI… this usually takes 2-5 seconds…"):
                results, err = api("POST", f"/ai/analyze/{content_id}")
            if err:
                st.error(err)
            else:
                st.session_state.pending_ai_results = results
                st.success("Analysis complete!")
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ✏️ Review & Edit
# ═══════════════════════════════════════════════════════════════════════════════

elif st.session_state.page == "✏️ Review & Edit":
    st.title("✏️ Review & Edit")

    if not require_content():
        st.stop()

    content_id = st.session_state.selected_content_id
    pending = st.session_state.pending_ai_results

    # Load existing outputs from DB
    data, err = api("GET", f"/content/item/{content_id}")
    if err:
        st.error(err)
        st.stop()

    existing_outputs = {o["output_type"]: o for o in data.get("outputs", [])}

    st.subheader(data["title"])
    st.caption("Edit any field below, then click **Save All** to persist to the database.")

    if not pending and not existing_outputs:
        st.info("No AI results yet. Go to **🤖 AI Processing** first to generate results.")
        if st.button("🤖 Go to AI Processing"):
            nav_to("🤖 AI Processing", content_id)
        st.stop()

    # Merge pending results with existing (pending takes priority)
    FIELD_LABELS = {
        "summary": "📋 Summary",
        "key_points": "🔑 Key Points",
        "keywords": "🏷️ Keywords",
        "topics": "📂 Topics / Categories",
        "suggested_tags": "💡 Suggested Tags",
    }

    edited_values = {}
    with st.form("edit_outputs_form"):
        for field, label in FIELD_LABELS.items():
            # Prefer unsaved pending result; fall back to DB value
            default_val = ""
            if pending and field in pending:
                default_val = pending[field]
            elif field in existing_outputs:
                default_val = existing_outputs[field]["text"]

            height = 200 if field in ("summary", "key_points") else 80
            edited_values[field] = st.text_area(label, value=default_val, height=height, key=f"edit_{field}")

        submitted = st.form_submit_button("💾 Save All to Database", use_container_width=True, type="primary")

    if submitted:
        outputs_payload = [
            {"output_type": field, "text": text.strip()}
            for field, text in edited_values.items()
            if text.strip()
        ]
        saved, err = api("POST", f"/outputs/{content_id}", json={"outputs": outputs_payload})
        if err:
            st.error(err)
        else:
            st.session_state.pending_ai_results = None
            st.success(f"✅ Saved {len(saved)} outputs to the database!")
            time.sleep(0.8)
            nav_to("🔍 Content Detail", content_id)

    # Edit individual existing outputs by ID (for already-saved items)
    if existing_outputs:
        st.divider()
        st.subheader("🔧 Edit Individual Saved Outputs")
        st.caption("Use these to make targeted edits to already-saved outputs.")

        for field, output in existing_outputs.items():
            label = FIELD_LABELS.get(field, field.replace("_", " ").title())
            with st.expander(f"Edit: {label} (ID: {output['id']})", expanded=False):
                new_text = st.text_area("", value=output["text"], height=120, key=f"ind_edit_{output['id']}")
                if st.button("💾 Save", key=f"save_ind_{output['id']}"):
                    updated, err = api("PUT", f"/outputs/{output['id']}", json={"text": new_text})
                    if err:
                        st.error(err)
                    else:
                        st.success("Saved!")
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: 🔄 Transform
# ═══════════════════════════════════════════════════════════════════════════════

elif st.session_state.page == "🔄 Transform":
    st.title("🔄 Transform Content")
    st.caption("Repurpose your content into different formats using AI.")

    if not require_content():
        st.stop()

    content_id = st.session_state.selected_content_id
    data, err = api("GET", f"/content/item/{content_id}")
    if err:
        st.error(err)
        st.stop()

    st.subheader(data["title"])

    FORMATS = {
        "faq": "❓ FAQ — Questions & Answers",
        "social_post": "📱 Social Media Post",
        "email_summary": "📧 Email Summary",
        "press_release": "📰 Press Release Blurb",
    }

    selected_format = st.selectbox(
        "Choose a target format",
        options=list(FORMATS.keys()),
        format_func=lambda k: FORMATS[k],
    )

    # Check if this format is already saved
    existing_outputs = {o["output_type"]: o for o in data.get("outputs", [])}
    if selected_format in existing_outputs:
        st.info(f"ℹ️ A **{FORMATS[selected_format]}** output already exists for this content. Generating again will replace it.")

    if st.button(f"⚡ Generate {FORMATS[selected_format]}", use_container_width=True, type="primary"):
        with st.spinner(f"⚡ Generating {FORMATS[selected_format]}… please wait…"):
            result, err = api("POST", f"/ai/transform/{content_id}", json={"format": selected_format})
        if err:
            st.error(err)
        else:
            st.session_state.pending_transform = result
            st.rerun()

    # Review & save transform result
    if st.session_state.pending_transform and st.session_state.pending_transform.get("format") == selected_format:
        pending_t = st.session_state.pending_transform
        st.success(f"✅ {FORMATS[selected_format]} generated! Review and edit below before saving.")
        st.divider()

        with st.form("save_transform_form"):
            edited_transform = st.text_area(
                f"✏️ Edit {FORMATS[selected_format]}",
                value=pending_t["text"],
                height=400,
            )
            save_btn = st.form_submit_button("💾 Save to Database", use_container_width=True, type="primary")

        if save_btn:
            saved, err = api(
                "POST",
                f"/outputs/{content_id}",
                json={"outputs": [{"output_type": selected_format, "text": edited_transform.strip()}]},
            )
            if err:
                st.error(err)
            else:
                st.session_state.pending_transform = None
                st.success(f"✅ {FORMATS[selected_format]} saved!")
                time.sleep(0.8)
                nav_to("🔍 Content Detail", content_id)

    # Show previously saved transforms for this content
    saved_transforms = {k: v for k, v in existing_outputs.items() if k in FORMATS}
    if saved_transforms:
        st.divider()
        st.subheader("📁 Previously Saved Transforms")
        for fmt_key, output in saved_transforms.items():
            with st.expander(FORMATS[fmt_key], expanded=False):
                st.text(output["text"])
                st.caption(f"Saved: {output['created_at'][:19].replace('T', ' ')}")
