"""
Deep Research Assistant - Streamlit front end for the multi-agent pipeline.

Run locally:   streamlit run app.py
Deploy:        push to GitHub -> Streamlit Community Cloud (add API keys under Secrets)
"""

import math
import os
import re
import time
import traceback
from datetime import datetime
from typing import Optional

import streamlit as st

# --------------------------------------------------------------------------
# Page config (must be the first Streamlit call)
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Deep Research Assistant",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# Environment: .env locally, st.secrets when deployed
# --------------------------------------------------------------------------
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

try:
    for _k, _v in st.secrets.items():
        if isinstance(_v, str) and _k not in os.environ:
            os.environ[_k] = _v
except Exception:
    pass  # no secrets file locally - .env is used instead

# --------------------------------------------------------------------------
# Themes
# --------------------------------------------------------------------------
THEMES = {
    "Daylight": dict(
        bg="#f4f7ff", card="#ffffff", ink="#14213d", soft="#53607c", line="#dbe3f3",
        accent="#4f46e5", accent_soft="#ebeaff", on_accent="#ffffff", code="#f1f4fb",
        hero="linear-gradient(120deg,#4f46e5 0%,#7c3aed 48%,#ec4899 100%)",
        shadow="0 10px 34px rgba(79,70,229,.12)",
    ),
    "Sunset": dict(
        bg="#fff6f1", card="#ffffff", ink="#2b1630", soft="#7a5a6b", line="#f1d9d3",
        accent="#e11d48", accent_soft="#ffe4ea", on_accent="#ffffff", code="#fbefec",
        hero="linear-gradient(120deg,#f97316 0%,#e11d48 52%,#9333ea 100%)",
        shadow="0 10px 34px rgba(225,29,72,.12)",
    ),
    "Midnight": dict(
        bg="#0b1020", card="#131a30", ink="#e8ecf8", soft="#9aa6c6", line="#26314f",
        accent="#38bdf8", accent_soft="#12304a", on_accent="#04121f", code="#0e1428",
        hero="linear-gradient(120deg,#0ea5e9 0%,#6366f1 55%,#a855f7 100%)",
        shadow="0 10px 34px rgba(0,0,0,.40)",
    ),
    "Aurora": dict(
        bg="#07161a", card="#0e2428", ink="#e6fbf5", soft="#8fb8b0", line="#1b3f44",
        accent="#2dd4bf", accent_soft="#0f3a3a", on_accent="#03211c", code="#0a1c20",
        hero="linear-gradient(120deg,#059669 0%,#0891b2 50%,#7c3aed 100%)",
        shadow="0 10px 34px rgba(0,0,0,.40)",
    ),
}

st.session_state.setdefault("theme", "Daylight")
st.session_state.setdefault("history", [])
st.session_state.setdefault("current", None)
st.session_state.setdefault("topic_input", "")

T = THEMES[st.session_state["theme"]]

ROOT_VARS = (
    "<style>:root{"
    f"--bg:{T['bg']};--card:{T['card']};--ink:{T['ink']};--soft:{T['soft']};"
    f"--line:{T['line']};--accent:{T['accent']};--accent-soft:{T['accent_soft']};"
    f"--on-accent:{T['on_accent']};--code:{T['code']};--hero:{T['hero']};"
    f"--shadow:{T['shadow']};"
    "}</style>"
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&family=Manrope:wght@400;500;600;700;800&display=swap');

html, body, .stApp { font-family: 'Manrope', system-ui, sans-serif; }
.stApp { background: var(--bg); }

/* text colour for everything Streamlit renders */
.stApp, .stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3,
.stApp h4, .stApp h5, .stApp h6, .stApp summary { color: var(--ink); }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: var(--soft); }
.stApp button p { color: inherit; }
.stApp hr { border-color: var(--line); }

/* chrome */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDeployButton"] { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.8rem; padding-bottom: 4rem; max-width: 1100px; }

