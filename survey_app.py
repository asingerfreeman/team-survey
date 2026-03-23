import streamlit as st
import json
import os
import uuid
import qrcode
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
from wordcloud import WordCloud
from collections import Counter
import pandas as pd
from urllib.parse import urlparse


def detect_base_url():
    try:
        parsed = urlparse(st.context.url)
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return "http://localhost:8501"

DATA_FILE = os.path.join(os.path.dirname(__file__), "survey_data.json")

st.set_page_config(page_title="Team AI Survey", layout="wide", page_icon="🤖")


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"surveys": {}, "responses": {}}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def make_qr(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a1a2e", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── routing ──────────────────────────────────────────────────────────────────
params = st.query_params
page = params.get("page", "admin")
survey_id = params.get("id", "")
data = load_data()

# ═══════════════════════════════════════════════════════════════════════════════
# SURVEY PAGE
# ═══════════════════════════════════════════════════════════════════════════════
if page == "survey":
    if survey_id not in data["surveys"]:
        st.error("Survey not found.")
        st.stop()

    survey = data["surveys"][survey_id]

    st.markdown(
        "<h1 style='text-align:center;'>🤖 " + survey["title"] + "</h1>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    if st.session_state.get("submitted"):
        st.success("### Thank you for your response! 🎉")
        st.balloons()
        st.stop()

    with st.form("survey_form", clear_on_submit=False):
        answers = {}
        for q in survey["questions"]:
            st.markdown(f"**{q['text']}**")
            if q["type"] == "multiple_choice":
                answers[q["id"]] = st.radio(
                    q["text"], q.get("options", []), label_visibility="collapsed"
                )
            else:
                answers[q["id"]] = st.text_area(
                    q["text"], placeholder="Type your answer here...", label_visibility="collapsed"
                )
            st.markdown("")

        submitted = st.form_submit_button("Submit Response ✅", use_container_width=True)

    if submitted:
        if survey_id not in data["responses"]:
            data["responses"][survey_id] = []
        data["responses"][survey_id].append(answers)
        save_data(data)
        st.session_state["submitted"] = True
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# RESULTS PAGE
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "results":
    if survey_id not in data["surveys"]:
        st.error("Survey not found.")
        st.stop()

    survey = data["surveys"][survey_id]
    responses = data["responses"].get(survey_id, [])

    st.title(f"📊 Results: {survey['title']}")
    col1, col2 = st.columns(2)
    col1.metric("Total Responses", len(responses))
    col2.metric("Questions", len(survey["questions"]))
    st.markdown("---")

    if not responses:
        st.info("No responses yet. Share the survey link to collect data.")
        st.stop()

    for q in survey["questions"]:
        st.subheader(q["text"])
        answers = [r.get(q["id"], "").strip() for r in responses if r.get(q["id"], "").strip()]

        if not answers:
            st.caption("No answers yet.")
            continue

        if q["type"] == "multiple_choice":
            counts = Counter(answers)
            df = pd.DataFrame(counts.most_common(), columns=["Option", "Count"])
            fig, ax = plt.subplots(figsize=(8, 4))
            bars = ax.barh(df["Option"], df["Count"], color="#4f8ef7")
            ax.bar_label(bars, padding=4)
            ax.set_xlabel("Responses")
            ax.spines[["top", "right"]].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        else:
            # Word cloud
            text = " ".join(answers)
            try:
                wc = WordCloud(
                    width=900, height=400, background_color="white",
                    colormap="Blues", max_words=80, collocations=False,
                ).generate(text)
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.imshow(wc, interpolation="bilinear")
                ax.axis("off")
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
            except Exception:
                pass

            with st.expander(f"View all {len(answers)} responses"):
                for i, a in enumerate(answers, 1):
                    st.markdown(f"**{i}.** {a}")

        st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN PAGE
# ═══════════════════════════════════════════════════════════════════════════════
else:
    st.title("🤖 Team Survey Builder")
    st.caption("Create surveys, generate QR codes, and view results.")

    tab_create, tab_surveys = st.tabs(["➕ Create Survey", "📋 My Surveys"])

    # ── Create Survey ──────────────────────────────────────────────────────────
    with tab_create:
        st.subheader("New Survey")

        title = st.text_input("Survey Title", placeholder="e.g. AI Tools We Should Build")

        if "draft_questions" not in st.session_state:
            st.session_state.draft_questions = []

        # Add a question
        with st.expander("➕ Add a Question", expanded=True):
            q_type = st.selectbox(
                "Question Type",
                ["open_ended", "multiple_choice"],
                format_func=lambda x: "Open-ended (free text)" if x == "open_ended" else "Multiple choice",
            )
            q_text = st.text_input("Question text", placeholder="What AI tools would you like built?")
            q_options_raw = ""
            if q_type == "multiple_choice":
                q_options_raw = st.text_input(
                    "Answer options (comma-separated)",
                    placeholder="Automation tool, Data dashboard, Chatbot, Other",
                )

            if st.button("Add Question", type="primary"):
                if not q_text.strip():
                    st.error("Please enter question text.")
                elif q_type == "multiple_choice" and not q_options_raw.strip():
                    st.error("Please enter at least one option.")
                else:
                    q = {
                        "id": str(uuid.uuid4())[:8],
                        "type": q_type,
                        "text": q_text.strip(),
                    }
                    if q_type == "multiple_choice":
                        q["options"] = [o.strip() for o in q_options_raw.split(",") if o.strip()]
                    st.session_state.draft_questions.append(q)
                    st.success("Question added!")

        # Preview questions
        if st.session_state.draft_questions:
            st.markdown("**Questions in this survey:**")
            for i, q in enumerate(st.session_state.draft_questions):
                c1, c2 = st.columns([8, 1])
                with c1:
                    badge = "📝" if q["type"] == "open_ended" else "🔘"
                    st.markdown(f"{badge} **{i+1}.** {q['text']}")
                    if q["type"] == "multiple_choice":
                        st.caption("Options: " + " · ".join(q.get("options", [])))
                with c2:
                    if st.button("🗑", key=f"del_{i}", help="Remove"):
                        st.session_state.draft_questions.pop(i)
                        st.rerun()
            st.markdown("")

        base_url = st.text_input(
            "App base URL (for QR code link)",
            value=detect_base_url(),
            help="Auto-detected from current URL. Override if needed.",
        )

        st.markdown("")
        if st.button("🚀 Create Survey & Generate QR Code", type="primary", use_container_width=True):
            if not title.strip():
                st.error("Please enter a survey title.")
            elif not st.session_state.draft_questions:
                st.error("Please add at least one question.")
            else:
                sid = str(uuid.uuid4())[:8]
                data["surveys"][sid] = {
                    "title": title.strip(),
                    "questions": st.session_state.draft_questions[:],
                }
                save_data(data)
                st.session_state.draft_questions = []

                survey_url = f"{base_url.rstrip('/')}/?page=survey&id={sid}"
                results_url = f"{base_url.rstrip('/')}/?page=results&id={sid}"

                st.success("Survey created!")
                st.markdown("---")

                col_qr, col_links = st.columns([1, 2])
                with col_qr:
                    st.image(make_qr(survey_url), caption="Scan to take the survey", width=250)
                with col_links:
                    st.markdown("**Survey link (share or project on screen):**")
                    st.code(survey_url)
                    st.markdown("**Results link:**")
                    st.code(results_url)
                    st.markdown(f"**Survey ID:** `{sid}`")

    # ── My Surveys ─────────────────────────────────────────────────────────────
    with tab_surveys:
        if not data["surveys"]:
            st.info("No surveys yet. Create one in the ➕ Create Survey tab.")
        else:
            base_url2 = st.text_input(
                "App base URL",
                value=detect_base_url(),
                key="base_url2",
            )
            st.markdown("")

            for sid, survey in reversed(list(data["surveys"].items())):
                n_responses = len(data["responses"].get(sid, []))
                with st.expander(f"**{survey['title']}** — {n_responses} response(s)"):
                    survey_url = f"{base_url2.rstrip('/')}/?page=survey&id={sid}"
                    results_url = f"{base_url2.rstrip('/')}/?page=results&id={sid}"

                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**Survey link:**")
                        st.code(survey_url, language=None)
                        st.image(make_qr(survey_url), width=180)
                    with c2:
                        st.markdown("**Results link:**")
                        st.code(results_url, language=None)
                        if st.button("View Results →", key=f"view_{sid}"):
                            st.query_params["page"] = "results"
                            st.query_params["id"] = sid
                            st.rerun()

                    st.caption(
                        f"ID: {sid} · "
                        + " · ".join(
                            f"Q{i+1}: {q['type'].replace('_',' ')}"
                            for i, q in enumerate(survey["questions"])
                        )
                    )
