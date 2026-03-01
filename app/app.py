import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ast
from collections import Counter
from pathlib import Path

st.set_page_config(page_title="Remote Job Market Pulse", layout="wide")

APP_DIR = Path(__file__).resolve().parent
DATA_PATH = APP_DIR.parent / "data" / "processed" / "data_clean.csv"

RUN_INFO_PATH = APP_DIR.parent / "data" / "processed" / "run_job_info.csv"
SCRAPE_RUNS_PATH = APP_DIR.parent / "data" / "meta" / "scrape_runs.csv"

@st.cache_data
def load_run_info():
    if not RUN_INFO_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(RUN_INFO_PATH, parse_dates=["scraped_at"])
    return df

@st.cache_data
def load_scrape_runs():
    return pd.read_csv(SCRAPE_RUNS_PATH, parse_dates=["started_at"])


@st.cache_data
def load_data(path: Path):
  # data\processed\data_clean2.csv
  if not path.exists():
    st.error(f"Data file not found:{path.resolve()}")
    st.stop()

  
  df = pd.read_csv(DATA_PATH)
  df['tags_list'] = df['tags'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else [])
  return df

df = load_data(DATA_PATH)

run_info = load_run_info()

if run_info.empty:
    new_jobs_last = 0
else:
    latest_run = run_info.sort_values("scraped_at").iloc[-1]
    value = latest_run.get("new_jobs", 0)

    if pd.isna(value):
        new_jobs_last = 0
    else:
        new_jobs_last = int(value)

# header and hottest family
hottest_family = df['job_family'].value_counts().idxmax()
hottest_count = df['job_family'].value_counts().max()

