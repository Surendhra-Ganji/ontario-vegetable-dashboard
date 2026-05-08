from __future__ import annotations
import os
from pathlib import Path
from datetime import datetime

import requests
import streamlit as st
import pandas as pd
import plotly.express as px

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
FEEDBACK_DIR = Path("data/feedback")
FEEDBACK_FILE = FEEDBACK_DIR / "feedback.csv"

st.set_page_config(page_title="Ontario Vegetable Dashboard", layout="wide")

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 0.7rem;
        padding-bottom: 0.8rem;
        max-width: 1460px;
    }

    .kpi-title {
        font-size: 1.02rem;
        font-weight: 700;
        margin-bottom: 0.45rem;
    }

    .kpi-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.6rem 0.75rem;
        min-height: 82px;
    }

    .kpi-label {
        font-size: 0.78rem;
        color: #64748b;
        margin-bottom: 0.12rem;
    }

    .kpi-value {
        font-size: 0.98rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.18;
    }

    .hint-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 0.75rem 0.9rem;
        border-radius: 12px;
        margin-bottom: 0.7rem;
    }

    .small-note {
        color: #64748b;
        font-size: 0.86rem;
    }

    .ai-answer-card {
    background: linear-gradient(135deg, #0f172a, #14532d);
    color: white;
    padding: 1rem 1.1rem;
    border-radius: 14px;
    margin-top: 0.4rem;
    font-size: 0.96rem;
    line-height: 1.5;
    white-space: normal;
    word-break: break-word;
    overflow-wrap: anywhere;
    width: 100%;
}

.bullet-chip {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 10px;
    padding: 0.5rem 0.65rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    min-height: 58px;
}

.confidence-box {
    background: rgba(255,255,255,0.10);
    border-left: 4px solid rgba(255,255,255,0.85);
    padding: 0.55rem 0.75rem;
    border-radius: 8px;
    margin-top: 0.2rem;
}

    .insight-title {
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }

    .section-title {
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }

    .bullet-chip {
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 10px;
        padding: 0.45rem 0.6rem;
        margin-bottom: 0.45rem;
        font-size: 0.9rem;
    }

    .user-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.8rem;
    }

    .confidence-box {
        background: rgba(255,255,255,0.10);
        border-left: 4px solid rgba(255,255,255,0.85);
        padding: 0.55rem 0.75rem;
        border-radius: 8px;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_get(path: str, params: dict | None = None):
    r = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def api_post(path: str, payload: dict | None = None):
    r = requests.post(f"{API_BASE_URL}{path}", json=payload or {}, timeout=180)
    r.raise_for_status()
    return r.json()


def build_year_slider(label: str, min_year: int, max_year: int, key: str, default_window: int = 10):
    min_year = int(min_year)
    max_year = int(max_year)

    if min_year >= max_year:
        st.info(f"Only one year is currently available: {max_year}")
        return (min_year, max_year)

    default_start = max(min_year, max_year - (default_window - 1))
    return st.slider(
        label,
        min_value=min_year,
        max_value=max_year,
        value=(default_start, max_year),
        key=key,
    )


def safe_get_available_vegetables(all_vegetables: list[dict], kpi_df: pd.DataFrame) -> list[dict]:
    if kpi_df.empty or "dataset_id" not in kpi_df.columns:
        return []
    loaded_ids = set(kpi_df["dataset_id"].astype(str).tolist())
    return [v for v in all_vegetables if v["id"] in loaded_ids]


def get_global_year_bounds(available_ids: list[str]) -> tuple[int, int]:
    mins = []
    maxs = []

    for veg_id in available_ids:
        try:
            detail = api_get(f"/vegetables/{veg_id}")
            if detail.get("min_year") is not None:
                mins.append(int(detail["min_year"]))
            if detail.get("max_year") is not None:
                maxs.append(int(detail["max_year"]))
        except Exception:
            continue

    if mins and maxs:
        return min(mins), max(maxs)

    return 1975, 2025


def format_ai_answer(answer: str):
    text = (answer or "").strip()
    if not text:
        return "", [], "", "", ""

    sections = {
        "summary": "",
        "key_insights": [],
        "likely_explanation": "",
        "confidence": "",
        "recommendation": "",
    }

    current_section = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        low = line.lower().rstrip(":")

        if low == "summary":
            current_section = "summary"
            continue
        elif low == "key insights":
            current_section = "key_insights"
            continue
        elif low == "likely explanation":
            current_section = "likely_explanation"
            continue
        elif low == "confidence":
            current_section = "confidence"
            continue
        elif low == "recommendation":
            current_section = "recommendation"
            continue

        if current_section == "key_insights":
            if line.startswith("-") or line.startswith("•") or line.startswith("*"):
                sections["key_insights"].append(line.lstrip("-•* ").strip())
            else:
                sections["key_insights"].append(line)
        elif current_section in sections:
            if sections[current_section]:
                sections[current_section] += " " + line
            else:
                sections[current_section] = line
        else:
            if not sections["summary"]:
                sections["summary"] = line

    return (
        sections["summary"],
        sections["key_insights"],
        sections["likely_explanation"],
        sections["confidence"],
        sections["recommendation"],
    )


def render_ai_answer(answer: str):
    summary, bullets, explanation, confidence, recommendation = format_ai_answer(answer)

    st.markdown("<div class='ai-answer-card'>", unsafe_allow_html=True)

    if summary:
        st.markdown("**Summary**")
        st.markdown(summary)

    if bullets:
        st.markdown("**Key Insights**")
        cols = st.columns(3)
        for i, item in enumerate(bullets):
            with cols[i % 3]:
                st.markdown(
                    f"<div class='bullet-chip'>• {item}</div>",
                    unsafe_allow_html=True,
                )

    lower_left, lower_mid, lower_right = st.columns([1.3, 1, 1])

    with lower_left:
        if explanation:
            st.markdown("**Likely Explanation**")
            st.markdown(explanation)

    with lower_mid:
        if confidence:
            st.markdown("**Confidence**")
            st.markdown(
                f"<div class='confidence-box'>{confidence}</div>",
                unsafe_allow_html=True,
            )

    with lower_right:
        if recommendation:
            st.markdown("**Recommendation**")
            st.markdown(recommendation)

    st.markdown("</div>", unsafe_allow_html=True)

def save_feedback(name: str, email: str, feedback_type: str, crop: str, rating: int, comments: str):
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)

    row = pd.DataFrame(
        [
            {
                "submitted_at": datetime.now().isoformat(timespec="seconds"),
                "name": name.strip(),
                "email": email.strip(),
                "feedback_type": feedback_type,
                "crop": crop,
                "rating": rating,
                "comments": comments.strip(),
            }
        ]
    )

    if FEEDBACK_FILE.exists():
        existing = pd.read_csv(FEEDBACK_FILE)
        combined = pd.concat([existing, row], ignore_index=True)
    else:
        combined = row

    combined.to_csv(FEEDBACK_FILE, index=False)


