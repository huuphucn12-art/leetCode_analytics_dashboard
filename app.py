import streamlit as st
from src.streamlits.page import *
from src.utility.streamlit_utils import connection

st.set_page_config(
    page_title="LeetCode Analytics App",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    st.title("🚀 LeetCode Analytics Dashboard")
    tabs = st.tabs(["Overview", "Monthly performance", "Topic analysis"])
    with tabs[0]:
        render_overview()
    with tabs[1]:
        render_monthly_performance_dashboard()
    with tabs[2]:
        render_topic_analysis_dashboard()
    connection.close()


if __name__ == "__main__":
    main()
