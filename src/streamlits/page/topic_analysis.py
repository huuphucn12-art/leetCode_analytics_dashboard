import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.utility.streamlit_utils import connection


@st.cache_data
def load_topic_mastery_data():
    df = pd.DataFrame(
        {
            "activity_year": pd.Series(dtype="int16"),
            "topic_name": pd.Series(dtype="string"),
        }
    )
    try:
        cursor = connection.cursor()
        query = f"""
            WITH cte_topic_analysis AS
            (
                SELECT 
                    year(sub_date) as activity_year,
                    topic_tag as topic_name,
                    COUNT(question_id) as total_submissions,
                    COUNT(DISTINCT CASE WHEN status_display = "Accepted" THEN question_id END) as total_solved,
                    ROUND(COUNT(CASE WHEN status_display = "Wrong Answer" THEN question_id END)*100.0 / total_submissions,2) as wa_rate,
                    ROUND(COUNT(CASE WHEN status_display = "Time Limit Exceeded" THEN question_id END)*100.0 / total_submissions,2) as tle_rate,
                    ROUND(COUNT(CASE WHEN status_display = "Memory Limit Exceeded" THEN question_id END)*100.0 / total_submissions,2) as mle_rate,
                    ROUND(COUNT(CASE WHEN status_display = "Runtime Error" THEN question_id END)*100.0 / total_submissions,2) as re_rate,

                    COUNT(DISTINCT CASE WHEN status_display = "Accepted" AND difficulty = "Easy" THEN question_id END) as easy_solved,
                    COUNT(DISTINCT CASE WHEN status_display = "Accepted" AND difficulty = "Medium" THEN question_id END) as medium_solved,
                    COUNT(DISTINCT CASE WHEN status_display = "Accepted" AND difficulty = "Hard" THEN question_id END) as hard_solved,
                    ROUND(total_solved*100.0 / total_submissions,2) AS acceptance_rate,
                    coalesce(ROUND(try_divide((easy_solved+2*medium_solved+3*hard_solved)*1.0, total_solved),2),0.0) AS avg_difficulty_score
                FROM mart_submission_topic
                WHERE topic_tag IS NOT NULL
                GROUP BY activity_year,topic_name
            )
            SELECT 
                activity_year,topic_name,
                total_solved,wa_rate,
                tle_rate,mle_rate,
                re_rate,total_submissions,
                avg_difficulty_score,acceptance_rate
            FROM cte_topic_analysis
            ORDER BY total_submissions DESC
        """
        cursor.execute(query)
        df = pd.DataFrame(
            cursor.fetchall(), columns=[desc[0] for desc in cursor.description]
        )
    except Exception as e:
        st.error(
            title="Get error while execute load_topic_mastery_data", icon="🚨", body=""
        )
    return df


@st.cache_data
def load_runtime_memory_topic_data():
    df = pd.DataFrame({"topic_name": pd.Series(dtype="string")})
    try:
        cursor = connection.cursor()
        query = """
            SELECT 
                sub_id as submission_id,
                question_title,
                topic_tag as topic_name, 
                runtime_ms,
                memory_mb
            FROM mart_submission_topic
            WHERE topic_tag is not NULL AND status_display = "Accepted"        
        """

        cursor.execute(query)
        df = pd.DataFrame(
            cursor.fetchall(), columns=[desc[0] for desc in cursor.description]
        )

    except Exception as e:
        st.error(
            title="Get error while execute load_runtime_memory_topic_data",
            icon="🚨",
            body="",
        )
    return df


def render_topic_radar_ac_rate_bubble(df):
    st.divider()
    col_radar, col_scatter = st.columns(2)

    with col_radar:
        with st.container(border=True):
            st.markdown("#### 🕸️ Topic Mastery Radar")
            st.caption("Solved volume by selected topics")

            if not df.empty:
                # Đóng vòng Radar (Nối điểm cuối về điểm đầu)
                categories = df["topic_name"].tolist()
                values = df["total_solved"].tolist()
                categories.append(categories[0])
                values.append(values[0])

                fig_radar = go.Figure(
                    data=go.Scatterpolar(
                        r=values, theta=categories, fill="toself", line_color="#26a641"
                    )
                )
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, showticklabels=False)),
                    showlegend=False,
                    margin=dict(t=20, b=20, l=20, r=20),
                    height=320,
                )
                st.plotly_chart(fig_radar, width="stretch")
            else:
                st.warning("No data")
    with col_scatter:
        with st.container(border=True):
            st.markdown("#### 🎯 Effort vs Success")
            st.caption("High-effort topics with accuracy rates")
            if not df.empty:
                fig_scatter = px.scatter(
                    df,
                    x="total_solved",
                    y="acceptance_rate",
                    text="topic_name",
                    size="total_submissions",
                    color="acceptance_rate",
                    color_continuous_scale="RdYlGn",
                    labels={
                        "total_solved": "Problem Solved",
                        "acceptance_rate": "Accepted Rated %",
                    },
                )
                fig_scatter.update_traces(
                    textposition="top center",
                    marker=dict(line=dict(width=1, color="DarkSlateGrey")),
                )
                fig_scatter.update_layout(height=320, margin=dict(t=20, b=20))
                st.plotly_chart(fig_scatter, width="stretch")
            else:
                st.warning("No data")