/* ---------- hero ---------- */
.stApp .hero {
  position: relative; overflow: hidden;
  background: var(--hero);
  border-radius: 22px;
  padding: 2.4rem 2.6rem 2.2rem 2.6rem;
  margin-bottom: 1.6rem;
  box-shadow: var(--shadow);
}
.hero::before, .hero::after { content: ""; position: absolute; border-radius: 50%; pointer-events: none; }
.hero::before { width: 340px; height: 340px; right: -90px; top: -150px; background: rgba(255,255,255,.14); }
.hero::after  { width: 220px; height: 220px; right: 140px; bottom: -130px; background: rgba(255,255,255,.10); }
.stApp .hero h1 {
  font-family: 'Newsreader', Georgia, serif; font-weight: 500;
  font-size: clamp(2rem, 4vw, 3.1rem); line-height: 1.08; letter-spacing: -0.02em;
  margin: 0 0 .7rem 0; color: #fff; position: relative;
}
.stApp .hero p { color: rgba(255,255,255,.92); font-size: 1.04rem; line-height: 1.6; max-width: 60ch; margin: 0 0 1.2rem 0; position: relative; }
.hero .tags { display: flex; flex-wrap: wrap; gap: .5rem; position: relative; }
.hero .tags span {
  background: rgba(255,255,255,.18); color: #fff; border: 1px solid rgba(255,255,255,.35);
  padding: .3rem .8rem; border-radius: 999px; font-size: .82rem; font-weight: 600; backdrop-filter: blur(4px);
}

/* ---------- inputs ---------- */
div[data-baseweb="input"] {
  background: var(--card); border: 1.5px solid var(--line); border-radius: 14px; box-shadow: var(--shadow);
}
div[data-baseweb="input"]:focus-within { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
div[data-baseweb="base-input"] { background: transparent; }
div[data-testid="stTextInput"] input {
  background: transparent; color: var(--ink); font-size: 1.04rem; padding: .9rem 1rem;
  -webkit-text-fill-color: var(--ink);
}
div[data-testid="stTextInput"] input::placeholder { color: var(--soft); -webkit-text-fill-color: var(--soft); opacity: .8; }

/* ---------- buttons ---------- */
.stButton > button, .stDownloadButton > button {
  border-radius: 12px; font-weight: 700; font-family: 'Manrope', sans-serif;
  border: 1.5px solid var(--line); background: var(--card); color: var(--ink);
  transition: border-color .15s, color .15s, transform .15s;
}
.stButton > button:hover, .stDownloadButton > button:hover { border-color: var(--accent); color: var(--accent); }
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible { outline: 3px solid var(--accent-soft); outline-offset: 1px; }
.stButton > button[kind="primary"] {
  background: var(--accent); border-color: var(--accent); color: var(--on-accent); padding-top: .62rem; padding-bottom: .62rem;
}
.stButton > button[kind="primary"]:hover { filter: brightness(1.08); color: var(--on-accent); transform: translateY(-1px); }

/* ---------- pipeline ---------- */
.pipeline {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: .9rem; margin: 1.4rem 0 1.8rem 0;
}
.stage {
  position: relative; background: var(--card); border: 1.5px solid var(--line);
  border-radius: 16px; padding: 1.1rem 1.1rem 1rem 1.1rem; overflow: hidden;
  box-shadow: var(--shadow);
}
.stage .bar { position: absolute; left: 0; right: 0; top: 0; height: 5px; background: var(--c); opacity: .28; }
.stage .n {
  display: inline-flex; align-items: center; justify-content: center;
  width: 2.2rem; height: 2.2rem; border-radius: 12px; font-size: 1.1rem; font-weight: 800;
  background: var(--accent-soft); margin-bottom: .6rem;
}
.stage .t { font-weight: 800; font-size: 1rem; margin-bottom: .15rem; color: var(--ink); }
.stage .d { font-size: .85rem; color: var(--soft); line-height: 1.45; }
.stage.active { border-color: var(--c); }
.stage.active .bar, .stage.done .bar { opacity: 1; }
.stage.active .n { background: var(--c); animation: ring 1.5s ease-out infinite; }
.stage.done .n { background: var(--c); color: #fff; }
.stage.error { border-color: #dc2626; }
.stage.error .bar { background: #dc2626; opacity: 1; }
.stage.error .n { background: #dc2626; color: #fff; }
@keyframes ring { 0% { box-shadow: 0 0 0 0 var(--c); } 100% { box-shadow: 0 0 0 12px transparent; } }
@media (prefers-reduced-motion: reduce) { .stage.active .n { animation: none; } }
@media (max-width: 800px) { .pipeline { grid-template-columns: 1fr 1fr; } }

/* ---------- results ---------- */
.result-head h2 {
  font-family: 'Newsreader', Georgia, serif; font-weight: 500; font-size: 1.9rem;
  letter-spacing: -0.01em; margin: 0 0 .6rem 0; color: var(--ink);
}
.chips { display: flex; flex-wrap: wrap; gap: .5rem; margin-bottom: 1rem; }
.chip {
  background: var(--accent-soft); color: var(--accent); border-radius: 999px;
  padding: .3rem .85rem; font-size: .82rem; font-weight: 700;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--card); border: 1.5px solid var(--line); border-left: 6px solid var(--accent);
  border-radius: 16px; box-shadow: var(--shadow);
}
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] h1,
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] h2,
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] h3 {
  font-family: 'Newsreader', Georgia, serif; font-weight: 500; letter-spacing: -0.01em;
}
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] p,
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] li {
  font-family: 'Newsreader', Georgia, serif; font-size: 1.1rem; line-height: 1.7;
}
.stApp a { color: var(--accent); }

