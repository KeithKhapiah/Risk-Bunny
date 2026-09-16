"""UPI Fraud Ring & Merchant Analytics dashboard.

Run with: streamlit run dashboard.py
"""

from pathlib import Path
import time
import base64
from textwrap import dedent

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="UPI Fraud Analytics", page_icon="◆", layout="wide")

def find_data_dir():
    here = Path(__file__).resolve().parent
    repo_root = here.parent
    candidates = [
        repo_root / "data" / "processed",
        here / "data" / "processed",
        repo_root / "data",
        here / "data",
        repo_root / "DATA" / "cleaned_data",
        here / "DATA" / "cleaned_data",
        repo_root / "cleaned_data",
        here / "cleaned_data",
        Path("data/processed").resolve(),
        Path("data").resolve(),
        Path("DATA/cleaned_data").resolve(),
        Path("cleaned_data").resolve(),
    ]
    for c in candidates:
        if (c / "dim_customers.csv").exists() or (c / "fact_transactions.csv").exists():
            return c
    return repo_root / "data" / "processed"

DATA_DIR = find_data_dir()

try:
    from agent.agent import query_agent
except ImportError:
    try:
        from agent import query_agent
    except ImportError:
        import sys
        here = Path(__file__).resolve().parent
        repo_root = here.parent
        sys.path.extend([str(here), str(repo_root), str(repo_root / "agent")])
        from agent import query_agent

def get_bunny_assets():
    here = Path(__file__).resolve().parent
    repo_root = here.parent
    candidates = [
        here / "assets" / "bunny.png",
        repo_root / "dashboard" / "assets" / "bunny.png",
        repo_root / "agent" / "assets" / "bunny.png",
        repo_root / "assets" / "bunny.png",
        here / "bunny.png",
        repo_root / "bunny.png",
        Path("dashboard/assets/bunny.png").resolve(),
        Path("bunny.png").resolve(),
    ]
    img_path = None
    b64_str = ""
    for c in candidates:
        if c.exists():
            img_path = str(c)
            try:
                with open(c, "rb") as f:
                    b64_str = base64.b64encode(f.read()).decode("utf-8")
            except Exception:
                pass
            break
    return img_path, b64_str

BUNNY_IMG_PATH, BUNNY_B64 = get_bunny_assets()

COLORS = [
    "#06B6D4",  # Cyan / Electric Blue
    "#818CF8",  # Indigo / Electric Violet
    "#10B981",  # Emerald Green
    "#F59E0B",  # Warm Amber
    "#F43F5E",  # Rose / Crimson
    "#38BDF8",  # Sky Blue
    "#A855F7",  # Purple
    "#FB7185",  # Coral
]


@st.cache_data(show_spinner="Loading dashboard data...")
def load_data():
    customers = pd.read_csv(DATA_DIR / "dim_customers.csv")
    merchants = pd.read_csv(DATA_DIR / "dim_merchants.csv")
    transactions = pd.read_csv(DATA_DIR / "fact_transactions.csv")
    chargebacks = pd.read_csv(DATA_DIR / "fact_chargebacks.csv")

    date_columns = [
        (customers, ["date_of_birth_clean", "signup_timestamp_clean"]),
        (merchants, ["onboarding_date_clean"]),
        (transactions, ["txn_timestamp"]),
        (chargebacks, [
            "transaction_timestamp_clean",
            "reported_timestamp_clean",
            "bank_response_timestamp_clean",
        ]),
    ]
    for frame, columns in date_columns:
        for column in columns:
            frame[column] = pd.to_datetime(frame[column], errors="coerce")

    transactions["merchant_category_final"] = transactions[
        "merchant_category_final"
    ].fillna("Unclassified")
    chargebacks["merchant_category_final"] = chargebacks[
        "merchant_category_final"
    ].fillna("Unclassified")
    return customers, merchants, transactions, chargebacks


def money(value: float) -> str:
    return f"₹{value:,.0f}"


def metric_card(label: str, value: str, help_text: str = "", accent: str = "#06B6D4"):
    st.markdown(
        f"<div class='metric-tile' style='border-top: 3px solid {accent};'>"
        f"<span>{label}</span><strong>{value}</strong>"
        f"<small>{help_text}</small></div>",
        unsafe_allow_html=True,
    )