st.caption("Live Ontario Open Data ETL + FAISS RAG + Groq/OpenAI chat")

with st.sidebar:
    st.header("Access")
    username = st.text_input("Username", value="admin")
    password = st.text_input("Password", value="ChangeMe123!", type="password")

    if st.button("Login"):
        try:
            api_post("/auth/login", {"username": username, "password": password})
            st.success("Login successful")
        except Exception as exc:
            st.error(f"Login failed: {exc}")

    st.divider()
    st.subheader("AI Status")
    try:
        st.json(api_get("/ai/status"))
    except Exception as exc:
        st.error(f"AI status failed: {exc}")


try:
    veg_resp = api_get("/vegetables")
    kpi_resp = api_get("/vegetables/kpis")
except Exception as exc:
    st.error(f"Could not load backend data: {exc}")
    st.stop()

all_vegetables = veg_resp["vegetables"]
kpis = pd.DataFrame(kpi_resp["kpis"])
available_vegetables = safe_get_available_vegetables(all_vegetables, kpis)

if not available_vegetables:
    st.error("No successfully loaded vegetable datasets are available.")
    st.stop()

name_by_id = {d["id"]: d.get("display_name", d["name"]) for d in available_vegetables}
veg_ids = [d["id"] for d in available_vegetables]
display_names = [name_by_id[x] for x in veg_ids]