st.markdown(
    """
    <style>
    .section-box {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 18px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.25rem;
    }
    .kpi-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.035), rgba(255,255,255,0.015));
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 1rem 1.25rem;
    box-shadow: 0 6px 16px rgba(0,0,0,0.2);
    }

    .kpi-label {
        font-size: 0.75rem;
        letter-spacing: 0.02em;
        color: rgba(255,255,255,0.6);
    }

    .kpi-value {
        font-size: 1.9rem;
        font-weight: 700;
        line-height: 1.1;
    }

    .kpi-delta {
        display: inline-block;
        margin-top: 0.5rem;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        background-color: rgba(34,197,94,0.15);
        color: #4ade80;
        font-size: 0.75rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

from datetime import datetime, timezone

scrape_runs = load_scrape_runs()

# Ensure timezone-aware
scrape_runs["started_at"] = pd.to_datetime(
    scrape_runs["started_at"], utc=True
)

last_run_time = scrape_runs["started_at"].max()
now = datetime.now(timezone.utc)

delta = now - last_run_time
hours = int(delta.total_seconds() // 3600)
minutes = int(delta.total_seconds() // 60)

if hours > 24:
    freshness_text = f"Last scraped {delta.days} days ago"
elif hours > 0:
    freshness_text = f"Last scraped {hours} hours ago"
else:
    freshness_text = f"Last scraped {minutes} minutes ago"


col_title, col_fresh = st.columns([0.85, 0.15])

with col_title:
    st.markdown(
        """
        <h1 style="margin-bottom: 0.25rem;">Remote Job Market Pulse 2025</h1>
        <p style="color: rgba(255,255,255,0.6); margin-top: 0;">
            Real-time insights from global remote job postings
        </p>
        """,
        unsafe_allow_html=True,
    )

with col_fresh:
    st.markdown(
        f"""
        <div style="
            text-align: right;
            margin-top: 1.4rem;
            font-size: 0.75rem;
            color: rgba(255,255,255,0.55);
            line-height: 1.6;
        ">
            ⏱ {freshness_text}<br/>
            🗂 {len(scrape_runs)} runs · last status: {scrape_runs.iloc[-1]['status']}
        </div>
        """,
        unsafe_allow_html=True,
    )


col_h1, col_h2, col_h3, col_h4 = st.columns(4, gap="large")

with col_h1:
  st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Jobs Analyzed</div>
            <div class="kpi-value">{len(df):,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_h2:
  st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Hottest Job Family</div>
            <div class="kpi-value">{hottest_family}</div>
            <div class="kpi-delta">↑ {hottest_count} jobs</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_h3:
  global_pct = (df['location'].str.strip() == 'Remote').mean()*100
  st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Global Remote %</div>
            <div class="kpi-value">{global_pct:.1f}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  
with col_h4:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">New Jobs (Last Run)</div>
            <div class="kpi-value">{new_jobs_last}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown("---")
left, right = st.columns([0.55, 0.45], gap="large")

with left:
  
# Real-time search engine
  st.markdown("### 🔍 Skill-Specific Job Finder")
  st.caption("Search job listings by skill, role, or company")
  search_query = st.text_input(
    "Search jobs",
      label_visibility="collapsed",
      placeholder="Type skills or keywords (e.g., Python, AWS, React, Lead)",
  )

  if search_query:
    # Split by comma, strip whitespace, drop empties
    keywords = [
        kw.strip().lower()
        for kw in search_query.split(",")
        if kw.strip()
    ]

    def row_matches(row) -> bool:
        haystack = " ".join([
            str(row["tags"]),
            str(row["title"]),
            str(row["company"]),
        ]).lower()

        return any(kw in haystack for kw in keywords)

    filtered_df = df[df.apply(row_matches, axis=1)]

  else:
    filtered_df = df

  if search_query:
    st.caption(
        "Searching for: "
        + ", ".join(f"`{kw}`" for kw in keywords)
    )

  st.caption(f"{len(filtered_df):,} matching jobs")
  show_all = st.toggle(
    "Show all matching jobs",
    value=False,
    help="Toggle to view all results",
  )

  rows_to_show = len(filtered_df) if show_all else 3

  st.dataframe( filtered_df[ 
    ['title', 'company', 'location', 'job_family', 'url'] ].head(rows_to_show), 
               width = "stretch", 
        column_config={ "title": st.column_config.TextColumn("Role"), 
       "company": st.column_config.TextColumn("Company"), 
       "location": st.column_config.TextColumn("Location"), "job_family": st.column_config.TextColumn("Category"), 
       "url": st.column_config.LinkColumn( "Job Link", display_text="View posting ↗", ), 
       }, 
       hide_index=True, )
  

def get_radar_data(family):
    # Get top 8 skills for this specific family
    family_tags = df[df['job_family'] == family].explode('tags_list')
    tag_counts = family_tags['tags_list'].value_counts().head(8)
    return tag_counts

# Radar skill chart
with right:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <h3 style="margin: 0;">🎯 Skill DNA</h3>
            <span title="Relative skill composition derived from job postings"
                style="
                    font-size: 1.1rem;
                    color: rgba(255,255,255,0.55);
                    cursor: help;
                ">
                ℹ️
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


    selected_family = st.selectbox(
            "Job Family",
            df["job_family"].unique(),
            label_visibility="collapsed",
    )

    radar_stats = get_radar_data(selected_family)

    fig_radar = go.Figure()

    if radar_stats.empty:
        st.warning("No skill data available for this job family yet.")
    else:
        fig_radar.add_trace(
            go.Scatterpolar(
                r=radar_stats.values,
                theta=radar_stats.index,
                fill="toself",
                name=selected_family,
                line_color="#01674C",
            )
        )

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, radar_stats.max() + 5],
                )
            ),
            showlegend=False,
            title=f"Required Expertise: {selected_family}",
            height=300,
            margin=dict(l=30, r=30, t=50, b=30),
        )

    st.plotly_chart(
        fig_radar,
        width="stretch",
        key=f"radar_chart_{selected_family}"
    )


tab1, tab2, tab3 = st.tabs(["Skill Landscape", "Family Comparison", "Data History"])
with tab1:
  st.subheader("Top Skills in the Market")
  # Flatten all tags to find frequency
  all_tags = df.explode('tags_list')
  top_tags = all_tags['tags_list'].value_counts().head(30).reset_index()
  top_tags.columns = ['Skill', 'Frequency']

  top_tags['Dominant Family'] = top_tags['Skill'].apply(
      lambda s: all_tags[all_tags['tags_list'] == s]['job_family'].mode()[0]
  )

  fig_bubble = px.scatter(top_tags, x="Skill", y="Frequency",
                  size="Frequency", color="Dominant Family",
                  hover_name="Skill", size_max=60,
                  title="Top 30 Skills: Market Frequency vs. Primary Job Family")
  st.plotly_chart(fig_bubble, width = "stretch", key = "bubble_chart")

with tab2:
  
  st.subheader("Skill Importance by Job Family")

  TOP_SKILLS = 10

  # Explode skills
  exploded = df.explode("tags_list")
  top_skills = (
      exploded["tags_list"]
      .value_counts()
      .head(TOP_SKILLS)
      .index
  )

  filtered = exploded[exploded["tags_list"].isin(top_skills)]
  heatmap_df = (
      filtered
      .groupby(["job_family", "tags_list"])
      .size()
      .reset_index(name="count")
      .pivot(index="job_family", columns="tags_list", values="count")
      .fillna(0)
  )

  # Normalize per family (row-wise)
  heatmap_norm = heatmap_df.div(heatmap_df.max(axis=1), axis=0)

  fig = px.imshow(
      heatmap_norm,
      color_continuous_scale=[
          "#020617",  # near-black
          "#1e293b",
          "#0ea5e9",  # blue
          "#2522c5",  # green
      ],
      aspect="auto",
      labels=dict(
          x="Skill",
          y="Job Family",
          color="Relative Importance",
      ),
  )

  fig.update_layout(
      title="Skill Importance by Job Family",
      font=dict(size=12),
      title_font_size=18,
      xaxis_title=None,
      yaxis_title=None,
      coloraxis_colorbar=dict(
          title="Importance",
          tickformat=".0%",
      ),
      paper_bgcolor="rgba(0,0,0,0)",
      plot_bgcolor="rgba(0,0,0,0)",
  )

  fig.update_xaxes(side="top")
  fig.update_yaxes(tickfont=dict(size=11))

  st.plotly_chart(fig, width = "stretch", key = "heatmap_chart")

with tab3:
    st.subheader("Market Trends Over Time")

    st.caption("Total observed jobs vs newly appearing jobs per scrape run")

    fig = px.line(
        run_info,
        x="scraped_at",
        y=["total_jobs", "new_jobs"],
        markers=True,
    )

    fig.update_layout(
        height=320,
        xaxis_title="Scrape Time",
        yaxis_title="Jobs",
        legend_title_text="Metric",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, width = "stretch", key = "trend_chart")

st.caption(
    f"""
    Data health:
    • {len(scrape_runs)} scrape runs
    • Last run status: {scrape_runs.iloc[-1]['status']}
    """
)