def chart(fig, key=None):
    if key is None:
        import uuid
        key = f"chart_{uuid.uuid4().hex}"
    fig.update_layout(
        template="plotly_dark",
        colorway=COLORS,
        margin=dict(l=8, r=8, t=42, b=8),
        legend_title_text="",
        font=dict(family="Inter, Arial, sans-serif", color="#94A3B8"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False, zeroline=False, tickfont=dict(color="#94A3B8"))
    fig.update_yaxes(gridcolor="rgba(255, 255, 255, 0.07)", zeroline=False, tickfont=dict(color="#94A3B8"))
    st.plotly_chart(fig, use_container_width=True, key=key)


def section_heading(title: str, description: str):
    st.markdown(
        f"<div class='section-title'><span>LIVE ANALYTICS</span><h2>{title}</h2><p>{description}</p></div>",
        unsafe_allow_html=True,
    )


def render_full_screen_agent():
    """Render an immersive full-screen chatbot experience featuring Risk Bunny."""
    st.markdown(
        dedent(f"""
        <style>
        [data-testid="stSidebar"] {{ display: none !important; }}
        [data-testid="collapsedControl"] {{ display: none !important; }}
        .block-container {{
            max-width: 960px !important;
            padding-top: 1.2rem !important;
            padding-bottom: 5.5rem !important;
        }}
        .bunny-badge {{
            display: flex;
            align-items: center;
            gap: 14px;
        }}
        .bunny-avatar-sm {{
            width: 44px;
            height: 44px;
            border-radius: 50%;
            object-fit: cover;
            border: 1.5px solid #06B6D4;
            box-shadow: 0 0 12px rgba(6, 182, 212, 0.35);
        }}
        .bunny-name {{
            font-size: 1.25rem;
            font-weight: 800;
            color: #FFFFFF;
            line-height: 1.2;
            letter-spacing: -0.01em;
        }}
        .bunny-status {{
            font-size: 0.74rem;
            color: #94A3B8;
            font-weight: 600;
            letter-spacing: 0.04em;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .bunny-pulse-dot {{
            width: 7px;
            height: 7px;
            background: #10B981;
            border-radius: 50%;
            box-shadow: 0 0 8px #10B981;
        }}
        .bunny-hero-box {{
            text-align: center;
            padding: 20px 16px 14px;
        }}
        .bunny-hero-avatar {{
            width: 85px;
            height: 85px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid #06B6D4;
            box-shadow: 0 0 24px rgba(6, 182, 212, 0.35);
            margin-bottom: 12px;
        }}
        .bunny-hero-heading {{
            font-size: 1.65rem;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: -0.02em;
            margin-bottom: 6px;
        }}
        .bunny-hero-sub {{
            font-size: 0.95rem;
            color: #94A3B8;
            max-width: 560px;
            margin: 0 auto 20px;
            line-height: 1.45;
        }}
        div[data-testid="stButton"] button {{
            white-space: pre-wrap !important;
            word-break: break-word !important;
            text-align: left !important;
            background: #121624 !important;
            border: 1px solid #1E2538 !important;
            color: #CBD5E1 !important;
            border-radius: 12px !important;
            transition: all 0.2s ease !important;
        }}
        div[data-testid="stButton"] button:hover {{
            background: #161D2E !important;
            border-color: #38BDF8 !important;
            color: #FFFFFF !important;
            box-shadow: 0 4px 14px rgba(6, 182, 212, 0.15) !important;
        }}
        </style>
        """).strip(),
        unsafe_allow_html=True,
    )

    top_col_brand, top_col_actions = st.columns([0.68, 0.32])
    with top_col_brand:
        if BUNNY_B64:
            st.markdown(
                f"""
                <div class="bunny-badge">
                    <img src="data:image/png;base64,{BUNNY_B64}" class="bunny-avatar-sm" />
                    <div>
                        <div class="bunny-name">Risk Bunny</div>
                        <div class="bunny-status"><span class="bunny-pulse-dot"></span>ONLINE • DUCKDB RISK COPILOT</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown("### 🐰 Risk Bunny AI Copilot")
    with top_col_actions:
        st.write("")
        act_c1, act_c2 = st.columns(2)
        with act_c1:
            if st.button("🗑️ Reset", key="fs_reset_btn", use_container_width=True):
                st.session_state["agent_chat_messages"] = []
                st.rerun()
        with act_c2:
            if st.button("✕ Close", key="fs_close_btn", use_container_width=True):
                st.session_state["full_screen_agent"] = False
                st.rerun()

    st.divider()

    messages = st.session_state.get("agent_chat_messages", [])
    clicked_prompt = None

    if len(messages) == 0:
        if BUNNY_B64:
            st.markdown(
                f"""
                <div class="bunny-hero-box">
                    <img src="data:image/png;base64,{BUNNY_B64}" class="bunny-hero-avatar" />
                    <div class="bunny-hero-heading">How can Risk Bunny help you today?</div>
                    <div class="bunny-hero-sub">
                        Ask questions in plain English to uncover UPI fraud rings, investigate chargeback anomalies, or analyze merchant risk exposure.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown("### 🐰 How can Risk Bunny help you today?\nAsk questions in plain English about transactions, merchants, and chargebacks.")

        r1_c1, r1_c2 = st.columns(2)
        with r1_c1:
            if st.button(
                "📊  Top Disputed Categories\n\nWhich merchant category has the highest chargeback count?",
                key="fs_card_1",
                use_container_width=True,
            ):
                clicked_prompt = "Which merchant category has the highest chargeback count?"
        with r1_c2:
            if st.button(
                "📈  Daily Volume & Failures\n\nShow daily transaction volume trend and failure count.",
                key="fs_card_2",
                use_container_width=True,
            ):
                clicked_prompt = "Show daily transaction volume trend and failure count."

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        r2_c1, r2_c2 = st.columns(2)
        with r2_c1:
            if st.button(
                "⚠️  Missing UTR Correlation\n\nWhat is the correlation between missing UTR and transaction status?",
                key="fs_card_3",
                use_container_width=True,
            ):
                clicked_prompt = "What is the correlation between missing UTR and transaction status?"
        with r2_c2:
            if st.button(
                "🚨  Top Serial Disputers\n\nShow top 10 users by total disputed amount.",
                key="fs_card_4",
                use_container_width=True,
            ):
                clicked_prompt = "Show top 10 users by total disputed amount."

        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

    else:
        avatar_assistant = BUNNY_IMG_PATH if BUNNY_IMG_PATH else "🐰"
        for idx, msg in enumerate(messages):
            with st.chat_message(msg["role"], avatar=avatar_assistant if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])
                if msg.get("fig") is not None:
                    chart(msg["fig"], key=f"fs_hist_fig_{idx}")
                if msg.get("sql_query"):
                    with st.expander("🔍 View Synthesized DuckDB SQL & Data"):
                        st.code(msg["sql_query"], language="sql")
                        if msg.get("df") is not None and not msg["df"].empty:
                            st.dataframe(msg["df"], use_container_width=True, hide_index=True)

    user_input = st.chat_input("Ask Risk Bunny anything about your UPI data...")
    active_prompt = user_input if user_input else clicked_prompt

    if active_prompt:
        if "agent_chat_messages" not in st.session_state:
            st.session_state["agent_chat_messages"] = []

        st.session_state["agent_chat_messages"].append({
            "role": "user",
            "content": active_prompt,
            "fig": None,
            "sql_query": None,
            "df": None,
        })

        with st.chat_message("user", avatar="👤"):
            st.markdown(active_prompt)

        avatar_assistant = BUNNY_IMG_PATH if BUNNY_IMG_PATH else "🐰"
        with st.chat_message("assistant", avatar=avatar_assistant):
            with st.spinner("Risk Bunny is querying DuckDB and analyzing patterns..."):
                res = query_agent(active_prompt)

            if res.get("error"):
                err_text = f"⚠️ **Query Execution Issue:** {res['error']}"
                st.error(err_text)
                st.session_state["agent_chat_messages"].append({
                    "role": "assistant",
                    "content": err_text,
                    "fig": None,
                    "sql_query": res.get("sql_query"),
                    "df": None,
                })
            else:
                response_text = f"### {res.get('chart_title', 'Analysis Results')}\n\n{res.get('executive_summary', '')}"
                st.markdown(response_text)
                if res.get("fig") is not None:
                    import uuid
                    chart(res["fig"], key=f"fs_live_fig_{len(messages)}_{uuid.uuid4().hex[:6]}")
                if res.get("sql_query"):
                    with st.expander("🔍 View Synthesized DuckDB SQL & Data"):
                        st.code(res.get("sql_query", ""), language="sql")
                        if res.get("df") is not None and not res["df"].empty:
                            st.dataframe(res["df"], use_container_width=True, hide_index=True)

                st.session_state["agent_chat_messages"].append({
                    "role": "assistant",
                    "content": response_text,
                    "fig": res.get("fig"),
                    "sql_query": res.get("sql_query"),
                    "df": res.get("df"),
                })

        st.rerun()


def show_boot_sequence():
    """Render a one-time, session-based launch experience before the dashboard."""
    st.markdown(
        dedent("""
        <style>
        .stApp { background: radial-gradient(circle at 50% 38%, #2D2467 0%, #111935 34%, #070B18 78%); }
        .boot-wrap { min-height: 84vh; display: flex; align-items: center; justify-content: center; text-align: center; color: #F5F7FF; }
        .boot-scene { width: min(480px, 96vw); position: relative; padding: 32px 25px 28px; border: 1px solid rgba(150, 173, 255, .18); border-radius: 28px;
            background: linear-gradient(145deg, rgba(33, 42, 89, .72), rgba(9, 15, 35, .72)); box-shadow: 0 26px 85px rgba(0,0,0,.42); overflow: hidden; }
        .boot-scene:before { content: ''; position: absolute; inset: 0; opacity: .3; background-image: linear-gradient(rgba(110, 226, 211, .12) 1px, transparent 1px), linear-gradient(90deg, rgba(110, 226, 211, .12) 1px, transparent 1px); background-size: 26px 26px; }
        .boot-core { width: 148px; height: 148px; margin: 0 auto 26px; position: relative; display: grid; place-items: center; }
        .boot-ring, .boot-ring:before, .boot-ring:after { position: absolute; border-radius: 50%; content: ''; }
        .boot-ring { inset: 0; border: 1px solid rgba(116, 240, 218, .75); box-shadow: 0 0 30px rgba(82, 218, 208, .35); animation: spin 3s linear infinite; }
        .boot-ring:before { inset: 14px; border: 2px dashed rgba(148, 120, 255, .8); animation: spin 2.1s linear infinite reverse; }
        .boot-ring:after { width: 12px; height: 12px; top: 12px; left: 54px; background: #7DF1DC; box-shadow: 0 0 16px #7DF1DC; }
        .boot-prism { width: 51px; height: 51px; transform: rotate(45deg); background: linear-gradient(135deg, #9B83FF, #53E8D2); box-shadow: 0 0 32px rgba(104, 235, 215, .72); animation: pulse 1.35s ease-in-out infinite; }
        .boot-prism:after { content: ''; display: block; width: 18px; height: 18px; margin: 16px; background: #111933; }
        .boot-eyebrow, .boot-scene h1, .boot-scene p, .boot-progress, .boot-status { position: relative; }
        .boot-eyebrow { color: #70EAD8; font-size: .67rem; letter-spacing: .28em; font-weight: 800; }
        .boot-scene h1 { margin: 12px 0 7px; font-size: 2rem; color: #FFF; } .boot-scene p { color: #B5C0DF; margin: 0; }
        .boot-progress { height: 7px; width: min(330px, 88%); margin: 25px auto 11px; border-radius: 99px; background: #131E41; overflow: hidden; }
        .boot-progress i { display: block; height: 100%; width: 72%; border-radius: inherit; background: linear-gradient(90deg, #7768FF, #63EBD4, #FF8BAE); animation: load 1.55s ease-out forwards; }
        .boot-status { color: #98A9CF; font-size: .72rem; letter-spacing: .08em; } .boot-status b { color: #7BEAD9; }
        @keyframes spin { to { transform: rotate(360deg); } } @keyframes pulse { 50% { transform: rotate(45deg) scale(1.18); } }
        @keyframes load { from { width: 4%; } to { width: 100%; } }
        </style>
        <div class='boot-wrap'><div class='boot-scene'><div class='boot-core'><div class='boot-ring'></div><div class='boot-prism'></div></div>
        <div class='boot-eyebrow'>UPI FRAUD RING // MERCHANT ANALYTICS</div><h1>Mapping fraud risk &amp; merchant exposure</h1>
        <p>Preparing transaction patterns, chargeback cases, and merchant risk insights.</p><div class='boot-progress'><i></i></div>
        <div class='boot-status'><b>LOADING</b> &nbsp; LINKING TRANSACTIONS, MERCHANTS &amp; CHARGEBACKS</div></div></div>
        """).strip(),
        unsafe_allow_html=True,
    )
    time.sleep(1.7)
    st.session_state["boot_complete"] = True
    st.rerun()


if not st.session_state.get("boot_complete", False):
    show_boot_sequence()
    st.stop()


customers, merchants, transactions, chargebacks = load_data()

FILTER_DEFAULTS = {
    "start_date_filter": transactions["txn_timestamp"].min().date(),
    "end_date_filter": transactions["txn_timestamp"].max().date(),
    "status_filter": sorted(transactions["status_clean"].unique()),
    "category_filter": sorted(transactions["merchant_category_final"].unique()),
    "risk_filter": sorted(transactions["risk_segment_clean"].fillna("Unmatched").unique()),
}


def reset_filters():
    """Restore every global filter to the complete available data range."""
    for key, value in FILTER_DEFAULTS.items():
        st.session_state[key] = value


def apply_quick_view(view_name: str):
    """Apply a useful pre-set without changing the underlying data."""
    reset_filters()
    if view_name == "failed":
        st.session_state["status_filter"] = ["FAILED"]
    elif view_name == "high_risk":
        st.session_state["risk_filter"] = ["HIGH", "UNKNOWN"]


for filter_key, filter_value in FILTER_DEFAULTS.items():
    if filter_key not in st.session_state:
        st.session_state[filter_key] = filter_value

st.markdown(
    """<style>
    .stApp {
        background: #0B0E14;
        background-image: radial-gradient(circle at 50% 0%, #161C2B 0%, #0B0E14 65%);
        color: #E2E8F0;
    }
    .main .block-container { max-width: 1450px; padding-top: 2.2rem; padding-bottom: 3rem; }
    h1 { color: #FFFFFF; letter-spacing: -1.2px; font-weight: 800; }
    .hero {
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, #131826 0%, #0D111A 100%);
        border: 1px solid #20273B;
        border-left: 4px solid #06B6D4;
        box-shadow: 0 14px 36px rgba(0,0,0,0.5);
        padding: 24px 28px;
        border-radius: 18px;
        color: #FFFFFF;
        margin: 8px 0 24px;
    }
    .hero:after {
        content: '';
        position: absolute;
        width: 220px;
        height: 220px;
        border: 1px solid rgba(6, 182, 212, 0.12);
        border-radius: 50%;
        right: -60px;
        top: -110px;
        box-shadow: 0 0 0 35px rgba(6, 182, 212, 0.02);
    }
    .hero h3 { position: relative; margin: 0; font-size: 1.55rem; letter-spacing: -.5px; color: #FFFFFF; font-weight: 800; }
    .hero p { position: relative; margin: 6px 0 0; color: #94A3B8; font-size: .95rem; }
    .section-title { margin: 18px 0 16px; }
    .section-title span { font-size: .7rem; letter-spacing: .16em; color: #06B6D4; font-weight: 700; text-transform: uppercase; }
    .section-title h2 { margin: 3px 0; color: #FFFFFF; font-size: 1.45rem; font-weight: 800; letter-spacing: -.02em; }
    .section-title p { margin: 4px 0 0; color: #94A3B8; }
    .metric-tile {
        min-height: 115px;
        border-radius: 14px;
        padding: 16px 18px;
        background: #121624;
        border: 1px solid #1E2538;
        box-shadow: 0 4px 18px rgba(0,0,0,0.35);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .metric-tile:hover {
        transform: translateY(-2px);
        border-color: #2D3748;
    }
    .metric-tile span { color: #94A3B8; font-size: .75rem; text-transform: uppercase; letter-spacing: .08em; font-weight: 600; display: block; }
    .metric-tile strong { display: block; font-size: 1.65rem; margin-top: 8px; color: #FFFFFF; font-weight: 800; letter-spacing: -0.02em; }
    .metric-tile small { color: #64748B; display: block; margin-top: 4px; font-size: .74rem; }
    .filter-pulse {
        display: inline-block;
        padding: 7px 16px;
        margin: -2px 0 14px;
        border-radius: 999px;
        color: #94A3B8;
        background: #121624;
        border: 1px solid #1E2538;
        font-size: .82rem;
    }
    .filter-pulse b { color: #F1F5F9; }
    .spotlight {
        margin: 0 0 16px;
        padding: 12px 18px;
        border-radius: 12px;
        background: linear-gradient(90deg, rgba(245, 158, 11, 0.09) 0%, rgba(244, 63, 94, 0.06) 100%);
        border: 1px solid rgba(245, 158, 11, 0.35);
        box-shadow: 0 4px 16px rgba(245, 158, 11, 0.08);
        color: #E2E8F0;
        font-size: .88rem;
    }
    .spotlight span {
        display: inline-block;
        margin-right: 12px;
        color: #FFFFFF;
        background: linear-gradient(135deg, #F59E0B, #F43F5E);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: .65rem;
        font-weight: 800;
        letter-spacing: .12em;
    }
    .spotlight b { color: #FBBF24; }
    .spotlight strong { color: #FFFFFF; }
    [data-testid="stSidebar"] {
        background: #0A0D14 !important;
        border-right: 1px solid #1A2030 !important;
    }
    [data-testid="stSidebar"] * { color: #E2E8F0; }
    [data-testid="stSidebar"] .stCaption { color: #64748B !important; }
    [data-testid="stSidebar"] label { font-family: "Inter", "Segoe UI", sans-serif; font-weight: 600; letter-spacing: .015em; color: #CBD5E1 !important; }
    
    /* Multiselect container */
    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] [data-baseweb="input"] > div,
    [data-baseweb="select"] > div {
        background: #111522 !important;
        border: 1px solid #1E2538 !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] > div:hover,
    [data-baseweb="select"] > div:hover {
        border-color: #2D3A54 !important;
    }

    /* Filter Button Pills - Matches Sidebar Action Buttons */
    div[data-testid="stPills"],
    div[data-testid="stButtonGroup"] {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 6px !important;
        margin-bottom: 12px !important;
    }
    div[data-testid="stPills"] button,
    div[data-testid="stButtonGroup"] button,
    div[data-testid="stPills"] [data-testid="stBaseButton-pills"],
    div[data-testid="stButtonGroup"] [data-testid="stBaseButton-pills"] {
        background: #141826 !important;
        background-color: #141826 !important;
        border: 1px solid #20273B !important;
        border-radius: 8px !important;
        color: #94A3B8 !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        padding: 5px 12px !important;
        transition: all 0.15s ease !important;
        box-shadow: none !important;
    }
    div[data-testid="stPills"] button:hover,
    div[data-testid="stButtonGroup"] button:hover {
        background: #1E2538 !important;
        background-color: #1E2538 !important;
        border-color: #38BDF8 !important;
        color: #FFFFFF !important;
    }
    div[data-testid="stPills"] button[aria-checked="true"],
    div[data-testid="stPills"] button[aria-pressed="true"],
    div[data-testid="stButtonGroup"] button[aria-checked="true"],
    div[data-testid="stButtonGroup"] button[aria-pressed="true"],
    div[data-testid="stPills"] [data-testid="stBaseButton-pillsActive"],
    div[data-testid="stButtonGroup"] [data-testid="stBaseButton-pillsActive"] {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.18) 0%, rgba(99, 102, 241, 0.18) 100%) !important;
        background-color: rgba(6, 182, 212, 0.15) !important;
        border: 1px solid #06B6D4 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        box-shadow: 0 0 10px rgba(6, 182, 212, 0.25) !important;
    }

    [data-testid="stSidebar"] button {
        border: 1px solid #20273B;
        background: #141826;
        color: #E2E8F0;
        border-radius: 8px;
        font-weight: 600;
    }
    [data-testid="stSidebar"] button:hover {
        background: #1E2538;
        border-color: #38BDF8;
        color: #FFFFFF;
    }
    .quick-label { margin: 16px 0 7px; color: #94A3B8; font-size: .66rem; letter-spacing: .14em; font-weight: 800; }
    div[data-testid="stRadio"] > div { gap: .5rem; }
    div[data-testid="stRadio"] label {
        background: #111522;
        border: 1px solid #1E2538;
        border-radius: 999px;
        padding: 7px 16px;
        color: #94A3B8;
        font-size: .85rem;
        transition: all 0.2s ease;
    }
    div[data-testid="stRadio"] label:hover {
        border-color: #38BDF8;
        color: #FFFFFF;
    }
    div[data-testid="stRadio"] label:has(input:checked) {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.16) 0%, rgba(99, 102, 241, 0.16) 100%);
        border: 1px solid #06B6D4;
        color: #FFFFFF;
        font-weight: 700;
        box-shadow: 0 0 14px rgba(6, 182, 212, 0.25);
    }
    [data-testid="stPlotlyChart"] {
        background: #111522;
        border: 1px solid #1E2538;
        border-radius: 14px;
        padding: 8px 6px 4px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
    }
    [data-testid="stDataFrame"] {
        border: 1px solid #1E2538;
        border-radius: 12px;
        overflow: hidden;
        background: #111522;
    }
    [data-testid="stChatMessage"] {
        background: #111522;
        border: 1px solid #1E2538;
        border-radius: 16px;
        padding: 14px 18px;
        margin-bottom: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,.3);
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: #151A2B;
        border: 1px solid #232E48;
    }
    [data-testid="stChatInput"] {
        border-radius: 12px;
        border: 1px solid #232E48;
        background: #111522;
        color: #FFFFFF;
    }
    div[data-testid="stButton"] button {
        border-radius: 8px;
        border: 1px solid #1E2538;
        background: #121624;
        color: #CBD5E1;
        transition: all 0.2s ease;
    }
    div[data-testid="stButton"] button:hover {
        border-color: #06B6D4;
        background: #182032;
        color: #FFFFFF;
    }
    </style>""",
    unsafe_allow_html=True,
)

if st.session_state.get("full_screen_agent", False):
    render_full_screen_agent()
    st.stop()

col_head_left, col_head_bunny = st.columns([0.84, 0.16])
with col_head_left:
    st.title("UPI Fraud Ring & Merchant Analytics")
    st.markdown("""<div class='hero'><h3>Monitor payments. Surface risk. Act with confidence.</h3>
<p>Interactive operational analytics across transactions, merchant exposure, and chargeback cases.</p></div>""", unsafe_allow_html=True)

with col_head_bunny:
    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
    if BUNNY_B64:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: flex-end; gap: 7px; margin-bottom: 5px;">
                <div style="position: relative; display: flex; align-items: center;">
                    <img src="data:image/png;base64,{BUNNY_B64}" style="width: 28px; height: 28px; border-radius: 50%; object-fit: cover; border: 1.5px solid #3F3F46; box-shadow: 0 0 8px rgba(255, 255, 255, 0.12);" />
                    <span style="position: absolute; bottom: 0px; right: 0px; width: 8px; height: 8px; background: #10B981; border: 1.5px solid #09090B; border-radius: 50%;"></span>
                </div>
                <div style="font-size: 0.74rem; font-weight: 700; color: #A1A1AA; letter-spacing: 0.03em;">ONLINE</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    if st.button("🐰 Ask Risk Bunny", key="btn_hero_bunny", use_container_width=True):
        st.session_state["full_screen_agent"] = True
        st.rerun()

# Global filters only use columns that exist in the supplied data.
with st.sidebar:
    st.markdown("### Command filters")
    st.caption("Refine every view in the dashboard")
    st.markdown("<div class='quick-label'>QUICK EXPLORE</div>", unsafe_allow_html=True)
    quick_left, quick_right = st.columns(2)
    with quick_left:
        st.button("All activity", key="quick_all", use_container_width=True, on_click=apply_quick_view, args=("all",))
        st.button("High risk", key="quick_risk", use_container_width=True, on_click=apply_quick_view, args=("high_risk",))
    with quick_right:
        st.button("Failed only", key="quick_failed", use_container_width=True, on_click=apply_quick_view, args=("failed",))
        st.button("Reset", key="quick_reset", use_container_width=True, on_click=reset_filters)
    st.divider()
    min_date, max_date = transactions["txn_timestamp"].min().date(), transactions["txn_timestamp"].max().date()
    st.markdown("<div class='quick-label'>TRANSACTION PERIOD</div>", unsafe_allow_html=True)
    date_left, date_right = st.columns(2)
    with date_left:
        selected_start = st.date_input("From", min_value=min_date, max_value=max_date, key="start_date_filter")
    with date_right:
        selected_end = st.date_input("To", min_value=min_date, max_value=max_date, key="end_date_filter")
    status_options = sorted(transactions["status_clean"].unique())
    category_options = sorted(transactions["merchant_category_final"].unique())
    risk_options = sorted(transactions["risk_segment_clean"].fillna("Unmatched").unique())

    statuses = st.pills("Transaction status", status_options, default=st.session_state.get("status_filter", status_options), selection_mode="multi", key="status_filter")
    categories = st.pills("Merchant category", category_options, default=st.session_state.get("category_filter", category_options), selection_mode="multi", key="category_filter")
    risks = st.pills("Risk segment", risk_options, default=st.session_state.get("risk_filter", risk_options), selection_mode="multi", key="risk_filter")

    effective_statuses = statuses if (statuses and len(statuses) > 0) else status_options
    effective_categories = categories if (categories and len(categories) > 0) else category_options
    effective_risks = risks if (risks and len(risks) > 0) else risk_options

    st.divider()
    st.caption("Unmatched customer and merchant IDs are retained in all calculations.")
    with st.expander("How to use this dashboard"):
        st.write("Use Quick Explore for a starting view, then refine the date, status, merchant category, and risk filters. Every chart and table updates together.")

if selected_start > selected_end:
    st.sidebar.warning("The end date was before the start date, so the dates were swapped.")
    selected_start, selected_end = selected_end, selected_start
start_date = pd.Timestamp(selected_start)
end_date = pd.Timestamp(selected_end) + pd.Timedelta(days=1)

tx = transactions.loc[
    (transactions["txn_timestamp"] >= start_date)
    & (transactions["txn_timestamp"] < end_date)
    & transactions["status_clean"].isin(effective_statuses)
    & transactions["merchant_category_final"].isin(effective_categories)
    & transactions["risk_segment_clean"].fillna("Unmatched").isin(effective_risks)
].copy()

# A left join avoids removing transaction rows. One transaction may have several complaints.
matched_cb = chargebacks[chargebacks["txn_id"].isin(tx["txn_id"])].copy()
st.markdown(
    f"<div class='filter-pulse'><b>{len(tx):,}</b> transactions in view &nbsp; | &nbsp; "
    f"<b>{len(matched_cb):,}</b> linked chargeback complaints</div>",
    unsafe_allow_html=True,
)

if len(tx):
    spotlight = tx.groupby("merchant_category_final", as_index=False).agg(total_transactions=("txn_id", "nunique"))
    disputed = matched_cb.groupby("merchant_category_final", as_index=False).agg(disputed_transactions=("txn_id", "nunique"))
    spotlight = spotlight.merge(disputed, on="merchant_category_final", how="left").fillna(0)
    spotlight["ratio"] = spotlight["disputed_transactions"] / spotlight["total_transactions"]
    top_spotlight = spotlight.sort_values("ratio", ascending=False).iloc[0]
    st.markdown(
        f"<div class='spotlight'><span>ATTENTION SIGNAL</span><b>{top_spotlight['merchant_category_final']}</b> has the highest chargeback exposure in the current view "
        f"at <strong>{top_spotlight['ratio']:.2%}</strong>. Use Merchant Analytics to inspect the contributing merchants.</div>",
        unsafe_allow_html=True,
    )
else:
    st.warning("No transactions match the current filters. Try widening the date period or use Reset.")
    st.stop()
page = st.radio("Dashboard section", ["Executive Overview", "Fraud & Risk", "Merchant Analytics", "Chargeback Analytics"], horizontal=True, label_visibility="collapsed")

if page == "Executive Overview":
    section_heading("Executive overview", "A concise view of payment activity and the chargeback exposure behind it.")
    successful = (tx["status_clean"] == "SUCCESS").mean() if len(tx) else 0
    disputed_txns = matched_cb["txn_id"].dropna().nunique()
    ratio = disputed_txns / tx["txn_id"].nunique() if len(tx) else 0
    a, b, c, d, e = st.columns(5)
    with a: metric_card("Transactions", f"{len(tx):,}", accent="#06B6D4")
    with b: metric_card("Transaction value", money(tx["amount"].sum()), accent="#818CF8")
    with c: metric_card("Success rate", f"{successful:.1%}", accent="#10B981")
    with d: metric_card("Chargeback complaints", f"{len(matched_cb):,}", accent="#F59E0B")
    with e: metric_card("Chargeback ratio", f"{ratio:.2%}", "Distinct disputed transactions ÷ all transactions", accent="#F43F5E")

    left, right = st.columns(2)
    with left:
        trend = tx.assign(day=tx["txn_timestamp"].dt.date).groupby("day", as_index=False).agg(transactions=("txn_id", "count"), value=("amount", "sum"))
        chart(px.line(trend, x="day", y="transactions", title="Daily transaction volume", markers=True, color_discrete_sequence=["#06B6D4"]))
    with right:
        status = tx.groupby("status_clean", as_index=False).size().rename(columns={"size": "count"})
        chart(px.bar(status, x="status_clean", y="count", color="status_clean", title="Transaction status", color_discrete_map={"SUCCESS": "#10B981", "FAILED": "#F43F5E", "PENDING": "#F59E0B"}))

    category = tx.groupby("merchant_category_final", as_index=False).agg(transactions=("txn_id", "nunique"), value=("amount", "sum"))
    category = category.sort_values("value", ascending=False)
    chart(px.bar(category, x="merchant_category_final", y="value", title="Transaction value by merchant category", labels={"merchant_category_final": "Merchant category", "value": "Transaction value"}, color="merchant_category_final", color_discrete_sequence=COLORS))
    cb_category = matched_cb.groupby("merchant_category_final", as_index=False).agg(disputed_transactions=("txn_id", "nunique"), disputed_value=("disputed_amount_clean", "sum"))
    category_risk = category.merge(cb_category, on="merchant_category_final", how="left").fillna(0)
    category_risk["chargeback_ratio"] = category_risk["disputed_transactions"] / category_risk["transactions"]
    left, right = st.columns(2)
    with left:
        chart(px.area(trend, x="day", y="value", title="Daily transaction value", labels={"value": "Transaction value", "day": "Date"}, color_discrete_sequence=["#818CF8"]))
    with right:
        chart(px.bar(category_risk.sort_values("chargeback_ratio", ascending=False), x="merchant_category_final", y="chargeback_ratio", color="chargeback_ratio", color_continuous_scale=[[0, "#06B6D4"], [0.5, "#F59E0B"], [1, "#F43F5E"]], title="Category chargeback exposure", labels={"merchant_category_final": "Merchant category", "chargeback_ratio": "Chargeback ratio"}))

elif page == "Fraud & Risk":
    section_heading("Fraud & risk analytics", "Prioritise operational exceptions and the chargeback signals that deserve review.")
    high_risk = tx[tx["risk_segment_clean"].isin(["HIGH", "UNKNOWN"])]
    high_severity = matched_cb[matched_cb["severity_clean"].isin(["HIGH", "CRITICAL"])]
    a, b, c, d = st.columns(4)
    with a: metric_card("High / unknown risk", f"{len(high_risk):,}", accent="#F43F5E")
    with b: metric_card("Invalid / missing UTR", f"{int(tx['utr_missing_or_invalid'].sum()):,}", accent="#F59E0B")
    with c: metric_card("KYC mismatch", f"{int((~tx['has_kyc_match']).sum()):,}", accent="#A855F7")
    with d: metric_card("High / critical chargebacks", f"{len(high_severity):,}", accent="#FB7185")
    left, right = st.columns(2)
    with left:
        risk_status = tx.groupby(["risk_segment_clean", "status_clean"], dropna=False).size().reset_index(name="count")
        chart(px.bar(risk_status, x="risk_segment_clean", y="count", color="status_clean", barmode="stack", title="Transaction status by risk segment", color_discrete_map={"SUCCESS": "#10B981", "FAILED": "#F43F5E", "PENDING": "#F59E0B"}))
    with right:
        severity = matched_cb.groupby("severity_clean", as_index=False).size().rename(columns={"size": "count"})
        chart(px.bar(severity, x="severity_clean", y="count", color="severity_clean", title="Chargebacks by severity", color_discrete_map={"LOW": "#10B981", "MEDIUM": "#F59E0B", "HIGH": "#F43F5E", "CRITICAL": "#E11D48"}))
    reasons = matched_cb.groupby("reason_code_clean", as_index=False).agg(complaints=("complaint_id", "count"), disputed_amount=("disputed_amount_clean", "sum")).sort_values("complaints", ascending=False)
    chart(px.bar(reasons, x="reason_code_clean", y="complaints", color="disputed_amount", color_continuous_scale=[[0, "#818CF8"], [0.5, "#F59E0B"], [1, "#F43F5E"]], title="Chargeback reasons and disputed value"))
    exceptions = pd.DataFrame({
        "Exception": ["KYC mismatch", "Merchant mismatch", "Invalid / missing UTR", "Negative amount"],
        "Transactions": [int((~tx["has_kyc_match"]).sum()), int((~tx["has_merchant_match"]).sum()), int(tx["utr_missing_or_invalid"].sum()), int(tx["amount_was_negative"].sum())],
    })
    chart(px.bar(exceptions, x="Exception", y="Transactions", color="Exception", color_discrete_sequence=["#F43F5E", "#F59E0B", "#818CF8", "#A855F7"], title="Operational exception mix"))
    risk_landscape = tx.groupby(["risk_segment_clean", "merchant_category_final"], dropna=False, as_index=False).agg(
        transactions=("txn_id", "nunique"),
        average_amount=("amount", "mean"),
        invalid_utr_rate=("utr_missing_or_invalid", "mean"),
    )
    risk_landscape["risk_segment_clean"] = risk_landscape["risk_segment_clean"].fillna("Unmatched")
    chart(px.scatter_3d(
        risk_landscape, x="transactions", y="average_amount", z="invalid_utr_rate",
        color="risk_segment_clean", size="transactions", hover_name="merchant_category_final",
        size_max=42, title="3D risk exception landscape",
        labels={"average_amount": "Average transaction amount", "invalid_utr_rate": "Invalid UTR rate", "transactions": "Transactions"},
        color_discrete_map={"LOW": "#10B981", "MEDIUM": "#F59E0B", "HIGH": "#F43F5E", "UNKNOWN": "#A855F7", "Unmatched": "#64748B"}
    ))
    st.subheader("Risk review queue")
    st.dataframe(high_risk[["txn_id", "user_id", "merchant_id", "amount", "txn_timestamp", "status_clean", "kyc_status_clean", "risk_segment_clean", "utr_missing_or_invalid"]].sort_values("amount", ascending=False), use_container_width=True, hide_index=True)

elif page == "Merchant Analytics":
    section_heading("Merchant analytics", "Compare merchant volume, dispute exposure, and concentration of risk.")
    merchant_summary = tx.groupby("merchant_id", as_index=False).agg(transactions=("txn_id", "nunique"), transaction_value=("amount", "sum"), avg_ticket=("amount", "mean"))
    cb_by_merchant = matched_cb.groupby("merchant_id", as_index=False).agg(chargebacks=("complaint_id", "count"), disputed_value=("disputed_amount_clean", "sum"), disputed_txns=("txn_id", "nunique"))
    merchant_summary = merchant_summary.merge(cb_by_merchant, on="merchant_id", how="left").fillna({"chargebacks": 0, "disputed_value": 0, "disputed_txns": 0})
    merchant_summary["chargeback_ratio"] = merchant_summary["disputed_txns"] / merchant_summary["transactions"]
    merchant_summary = merchant_summary.merge(merchants[["merchant_id", "merchant_name", "merchant_category_clean", "merchant_status_clean", "business_type_clean"]], on="merchant_id", how="left")
    a, b, c, d = st.columns(4)
    with a: metric_card("Merchants in view", f"{tx['merchant_id'].nunique():,}", accent="#06B6D4")
    with b: metric_card("Matched merchants", f"{int(tx['has_merchant_match'].sum()):,}", accent="#10B981")
    with c: metric_card("Merchant match rate", f"{tx['has_merchant_match'].mean():.1%}" if len(tx) else "0.0%", accent="#38BDF8")
    with d: metric_card("Merchant disputed value", money(matched_cb["disputed_amount_clean"].sum()), accent="#F43F5E")
    cat = tx.groupby("merchant_category_final", as_index=False).agg(transactions=("txn_id", "nunique"), transaction_value=("amount", "sum"))
    cb_cat = matched_cb.groupby("merchant_category_final", as_index=False).agg(disputed_transactions=("txn_id", "nunique"), chargebacks=("complaint_id", "count"))
    cat = cat.merge(cb_cat, on="merchant_category_final", how="left").fillna(0)
    cat["chargeback_ratio"] = cat["disputed_transactions"] / cat["transactions"]
    chart(px.bar(cat.sort_values("chargeback_ratio", ascending=False), x="merchant_category_final", y="chargeback_ratio", color="chargeback_ratio", color_continuous_scale=[[0, "#06B6D4"], [0.5, "#F59E0B"], [1, "#F43F5E"]], title="Chargeback-to-transaction ratio by merchant category", labels={"merchant_category_final": "Merchant category", "chargeback_ratio": "Ratio"}))
    scatter = merchant_summary[merchant_summary["transactions"] > 0].copy()
    scatter["merchant_label"] = scatter["merchant_name"].fillna(scatter["merchant_id"])
    chart(px.scatter(scatter, x="transactions", y="chargeback_ratio", size="transaction_value", color="merchant_status_clean", hover_name="merchant_label", size_max=46, title="Merchant volume versus chargeback exposure", labels={"chargeback_ratio": "Chargeback ratio", "transactions": "Transactions"}, color_discrete_map={"ACTIVE": "#10B981", "SUSPENDED": "#F43F5E", "PENDING_KYC": "#F59E0B", "INACTIVE": "#64748B"}))
    chart(px.scatter_3d(
        scatter, x="transactions", y="avg_ticket", z="chargeback_ratio", size="transaction_value",
        color="merchant_status_clean", hover_name="merchant_label", size_max=42,
        title="3D merchant exposure map",
        labels={"transactions": "Transactions", "avg_ticket": "Average ticket", "chargeback_ratio": "Chargeback ratio"},
        color_discrete_map={"ACTIVE": "#10B981", "SUSPENDED": "#F43F5E", "PENDING_KYC": "#F59E0B", "INACTIVE": "#64748B"}
    ))
    st.subheader("Merchant exposure leaderboard")
    st.dataframe(merchant_summary.sort_values(["chargeback_ratio", "disputed_value"], ascending=False), use_container_width=True, hide_index=True, column_config={"chargeback_ratio": st.column_config.NumberColumn("Chargeback ratio", format="%.2%%"), "transaction_value": st.column_config.NumberColumn("Transaction value", format="₹%.0f"), "disputed_value": st.column_config.NumberColumn("Disputed value", format="₹%.0f"), "avg_ticket": st.column_config.NumberColumn("Avg ticket", format="₹%.0f")})

elif page == "Chargeback Analytics":
    section_heading("Chargeback analytics", "Track dispute inflow, resolution progress, and the drivers behind customer complaints.")
    a, b, c, d, e = st.columns(5)
    resolved = matched_cb["resolution_status_clean"].isin(["RESOLVED", "CLOSED"]).mean() if len(matched_cb) else 0
    with a: metric_card("Chargeback complaints", f"{len(matched_cb):,}", accent="#F59E0B")
    with b: metric_card("Distinct disputed transactions", f"{matched_cb['txn_id'].nunique():,}", accent="#F43F5E")
    with c: metric_card("Disputed amount", money(matched_cb["disputed_amount_clean"].sum()), accent="#FB7185")
    with d: metric_card("Resolution rate", f"{resolved:.1%}", accent="#10B981")
    with e: metric_card("Avg. report delay", f"{matched_cb['report_delay_days'].mean():.1f} days" if len(matched_cb) else "—", accent="#818CF8")
    left, right = st.columns(2)
    with left:
        reported = matched_cb.dropna(subset=["reported_timestamp_clean"]).assign(day=lambda x: x["reported_timestamp_clean"].dt.date).groupby("day", as_index=False).size().rename(columns={"size": "complaints"})
        chart(px.line(reported, x="day", y="complaints", title="Chargebacks reported over time", markers=True, color_discrete_sequence=["#F43F5E"]))
    with right:
        resolution = matched_cb.groupby("resolution_status_clean", as_index=False).size().rename(columns={"size": "complaints"})
        chart(px.pie(resolution, names="resolution_status_clean", values="complaints", title="Resolution status", color="resolution_status_clean", color_discrete_map={"RESOLVED": "#10B981", "CLOSED": "#34D399", "UNDER_REVIEW": "#F59E0B", "PENDING_MERCHANT": "#38BDF8", "REJECTED": "#F43F5E"}))
    left, right = st.columns(2)
    with left:
        channel = matched_cb.groupby("channel_clean", as_index=False).agg(complaints=("complaint_id", "count"), disputed_value=("disputed_amount_clean", "sum"))
        chart(px.bar(channel.sort_values("complaints", ascending=False), x="channel_clean", y="complaints", color="disputed_value", color_continuous_scale=[[0, "#06B6D4"], [0.5, "#818CF8"], [1, "#F43F5E"]], title="Complaint intake channel"))
    with right:
        category_cb = matched_cb.groupby("merchant_category_final", as_index=False).agg(complaints=("complaint_id", "count"), disputed_value=("disputed_amount_clean", "sum"))
        chart(px.treemap(category_cb, path=["merchant_category_final"], values="disputed_value", color="complaints", color_continuous_scale=[[0, "#38BDF8"], [0.5, "#818CF8"], [1, "#F43F5E"]], title="Disputed value by merchant category"))
    st.subheader("Chargeback case register")
    st.dataframe(matched_cb[["complaint_id", "txn_id", "merchant_id", "disputed_amount_clean", "reported_timestamp_clean", "resolution_status_clean", "severity_clean", "reason_code_clean", "channel_clean", "report_delay_days"]].sort_values("reported_timestamp_clean", ascending=False), use_container_width=True, hide_index=True)

    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

st.caption("Source: supplied cleaned customer, merchant, transaction, and chargeback CSV datasets. Filters apply to transactions; chargebacks shown are linked to the filtered transaction set.")