global_year_min, global_year_max = get_global_year_bounds(veg_ids)

st.markdown("<div class='kpi-title'>Key Information</div>", unsafe_allow_html=True)

latest_year = int(kpis["year"].max()) if not kpis.empty else global_year_max
top_prod = kpis.sort_values("production", ascending=False).iloc[0] if not kpis.empty else None
top_price = kpis.sort_values("price", ascending=False).iloc[0] if not kpis.empty else None
top_yield = kpis.sort_values("yield", ascending=False).iloc[0] if not kpis.empty else None
top_mover = kpis.sort_values("production_delta_pct", ascending=False).iloc[0] if not kpis.empty else None

c1, c2, c3, c4, c5 = st.columns(5)

c1.markdown(
    f"""
    <div class="kpi-card">
        <div class="kpi-label">📅 Latest Year</div>
        <div class="kpi-value">{latest_year}</div>
    </div>
    """,
    unsafe_allow_html=True,
)
c2.markdown(
    f"""
    <div class="kpi-card">
        <div class="kpi-label">📦 Production Leader</div>
        <div class="kpi-value">{top_prod['vegetable'] if top_prod is not None else '-'}<br><span style='font-size:0.88rem;font-weight:600'>{top_prod['production']:,.0f}</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)
c3.markdown(
    f"""
    <div class="kpi-card">
        <div class="kpi-label">💲 Highest Price</div>
        <div class="kpi-value">{top_price['vegetable'] if top_price is not None else '-'}<br><span style='font-size:0.88rem;font-weight:600'>{top_price['price']:.2f} cents/lb</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)