def render_topic_distribution_treemap_error_rate_stacked(df):
    st.divider()
    col_tree, col_error = st.columns(2)

    with col_tree:
        with st.container(border=True):
            st.markdown("#### 🧱 Topic Distribution (Treemap)")
            st.caption("Size: Practice Volume | Color: Average Difficulty")
            if not df.empty:
                fig_tree = px.treemap(
                    df,
                    path=[px.Constant("Topic Name"), "topic_name"],
                    values="total_solved",
                    color="avg_difficulty_score",
                    color_continuous_scale="Blues",
                    labels={"avg_difficulty_score": "Average Difficulty Score"},
                )
                fig_tree.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=350)
                st.plotly_chart(fig_tree, width="stretch")
            else:
                st.warning("No data")
    with col_error:
        with st.container(border=True):
            st.markdown("#### 🚨 Error Anatomy")
            st.caption("Error type distribution prior to acceptance.")
            if not df.empty:

                df_errors = df.melt(
                    id_vars=["topic_name"],
                    value_vars=["wa_rate", "tle_rate", "mle_rate", "re_rate"],
                    var_name="error_type",
                    value_name="rate",
                )

                error_map = {
                    "wa_rate": "Wrong Answer",
                    "tle_rate": "Time Limit",
                    "mle_rate": "Memory Limit",
                    "re_rate": "Runtime Error",
                }
                df_errors["error_type"] = df_errors["error_type"].map(error_map)

                fig_error = px.bar(
                    df_errors,
                    x="topic_name",
                    y="rate",
                    color="error_type",
                    barmode="stack",
                    color_discrete_map={
                        "Wrong Answer": "#ff375f",
                        "Time Limit": "#ffc01e",
                        "Memory Limit": "#8e44ad",
                        "Runtime Error": "#e67e22",
                    },
                    labels={
                        "topic_name": "Topic",
                        "rate": "Rate %",
                        "error_type": "Error Types",
                    },
                )
                fig_error.update_layout(
                    barmode="stack",
                    margin=dict(t=20, b=20),
                    height=350,
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                    ),
                )
                st.plotly_chart(fig_error, width="stretch")
            else:
                st.warning("No data")


def render_runtime_memory_topic_scatter(df_topic):
    st.divider()
    with st.container(border=True):
        st.markdown("#### ⚖️ Runtime vs Memory")
        st.caption("Runtime vs Memory Consumption across Paradigms & Data Structures")
        if not df_topic.empty:
            fig_scatter = px.scatter(
                df_topic,
                x="memory_mb",
                y="runtime_ms",
                color="topic_name",
                title="question_title",
                hover_data=["question_title"],
                opacity=0.7,
                labels={
                    "memory_mb": "Memory (MB) ",
                    "runtime_ms": "Runtime (ms) ",
                    "question_title": "Question ",
                },
            )
            fig_scatter.update_layout(
                height=350,
                margin=dict(t=20, b=20),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
            )
            st.plotly_chart(fig_scatter, width="stretch")
        else:
            st.warning("No data")


def render_topic_analysis_dashboard():
    # Load data
    df_gr_topic = load_topic_mastery_data()
    df_rm_topic = load_runtime_memory_topic_data()
    # Filter
    st.markdown("### 🧩 Topic Analysis Dashboard")
    st.caption("In-depth algorithmic proficiency diagnosis and error analysis by knowledge area")

    col_yr, col_mo = st.columns([1, 4])
    with col_yr:
        available_years = sorted(df_gr_topic["activity_year"].unique().tolist(), reverse=True)
        selected_year = st.selectbox("📅 Year:", options=available_years, key="selectbox_year_topic_analysis")

        df_gr_topic_yr = df_gr_topic[df_gr_topic["activity_year"] == selected_year]

    with col_mo:
        available_topics = df_gr_topic_yr["topic_name"].unique().tolist()
        default_topics = (available_topics[:5] if len(available_topics) >= 5 else available_topics)

        selected_topics = st.multiselect(
            "📌 Topics:",
            options=available_topics,
            default=default_topics,
            max_selections=6,
        )
        df_topic_yr_sl = df_gr_topic_yr[df_gr_topic_yr["topic_name"].isin(selected_topics)]
        df_rm_topic_sl = df_rm_topic[df_rm_topic["topic_name"].isin(selected_topics)]

    if not available_years or not available_topics:
        st.info("No data available")
        return
    if len(selected_topics) < 3:
        st.warning("⚠️ Please select at least 3 topics to optimize the chart display")
        return

    # Display
    render_topic_radar_ac_rate_bubble(df_topic_yr_sl)
    render_topic_distribution_treemap_error_rate_stacked(df_topic_yr_sl)
    render_runtime_memory_topic_scatter(df_rm_topic_sl)