/* tabs */
button[role="tab"] { color: var(--soft); font-weight: 700; }
button[role="tab"][aria-selected="true"] { color: var(--accent); }
div[data-baseweb="tab-highlight"] { background: var(--accent); }
div[data-baseweb="tab-border"] { background: var(--line); }

/* expander + code */
[data-testid="stExpander"] details { background: var(--card); border: 1.5px solid var(--line); border-radius: 12px; }
.stApp pre, .stApp [data-testid="stCode"] { background: var(--code); }
.stApp pre code, .stApp pre span { color: var(--ink); }

/* sidebar */
section[data-testid="stSidebar"] { background: var(--card); border-right: 1.5px solid var(--line); }
.brand { display: flex; align-items: center; gap: .65rem; margin-bottom: .6rem; }
.brand .logo {
  width: 2.3rem; height: 2.3rem; border-radius: 12px; background: var(--hero);
  display: flex; align-items: center; justify-content: center; font-size: 1.15rem;
}
.brand .name { font-weight: 800; font-size: 1.05rem; line-height: 1.1; color: var(--ink); }
.brand .sub { font-size: .78rem; color: var(--soft); }
.side-title { font-weight: 800; font-size: .92rem; margin: .2rem 0 .4rem 0; color: var(--ink); }
.side-note { color: var(--soft); font-size: .85rem; line-height: 1.5; }
</style>
"""
st.markdown(ROOT_VARS + CSS, unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
SEARCH_SNIPPET_CHARS = 1500  # how much of the search result the reader agent sees

STAGES = [
    ("🔎", "Search", "Finds recent, reliable sources", "#3b82f6"),
    ("📖", "Read", "Scrapes the most relevant page", "#14b8a6"),
    ("✍️", "Write", "Drafts the full report", "#f59e0b"),
    ("🧐", "Review", "Critiques accuracy and gaps", "#ec4899"),
]

EXAMPLES = [
    "Impact of generative AI on software jobs",
    "Solid-state batteries: where the technology stands",
    "How CRISPR is being used in agriculture",
]

URL_RE = re.compile(r"https?://[^\s)\]>\"']+")


def to_text(content) -> str:
    """LangChain message content can be a string or a list of content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            parts.append(block.get("text", "") if isinstance(block, dict) else str(block))
        return "\n".join(p for p in parts if p)
    return str(content)