c4.markdown(
    f"""
    <div class="kpi-card">
        <div class="kpi-label">🌾 Highest Yield</div>
        <div class="kpi-value">{top_yield['vegetable'] if top_yield is not None else '-'}<br><span style='font-size:0.88rem;font-weight:600'>{top_yield['yield']:,.0f} lbs/acre</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)
c5.markdown(
    f"""
    <div class="kpi-card">
        <div class="kpi-label">↗ Strongest YoY Move</div>
        <div class="kpi-value">{top_mover['vegetable'] if top_mover is not None else '-'}<br><span style='font-size:0.88rem;font-weight:600'>{top_mover['production_delta_pct']:+.2f}%</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

tabs = st.tabs(["Crops Production Analysis", "Detail View", "User Page"])

with tabs[0]:
    st.markdown("<div class='section-title'>Crops Production Analysis</div>", unsafe_allow_html=True)

    # -----------------------------
    # Top row: filters left, ask box right
    # -----------------------------
    left_col, right_col = st.columns([1.55, 1], gap="large")

    with left_col:
        filter_col1, filter_col2 = st.columns([1.15, 1])

        with filter_col1:
            selected_compare = st.multiselect(
                "Choose vegetables",
                veg_ids,
                default=veg_ids[: min(6, len(veg_ids))],
                format_func=lambda x: name_by_id.get(x, x),
                key="selected_compare",
            )

        with filter_col2:
            compare_metric = st.selectbox(
                "Comparison metric",
                ["production", "price", "yield", "farm_value", "area"],
                index=1,
                format_func=lambda x: x.replace("_", " ").title(),
                key="compare_metric",
            )

        year_range = build_year_slider(
            "Year range",
            global_year_min,
            global_year_max,
            "comparison_year_range",
            default_window=10,
        )

        run_analysis = st.button("Run analysis", key="run_analysis_btn")

    with right_col:
        st.markdown("<div class='section-title'>AI Assistant</div>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="hint-card">
                <div class="small-note">Try questions like</div>
                <div>
                    • Why was dry onion production low in 2020?<br>
                    • Why were carrot prices high in 2024?<br>
                    • Summarize sweet corn trends in the last 10 years<br>
                    • Compare the selected vegetables by price
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        user_q = st.text_area(
            "Ask about the data",
            value="",
            height=140,
            placeholder=(
                "Why were prices high for sweet corn in recent years?\n"
                "Summarize the latest trends for the selected vegetables.\n"
                "Compare carrot and dry onion production over the last 10 years."
            ),
            key="ai_question",
        )

        ask_ai = st.button("Ask AI", use_container_width=True, key="ask_ai_btn")

    # -----------------------------
    # Full-width chart row
    # -----------------------------
    chart_result = None
    chart_error = None

    if run_analysis:
        if not selected_compare:
            chart_error = "Please choose at least one vegetable."
        else:
            try:
                result = api_get(
                    "/vegetables/compare",
                    {
                        "dataset_ids": ",".join(selected_compare),
                        "metric": compare_metric,
                        "year_start": year_range[0],
                        "year_end": year_range[1],
                    },
                )
                chart_result = result
            except requests.HTTPError as exc:
                try:
                    detail = exc.response.json()
                except Exception:
                    detail = {"detail": str(exc)}
                chart_error = f"Comparison failed. Backend response: {detail}"
            except Exception as exc:
                chart_error = f"Comparison failed: {exc}"

    if chart_error:
        st.error(chart_error)

    if chart_result:
        comp_df = pd.DataFrame(chart_result["valid_rows"])

        if not comp_df.empty:
            comp_df = comp_df.sort_values(["vegetable", "Year"])

            fig = px.line(
                comp_df,
                x="Year",
                y=chart_result["comparison_metric_label"],
                color="vegetable",
                markers=True,
                title=f"{chart_result['comparison_metric_label']} ({year_range[0]}–{year_range[1]})",
            )
            fig.update_traces(connectgaps=True)
            fig.update_layout(
                margin=dict(l=8, r=8, t=42, b=8),
                legend_title_text="Vegetable",
                height=320,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No comparison rows returned for the selected filters.")

        if chart_result.get("skipped_datasets"):
            with st.expander("Skipped vegetables", expanded=False):
                st.dataframe(pd.DataFrame(chart_result["skipped_datasets"]), use_container_width=True)

    # -----------------------------
    # Full-width AI output row BELOW graph
    # -----------------------------
    ai_result = None
    ai_error = None

    if ask_ai:
        if not user_q.strip():
            ai_error = "Please enter a question."
        else:
            try:
                selected_names = [name_by_id.get(x, x) for x in st.session_state.get("selected_compare", [])]
                compare_metric_val = st.session_state.get("compare_metric", "price")
                selected_year_range = st.session_state.get(
                    "comparison_year_range", (global_year_min, global_year_max)
                )

                context_suffix = ""
                if selected_names:
                    context_suffix += f"\nFocus vegetables: {', '.join(selected_names)}."
                if selected_year_range:
                    context_suffix += f"\nFocus years: {selected_year_range[0]} to {selected_year_range[1]}."
                if compare_metric_val:
                    context_suffix += f"\nFocus metric: {compare_metric_val}."

                final_question = user_q.strip() + context_suffix

                ai_result = api_post("/chat/rag", {"question": final_question, "dataset_id": None})

            except requests.HTTPError as exc:
                try:
                    detail = exc.response.json()
                except Exception:
                    detail = {"detail": str(exc)}
                ai_error = f"Ask AI failed: {detail}"
            except Exception as exc:
                ai_error = f"Ask AI failed: {exc}"

    if ai_error:
        st.error(ai_error)

    if ai_result:
        st.markdown("### AI Summary")
        render_ai_answer(ai_result["answer"])

with tabs[1]:
    st.markdown("<div class='section-title'>Detail View</div>", unsafe_allow_html=True)

    selected_id = st.selectbox(
        "Choose vegetable",
        veg_ids,
        format_func=lambda x: name_by_id.get(x, x),
        key="detail_selected_id",
    )

    try:
        print(f"Fetching detail for dataset_id: {selected_id}")
        detail = api_get(f"/vegetables/{selected_id}")
        df = pd.DataFrame(detail["rows"]).sort_values("Year")
        metric_map = detail["metrics"]

        metric_key = st.selectbox(
            "Metric",
            list(metric_map.keys()),
            index=0,
            format_func=lambda x: x.replace("_", " ").title(),
            key="detail_metric",
        )

        metric_label = metric_map[metric_key]

        dmin = int(detail["min_year"]) if detail.get("min_year") is not None else global_year_min
        dmax = int(detail["max_year"]) if detail.get("max_year") is not None else global_year_max

        detail_year_range = build_year_slider(
            "Viewer year range",
            dmin,
            dmax,
            "viewer_year_range",
            default_window=10,
        )

        filtered = df[
            (df["Year"] >= detail_year_range[0]) &
            (df["Year"] <= detail_year_range[1])
        ].copy()

        if not filtered.empty and metric_label in filtered.columns:
            fig = px.line(
                filtered,
                x="Year",
                y=metric_label,
                markers=True,
                title=f"{name_by_id[selected_id]} — {metric_label} ({detail_year_range[0]}–{detail_year_range[1]})",
            )
            fig.update_traces(connectgaps=True)
            fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for the selected metric and year range.")

        with st.expander("Show detail rows", expanded=False):
            clean_cols = [c for c in filtered.columns if c not in ["Dataset", "dataset_id"]]
            st.dataframe(filtered[clean_cols], use_container_width=True)

    except requests.HTTPError as exc:
        try:
            detail = exc.response.json()
        except Exception:
            detail = {"detail": str(exc)}
        st.error(f"Detail view failed. Backend response: {detail}")
    except Exception as exc:
        st.error(f"Detail view failed: {exc}")

with tabs[2]:
    st.markdown("<div class='section-title'>User Page</div>", unsafe_allow_html=True)

    left, right = st.columns([1.2, 1], gap="large")

    with left:
        st.markdown(
            """
            <div class="user-card">
                <strong>We'd love your feedback</strong><br>
                Help us improve this dashboard by sharing what worked, what felt confusing, and what crops or features you want next.
            </div>
            """,
            unsafe_allow_html=True,
        )

        user_name = st.text_input("Your name", key="feedback_name")
        user_email = st.text_input("Email (optional)", key="feedback_email")
        feedback_type = st.selectbox(
            "Feedback type",
            ["General feedback", "Bug report", "Feature request", "Data issue", "UI suggestion"],
            key="feedback_type",
        )
        selected_crop = st.selectbox(
            "Related crop (optional)",
            ["None"] + display_names,
            key="feedback_crop",
        )
        rating = st.slider("Dashboard rating", 1, 5, 4, key="feedback_rating")
        comments = st.text_area(
            "Your feedback",
            height=140,
            placeholder="Tell us what you liked, what was confusing, and what you want improved.",
            key="feedback_comments",
        )

        if st.button("Submit feedback", key="submit_feedback"):
            if not comments.strip():
                st.warning("Please enter your feedback before submitting.")
            else:
                try:
                    save_feedback(
                        name=user_name,
                        email=user_email,
                        feedback_type=feedback_type,
                        crop=selected_crop,
                        rating=rating,
                        comments=comments,
                    )
                    st.success("Thank you — your feedback was saved.")
                except Exception as exc:
                    st.error(f"Could not save feedback: {exc}")

    with right:
        st.markdown(
            f"""
            <div class="user-card">
                <strong>Loaded crops</strong><br>
                {", ".join(display_names)}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="user-card">
                <strong>Current coverage</strong><br>
                • Available crops: {len(display_names)}<br>
                • Earliest year: {global_year_min}<br>
                • Latest year: {global_year_max}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if FEEDBACK_FILE.exists():
            try:
                feedback_df = pd.read_csv(FEEDBACK_FILE)
                st.markdown(
                    f"""
                    <div class="user-card">
                        <strong>Feedback received</strong><br>
                        {len(feedback_df)} response(s) collected so far.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            except Exception:
                pass