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

# ── Bain Capital brand colors ─────────────────────────────────────────────────
BC_RED    = "#CC0000"
BC_DARK   = "#1C1C1C"
BC_LIGHT  = "#F5F5F5"
BC_GRAY   = "#6B6B6B"
BC_BORDER = "#E0E0E0"

DATA_FILE = os.path.join(os.path.dirname(__file__), "survey_data.json")

st.set_page_config(page_title="Bain Capital | AI Survey", layout="wide", page_icon="🔴")


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"surveys": {}, "responses": {}}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def detect_base_url():
    try:
        parsed = urlparse(st.context.url)
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return "http://localhost:8501"


def make_qr(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=BC_DARK, back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def inject_css():
    st.markdown(f"""
    <style>
      /* ── Global ── */
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

      html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
      }}

      /* Hide Streamlit default chrome */
      #MainMenu, footer, header {{ visibility: hidden; }}

      /* Main background */
      .stApp {{
        background-color: {BC_LIGHT};
      }}

      /* ── Top banner ── */
      .bc-banner {{
        background-color: {BC_DARK};
        padding: 18px 40px;
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 32px;
        border-bottom: 3px solid {BC_RED};
      }}
      .bc-banner-logo {{
        color: {BC_RED};
        font-size: 28px;
        font-weight: 700;
        letter-spacing: -0.5px;
      }}
      .bc-banner-divider {{
        width: 1px;
        height: 28px;
        background: #444;
      }}
      .bc-banner-title {{
        color: white;
        font-size: 15px;
        font-weight: 400;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        opacity: 0.85;
      }}

      /* ── Cards ── */
      .bc-card {{
        background: white;
        border-radius: 4px;
        border: 1px solid {BC_BORDER};
        padding: 28px 32px;
        margin-bottom: 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
      }}

      /* ── Section headers ── */
      .bc-section-title {{
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: {BC_RED};
        margin-bottom: 6px;
      }}
      .bc-page-title {{
        font-size: 26px;
        font-weight: 700;
        color: {BC_DARK};
        margin-bottom: 4px;
        line-height: 1.2;
      }}
      .bc-subtitle {{
        font-size: 14px;
        color: {BC_GRAY};
        margin-bottom: 24px;
      }}

      /* ── Thank-you screen ── */
      .bc-thankyou {{
        text-align: center;
        padding: 60px 20px;
      }}
      .bc-thankyou-icon {{
        font-size: 56px;
        margin-bottom: 16px;
      }}
      .bc-thankyou-title {{
        font-size: 28px;
        font-weight: 700;
        color: {BC_DARK};
        margin-bottom: 8px;
      }}
      .bc-thankyou-sub {{
        font-size: 15px;
        color: {BC_GRAY};
      }}

      /* ── Metric boxes ── */
      .bc-metric {{
        background: white;
        border: 1px solid {BC_BORDER};
        border-top: 3px solid {BC_RED};
        border-radius: 4px;
        padding: 20px 24px;
        text-align: center;
      }}
      .bc-metric-value {{
        font-size: 36px;
        font-weight: 700;
        color: {BC_DARK};
        line-height: 1;
      }}
      .bc-metric-label {{
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: {BC_GRAY};
        margin-top: 6px;
      }}

      /* ── Question card ── */
      .bc-question {{
        background: white;
        border-left: 3px solid {BC_RED};
        border-radius: 0 4px 4px 0;
        padding: 20px 24px;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
      }}
      .bc-question-text {{
        font-size: 16px;
        font-weight: 600;
        color: {BC_DARK};
        margin-bottom: 16px;
      }}
      .bc-question-type {{
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: {BC_GRAY};
        margin-bottom: 10px;
      }}

      /* ── Buttons ── */
      .stButton > button {{
        background-color: white !important;
        color: {BC_DARK} !important;
        border: 1px solid {BC_BORDER} !important;
        border-radius: 2px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        letter-spacing: 0.3px !important;
        padding: 8px 20px !important;
        transition: all 0.15s ease !important;
      }}
      .stButton > button:hover {{
        border-color: {BC_RED} !important;
        color: {BC_RED} !important;
      }}
      .stButton > button[kind="primary"] {{
        background-color: {BC_RED} !important;
        color: white !important;
        border-color: {BC_RED} !important;
      }}
      .stButton > button[kind="primary"]:hover {{
        background-color: #aa0000 !important;
        color: white !important;
      }}

      /* ── Download button ── */
      .stDownloadButton > button {{
        background-color: {BC_DARK} !important;
        color: white !important;
        border: none !important;
        border-radius: 2px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        letter-spacing: 0.3px !important;
      }}
      .stDownloadButton > button:hover {{
        background-color: #333 !important;
      }}

      /* ── Form submit ── */
      .stFormSubmitButton > button {{
        background-color: {BC_RED} !important;
        color: white !important;
        border: none !important;
        border-radius: 2px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        letter-spacing: 0.5px !important;
        padding: 12px !important;
      }}
      .stFormSubmitButton > button:hover {{
        background-color: #aa0000 !important;
      }}

      /* ── Tabs ── */
      .stTabs [data-baseweb="tab-list"] {{
        gap: 0;
        border-bottom: 2px solid {BC_BORDER};
        background: transparent;
      }}
      .stTabs [data-baseweb="tab"] {{
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        color: {BC_GRAY};
        font-size: 13px;
        font-weight: 500;
        letter-spacing: 0.5px;
        padding: 10px 24px;
        margin-bottom: -2px;
      }}
      .stTabs [aria-selected="true"] {{
        color: {BC_RED} !important;
        border-bottom-color: {BC_RED} !important;
        background: transparent !important;
      }}

      /* ── Inputs ── */
      .stTextInput > div > div > input,
      .stTextArea > div > div > textarea,
      .stSelectbox > div > div {{
        border-radius: 2px !important;
        border-color: {BC_BORDER} !important;
        font-size: 14px !important;
      }}
      .stTextInput > div > div > input:focus,
      .stTextArea > div > div > textarea:focus {{
        border-color: {BC_RED} !important;
        box-shadow: 0 0 0 1px {BC_RED}33 !important;
      }}

      /* ── Radio buttons ── */
      .stRadio > div {{
        gap: 8px;
      }}
      .stRadio label {{
        font-size: 14px !important;
        color: {BC_DARK} !important;
      }}

      /* ── Expander ── */
      .streamlit-expanderHeader {{
        font-size: 13px !important;
        font-weight: 500 !important;
        color: {BC_DARK} !important;
        background: white !important;
        border: 1px solid {BC_BORDER} !important;
        border-radius: 2px !important;
      }}

      /* ── Code blocks (URLs) ── */
      .stCode {{
        background: {BC_LIGHT} !important;
        border: 1px solid {BC_BORDER} !important;
        border-radius: 2px !important;
        font-size: 12px !important;
      }}

      /* ── Divider ── */
      hr {{
        border-color: {BC_BORDER} !important;
        margin: 24px 0 !important;
      }}

      /* ── Success/error alerts ── */
      .stAlert {{
        border-radius: 2px !important;
        font-size: 14px !important;
      }}

      /* ── Sidebar (unused but clean it up) ── */
      section[data-testid="stSidebar"] {{
        display: none;
      }}
    </style>
    """, unsafe_allow_html=True)


def banner(subtitle=""):
    st.markdown(f"""
    <div class="bc-banner">
      <div class="bc-banner-logo">BAIN CAPITAL</div>
      <div class="bc-banner-divider"></div>
      <div class="bc-banner-title">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def metric_card(value, label):
    return f"""
    <div class="bc-metric">
      <div class="bc-metric-value">{value}</div>
      <div class="bc-metric-label">{label}</div>
    </div>
    """


# ── routing ───────────────────────────────────────────────────────────────────
inject_css()
params   = st.query_params
page     = params.get("page", "admin")
survey_id = params.get("id", "")
data     = load_data()

# ═══════════════════════════════════════════════════════════════════════════════
# SURVEY PAGE
# ═══════════════════════════════════════════════════════════════════════════════
if page == "survey":
    if survey_id not in data["surveys"]:
        st.error("Survey not found.")
        st.stop()

    survey = data["surveys"][survey_id]
    banner("AI Tools Survey")

    if st.session_state.get("submitted"):
        st.markdown("""
        <div class="bc-thankyou">
          <div class="bc-thankyou-icon">✓</div>
          <div class="bc-thankyou-title">Response Submitted</div>
          <div class="bc-thankyou-sub">Thank you for sharing your feedback.</div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    col_center = st.columns([1, 3, 1])[1]
    with col_center:
        st.markdown(f"""
        <div class="bc-section-title">Team Survey</div>
        <div class="bc-page-title">{survey["title"]}</div>
        <div class="bc-subtitle">Your responses are anonymous. Please answer all questions.</div>
        """, unsafe_allow_html=True)

        with st.form("survey_form", clear_on_submit=False):
            answers = {}
            for i, q in enumerate(survey["questions"]):
                type_label = "Open Response" if q["type"] == "open_ended" else "Select One"
                st.markdown(f"""
                <div class="bc-question">
                  <div class="bc-question-type">{type_label}</div>
                  <div class="bc-question-text">{i+1}. {q["text"]}</div>
                </div>
                """, unsafe_allow_html=True)

                if q["type"] == "multiple_choice":
                    answers[q["id"]] = st.radio(
                        q["text"], q.get("options", []), label_visibility="collapsed"
                    )
                else:
                    answers[q["id"]] = st.text_area(
                        q["text"], placeholder="Type your answer here...",
                        label_visibility="collapsed", height=100
                    )

            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Submit Response", use_container_width=True)

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
    banner("Survey Results")

    st.markdown(f"""
    <div class="bc-section-title">Results Dashboard</div>
    <div class="bc-page-title">{survey["title"]}</div>
    """, unsafe_allow_html=True)

    # Metrics + download row
    m1, m2, m3 = st.columns([1, 1, 2])
    m1.markdown(metric_card(len(responses), "Total Responses"), unsafe_allow_html=True)
    m2.markdown(metric_card(len(survey["questions"]), "Questions"), unsafe_allow_html=True)

    if responses:
        question_labels = {q["id"]: q["text"] for q in survey["questions"]}
        csv_rows = [{question_labels.get(qid, qid): ans for qid, ans in r.items()} for r in responses]
        csv_df = pd.DataFrame(csv_rows)
        with m3:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            st.download_button(
                label="⬇  Download Responses (CSV)",
                data=csv_df.to_csv(index=False).encode("utf-8"),
                file_name=f"{survey['title'].replace(' ', '_')}_responses.csv",
                mime="text/csv",
                use_container_width=False,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    if not responses:
        st.info("No responses yet.")
        st.stop()

    for q in survey["questions"]:
        answers = [r.get(q["id"], "").strip() for r in responses if r.get(q["id"], "").strip()]
        type_label = "Open Response" if q["type"] == "open_ended" else "Multiple Choice"

        st.markdown(f"""
        <div class="bc-question">
          <div class="bc-question-type">{type_label}</div>
          <div class="bc-question-text">{q["text"]}</div>
        </div>
        """, unsafe_allow_html=True)

        if not answers:
            st.caption("No answers yet.")
            st.markdown("<br>", unsafe_allow_html=True)
            continue

        if q["type"] == "multiple_choice":
            counts = Counter(answers)
            df = pd.DataFrame(counts.most_common(), columns=["Option", "Count"])

            fig, ax = plt.subplots(figsize=(8, max(2.5, len(df) * 0.6)))
            fig.patch.set_facecolor("white")
            ax.set_facecolor("white")
            bars = ax.barh(df["Option"], df["Count"], color=BC_RED, height=0.5)
            ax.bar_label(bars, padding=6, color=BC_DARK, fontsize=11, fontweight="600")
            ax.set_xlabel("Responses", fontsize=10, color=BC_GRAY)
            ax.tick_params(colors=BC_DARK, labelsize=11)
            ax.spines[["top", "right", "bottom"]].set_visible(False)
            ax.spines["left"].set_color(BC_BORDER)
            ax.set_xlim(0, df["Count"].max() * 1.2)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        else:
            text = " ".join(answers)
            try:
                wc = WordCloud(
                    width=1000, height=380,
                    background_color="white",
                    color_func=lambda *args, **kwargs: BC_RED
                    if __import__("random").random() > 0.5 else BC_DARK,
                    max_words=80,
                    collocations=False,
                    prefer_horizontal=0.85,
                ).generate(text)
                fig, ax = plt.subplots(figsize=(11, 4))
                fig.patch.set_facecolor("white")
                ax.imshow(wc, interpolation="bilinear")
                ax.axis("off")
                plt.tight_layout(pad=0)
                st.pyplot(fig)
                plt.close()
            except Exception:
                pass

            with st.expander(f"View all {len(answers)} written responses"):
                for i, a in enumerate(answers, 1):
                    st.markdown(
                        f"<div style='padding:10px 0; border-bottom:1px solid {BC_BORDER}; "
                        f"font-size:14px; color:{BC_DARK}'>"
                        f"<span style='color:{BC_RED}; font-weight:600; margin-right:10px'>{i}.</span>{a}</div>",
                        unsafe_allow_html=True,
                    )

        st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN PAGE
# ═══════════════════════════════════════════════════════════════════════════════
else:
    banner("Admin — Survey Builder")

    st.markdown("""
    <div class="bc-section-title">Survey Management</div>
    <div class="bc-page-title">AI Tools Survey Builder</div>
    <div class="bc-subtitle">Create surveys, generate QR codes, and view team responses.</div>
    """, unsafe_allow_html=True)

    tab_create, tab_surveys = st.tabs(["  Create Survey  ", "  My Surveys  "])

    # ── Create Survey ──────────────────────────────────────────────────────────
    with tab_create:
        st.markdown("<br>", unsafe_allow_html=True)
        col_form, col_preview = st.columns([3, 2])

        with col_form:
            st.markdown('<div class="bc-card">', unsafe_allow_html=True)
            st.markdown("**Survey Title**")
            title = st.text_input(
                "title", label_visibility="collapsed",
                placeholder="e.g. AI Tools We Should Build"
            )

            st.markdown("<br>**Add a Question**", unsafe_allow_html=True)
            q_type = st.selectbox(
                "Question Type",
                ["open_ended", "multiple_choice"],
                format_func=lambda x: "Open-ended (free text)" if x == "open_ended" else "Multiple choice",
            )
            q_text = st.text_input(
                "Question text", label_visibility="collapsed",
                placeholder="e.g. What AI tools would you like built?"
            )
            q_options_raw = ""
            if q_type == "multiple_choice":
                q_options_raw = st.text_input(
                    "Options", label_visibility="collapsed",
                    placeholder="Automation tool, Data dashboard, Chatbot, Other",
                )

            if st.button("+ Add Question", type="primary"):
                if "draft_questions" not in st.session_state:
                    st.session_state.draft_questions = []
                if not q_text.strip():
                    st.error("Please enter question text.")
                elif q_type == "multiple_choice" and not q_options_raw.strip():
                    st.error("Please enter at least one option.")
                else:
                    q = {"id": str(uuid.uuid4())[:8], "type": q_type, "text": q_text.strip()}
                    if q_type == "multiple_choice":
                        q["options"] = [o.strip() for o in q_options_raw.split(",") if o.strip()]
                    st.session_state.setdefault("draft_questions", []).append(q)
                    st.success("Question added.")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_preview:
            if "draft_questions" not in st.session_state:
                st.session_state.draft_questions = []

            st.markdown(f"""
            <div style="background:white; border:1px solid {BC_BORDER}; border-radius:4px;
                        padding:20px 24px; min-height:200px;">
              <div style="font-size:11px; font-weight:600; letter-spacing:2px;
                          text-transform:uppercase; color:{BC_RED}; margin-bottom:12px;">
                Survey Preview
              </div>
            """, unsafe_allow_html=True)

            if not st.session_state.draft_questions:
                st.markdown(f"<div style='color:{BC_GRAY}; font-size:13px;'>No questions yet.</div>",
                            unsafe_allow_html=True)
            else:
                for i, q in enumerate(st.session_state.draft_questions):
                    badge = "Open" if q["type"] == "open_ended" else "MC"
                    badge_color = BC_GRAY if q["type"] == "open_ended" else BC_RED
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;
                                padding:10px 0; border-bottom:1px solid {BC_BORDER};">
                      <div>
                        <span style="font-size:10px; font-weight:600; color:{badge_color};
                                     background:{badge_color}18; padding:2px 7px; border-radius:2px;
                                     margin-right:8px;">{badge}</span>
                        <span style="font-size:13px; color:{BC_DARK}; font-weight:500;">{q["text"]}</span>
                        {"<div style='font-size:11px; color:" + BC_GRAY + "; margin-top:4px; margin-left:40px;'>" + " · ".join(q.get("options",[])) + "</div>" if q["type"] == "multiple_choice" else ""}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                    c1, c2 = st.columns([8, 1])
                    with c2:
                        if st.button("✕", key=f"del_{i}", help="Remove"):
                            st.session_state.draft_questions.pop(i)
                            st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        base_url = st.text_input(
            "App URL (for QR code)",
            value=detect_base_url(),
            help="Auto-detected. Override if needed.",
        )

        if st.button("Generate Survey & QR Code", type="primary", use_container_width=True):
            if not title.strip():
                st.error("Please enter a survey title.")
            elif not st.session_state.get("draft_questions"):
                st.error("Please add at least one question.")
            else:
                sid = str(uuid.uuid4())[:8]
                data["surveys"][sid] = {
                    "title": title.strip(),
                    "questions": st.session_state.draft_questions[:],
                }
                save_data(data)
                st.session_state.draft_questions = []

                survey_url  = f"{base_url.rstrip('/')}/?page=survey&id={sid}"
                results_url = f"{base_url.rstrip('/')}/?page=results&id={sid}"

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style="background:{BC_DARK}; border-radius:4px; padding:24px 32px;
                             display:flex; gap:40px; align-items:flex-start;">
                  <div style="flex:1;">
                    <div style="font-size:10px; font-weight:600; letter-spacing:2px;
                                text-transform:uppercase; color:{BC_RED}; margin-bottom:6px;">
                      Survey Created
                    </div>
                    <div style="font-size:18px; font-weight:700; color:white; margin-bottom:20px;">
                      {title.strip()}
                    </div>
                    <div style="font-size:11px; color:#aaa; margin-bottom:4px; letter-spacing:1px; text-transform:uppercase;">
                      Survey Link
                    </div>
                    <div style="font-size:12px; color:white; background:#2c2c2c; padding:8px 12px;
                                border-radius:2px; font-family:monospace; margin-bottom:16px; word-break:break-all;">
                      {survey_url}
                    </div>
                    <div style="font-size:11px; color:#aaa; margin-bottom:4px; letter-spacing:1px; text-transform:uppercase;">
                      Results Link
                    </div>
                    <div style="font-size:12px; color:white; background:#2c2c2c; padding:8px 12px;
                                border-radius:2px; font-family:monospace; word-break:break-all;">
                      {results_url}
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                qr_col = st.columns([1, 1, 1])[1]
                with qr_col:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.image(make_qr(survey_url), caption="Scan to open survey", use_container_width=True)

    # ── My Surveys ─────────────────────────────────────────────────────────────
    with tab_surveys:
        st.markdown("<br>", unsafe_allow_html=True)
        if not data["surveys"]:
            st.info("No surveys yet. Create one in the Create Survey tab.")
        else:
            base_url2 = st.text_input("App URL", value=detect_base_url(), key="base_url2")
            st.markdown("<br>", unsafe_allow_html=True)

            for sid, survey in reversed(list(data["surveys"].items())):
                n_responses = len(data["responses"].get(sid, []))
                survey_url  = f"{base_url2.rstrip('/')}/?page=survey&id={sid}"
                results_url = f"{base_url2.rstrip('/')}/?page=results&id={sid}"

                with st.expander(f"{survey['title']}  —  {n_responses} response(s)"):
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.markdown(f"<div style='font-size:11px; font-weight:600; letter-spacing:1.5px; text-transform:uppercase; color:{BC_RED}; margin-bottom:6px;'>Survey Link</div>", unsafe_allow_html=True)
                        st.code(survey_url, language=None)
                        st.image(make_qr(survey_url), width=160)
                    with c2:
                        st.markdown(f"<div style='font-size:11px; font-weight:600; letter-spacing:1.5px; text-transform:uppercase; color:{BC_RED}; margin-bottom:6px;'>Results Link</div>", unsafe_allow_html=True)
                        st.code(results_url, language=None)
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("View Results →", key=f"view_{sid}", type="primary"):
                            st.query_params["page"] = "results"
                            st.query_params["id"] = sid
                            st.rerun()
                    st.caption(f"ID: {sid}  ·  {len(survey['questions'])} question(s)")