def stepper_html(active: Optional[int], done: int, failed: Optional[int] = None) -> str:
    cells = []
    for i, (icon, title, desc, color) in enumerate(STAGES):
        cls, label = "", icon
        if failed is not None and i == failed:
            cls, label = "error", "!"
        elif i < done:
            cls, label = "done", "✓"
        elif active is not None and i == active:
            cls = "active"
        cells.append(
            f'<div class="stage {cls}" style="--c:{color}"><div class="bar"></div>'
            f'<div class="n">{label}</div><div class="t">{title}</div>'
            f'<div class="d">{desc}</div></div>'
        )
    return f'<div class="pipeline">{"".join(cells)}</div>'


def run_pipeline(topic: str, stepper_slot) -> dict:
    """Same logic as pipeline.py, but reports progress to the UI."""
    from agents import build_reader_agent, build_search_agent, critic_chain, writer_chain

    state: dict = {"topic": topic}
    step = 0
    try:
        # 1 - search
        stepper_slot.markdown(stepper_html(0, 0), unsafe_allow_html=True)
        res = build_search_agent().invoke(
            {"messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]}
        )
        state["search_results"] = to_text(res["messages"][-1].content)

        # 2 - read
        step = 1
        stepper_slot.markdown(stepper_html(1, 1), unsafe_allow_html=True)
        res = build_reader_agent().invoke(
            {
                "messages": [
                    (
                        "user",
                        f"Based on the following search results about '{topic}', "
                        f"pick the most relevant URL and scrape it for deeper content.\n\n"
                        f"Search Results:\n{state['search_results'][:SEARCH_SNIPPET_CHARS]}",
                    )
                ]
            }
        )
        state["scraped_content"] = to_text(res["messages"][-1].content)

        # 3 - write
        step = 2
        stepper_slot.markdown(stepper_html(2, 2), unsafe_allow_html=True)
        research_combined = (
            f"SEARCH RESULTS : \n {state['search_results']} \n\n"
            f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
        )
        state["report"] = to_text(writer_chain.invoke({"topic": topic, "research": research_combined}))

        # 4 - review
        step = 3
        stepper_slot.markdown(stepper_html(3, 3), unsafe_allow_html=True)
        state["feedback"] = to_text(critic_chain.invoke({"report": state["report"]}))

        stepper_slot.markdown(stepper_html(None, 4), unsafe_allow_html=True)
        return state
    except Exception as exc:
        stepper_slot.markdown(stepper_html(None, step, failed=step), unsafe_allow_html=True)
        state["error"] = exc
        state["trace"] = traceback.format_exc()
        return state


def set_topic(value: str):
    st.session_state["topic_input"] = value


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="logo">🔎</div><div>'
        '<div class="name">Deep Research</div><div class="sub">Multi-agent assistant</div>'
        "</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="side-title">Theme</div>', unsafe_allow_html=True)
    st.radio("Theme", list(THEMES.keys()), key="theme", label_visibility="collapsed")
    st.divider()

    st.markdown('<div class="side-title">Past reports</div>', unsafe_allow_html=True)
    if not st.session_state["history"]:
        st.markdown(
            '<div class="side-note">Reports you generate in this session appear here.</div>',
            unsafe_allow_html=True,
        )
    for i in range(len(st.session_state["history"]) - 1, -1, -1):
        item = st.session_state["history"][i]
        label = item["topic"] if len(item["topic"]) <= 34 else item["topic"][:33] + "…"
        if st.button(label, key=f"hist_{i}", use_container_width=True):
            st.session_state["current"] = item
            st.rerun()
    if st.session_state["history"]:
        if st.button("Clear history", use_container_width=True):
            st.session_state["history"] = []
            st.session_state["current"] = None
            st.rerun()

# --------------------------------------------------------------------------
# Hero + input
# --------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
      <h1>Research any topic in minutes, with sources.</h1>
      <p>Enter a topic. Four AI agents search the web, read the strongest source,
      write a structured report, and review their own work before you see it.</p>
      <div class="tags"><span>4 AI agents</span><span>Live web search</span><span>Self-reviewed reports</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

col_in, col_btn = st.columns([5, 1.3], vertical_alignment="bottom")
with col_in:
    topic = st.text_input(
        "Research topic",
        key="topic_input",
        placeholder="e.g. The future of nuclear fusion energy",
        label_visibility="collapsed",
    )
with col_btn:
    go = st.button("Start research", type="primary", use_container_width=True)

st.caption("Try an example")
for col, ex in zip(st.columns(len(EXAMPLES)), EXAMPLES):
    col.button(ex, key=f"ex_{ex}", on_click=set_topic, args=(ex,), use_container_width=True)

stepper_slot = st.empty()

# --------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------
if go:
    clean_topic = topic.strip()
    if len(clean_topic) < 3:
        st.warning("Enter a topic with at least 3 characters.")
    else:
        started = time.time()
        result = run_pipeline(clean_topic, stepper_slot)
        result["elapsed"] = time.time() - started
        result["created"] = datetime.now().strftime("%d %b %Y, %H:%M")
        if "error" in result:
            st.error(
                "The research run stopped before finishing. Check your API keys and "
                "network connection, then try again."
            )
            with st.expander("Technical details"):
                st.code(result["trace"])
        else:
            st.session_state["history"].append(result)
            st.session_state["current"] = result
            st.toast("Report ready", icon="✅")
elif st.session_state["current"]:
    stepper_slot.markdown(stepper_html(None, 4), unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------
cur = st.session_state["current"]
if cur and "error" not in cur:
    words = len(cur["report"].split())
    minutes = max(1, math.ceil(words / 220))
    n_sources = len(set(URL_RE.findall(cur["search_results"] + " " + cur["scraped_content"])))
    st.markdown(
        f'<div class="result-head"><h2>{cur["topic"]}</h2><div class="chips">'
        f'<span class="chip">{words:,} words</span>'
        f'<span class="chip">{minutes} min read</span>'
        f'<span class="chip">{n_sources} source link{"s" if n_sources != 1 else ""}</span>'
        f'<span class="chip">Generated in {cur["elapsed"]:.0f}s</span>'
        f'<span class="chip">{cur["created"]}</span>'
        "</div></div>",
        unsafe_allow_html=True,
    )

    tab_report, tab_review, tab_sources, tab_raw = st.tabs(
        ["Report", "Critic's review", "Search results", "Scraped page"]
    )

    with tab_report:
        with st.container(border=True):
            st.markdown(cur["report"])
        st.write("")
        dl1, dl2, _ = st.columns([1.4, 1.4, 3])
        safe_name = "".join(c if c.isalnum() else "_" for c in cur["topic"])[:50] or "report"
        dl1.download_button(
            "Download as Markdown",
            data=f"# {cur['topic']}\n\n{cur['report']}\n\n---\n\n## Critic's review\n\n{cur['feedback']}",
            file_name=f"{safe_name}.md",
            mime="text/markdown",
            use_container_width=True,
        )
        dl2.download_button(
            "Download as text",
            data=cur["report"],
            file_name=f"{safe_name}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with tab_review:
        with st.container(border=True):
            st.markdown(cur["feedback"])

    with tab_sources:
        with st.container(border=True):
            st.markdown(cur["search_results"])

    with tab_raw:
        with st.container(border=True):
            st.markdown(cur["scraped_content"])
elif not go:
    st.markdown(
        '<div class="side-note" style="margin-top:1.2rem">Your report appears here once the run finishes. '
        "A typical run takes one to three minutes.</div>",
        unsafe_allow_html=True,
    )