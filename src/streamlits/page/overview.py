import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from src.utility.streamlit_utils import connection

@st.cache_data
def load_topic_data():
    df = pd.DataFrame({'activity_year': pd.Series(dtype='int16')})
    try:
        with connection.cursor() as cursor:
            query="""
                SELECT 
                    YEAR(sub_date) as activity_year,
                    MONTH(sub_date) as activity_month,
                    topic_tag as topic_name,
                    SUM(CASE WHEN status_display = "Accepted" THEN 1 ELSE 0 END) AS solved_count
                FROM mart_submission_topic
                GROUP BY activity_year,activity_month,topic_tag
                HAVING topic_tag IS NOT NULL
                ORDER BY activity_year DESC,activity_month ASC, solved_count DESC
            """
            cursor.execute(query)
            df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
    except Exception as e:
        st.error(title="Get error while execute load_topic_data", icon="🚨", body="")
    return df

@st.cache_data
def load_error_data():
    df = pd.DataFrame({'activity_year': pd.Series(dtype='int16')})

    try:
        with connection.cursor() as cursor:
            query="""
                SELECT 
                    YEAR(sub_date) as activity_year,
                    difficulty,
                    SUM(CASE WHEN status_display='Accepted' THEN 1 ELSE 0 END) as total_accepted,
                    SUM(CASE WHEN status_display='Wrong Answer' THEN 1 ELSE 0 END) as wa_count,
                    SUM(CASE WHEN status_display='Time Limit Exceeded' THEN 1 ELSE 0 END) as tle_count,
                    SUM(CASE WHEN status_display='Runtime Error' THEN 1 ELSE 0 END) as re_count,
                    COUNT(*) AS total_submissions
                FROM mart_submission_difficulty
                GROUP BY activity_year, difficulty
                ORDER BY activity_year DESC, difficulty
            """

            cursor.execute(query)
            df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

    except Exception as e:
        st.error(title="Get error while execute load_error_data", icon="🚨", body="")
    return df
@st.cache_data
def load_overall_data():
    df = pd.DataFrame({'activity_year': pd.Series(dtype='int16'),})

    try:
        with connection.cursor() as cursor:
            query="""
                WITH cte_submission_information AS
                (
                    SELECT 
                        question_id,
                        sub_date,
                        status_display,
                        difficulty
                    FROM mart_submission_difficulty
                )
                ,cte_streak_information 
                (
                    SELECT 
                        sub_date,
                        gap,
                        COUNT(gap) OVER(PARTITION BY gap) as streak
                    FROM (
                        SELECT sub_date, unix_date(sub_date) - row_number()OVER(ORDER BY sub_date) as gap
                        FROM (SELECT DISTINCT sub_date FROM cte_submission_information WHERE status_display = "Accepted")
                    ) as t
                )
                ,cte_accept_difficulty 
                (
                    SELECT 
                        COUNT(DISTINCT CASE WHEN status_display = "Accepted" THEN question_id END) as total_solved,
                        COUNT(DISTINCT CASE WHEN status_display = "Accepted" AND difficulty = "Easy" THEN question_id END) as easy_solved,
                        COUNT(DISTINCT CASE WHEN status_display = "Accepted" AND difficulty = "Medium" THEN question_id END) as medium_solved,
                        COUNT(DISTINCT CASE WHEN status_display = "Accepted" AND difficulty = "Hard" THEN question_id END) as hard_solved
                    FROM cte_submission_information

                )
                ,cte_submit_overall 
                (
                    SELECT 

                        COUNT(question_id) as total_submissions,
                        COUNT(CASE WHEN status_display = "Accepted" THEN question_id END) as accepted_submissions,
                        COUNT(CASE WHEN difficulty = "Easy" THEN question_id END) as total_easy_question,
                        COUNT(CASE WHEN difficulty = "Medium" THEN question_id END) as total_medium_question,
                        COUNT(CASE WHEN difficulty = "Hard" THEN question_id END) as total_hard_question
                    FROM cte_submission_information
                )
                ,cte_current_streak
                (
                    SELECT 
                        coalesce(SUM(DISTINCT streak),0) as current_streak
                    FROM cte_streak_information 
                    WHERE sub_date IN (date_sub(GETDATE(),1), GETDATE()) 
                )
                ,cte_longest_streak
                (
                    SELECT MAX(streak) as longest_streak FROM cte_streak_information
                )
                ,cte_contest_participate
                (
                    SELECT COUNT(DISTINCT CASE WHEN status_display = "Accepted" THEN contest_id END) as contests_participated
                    FROM mart_submission_contest
                )
                ,cte_main_language 
                (
                    SELECT  
                        language
                    FROM dim_submission
                    GROUP BY language
                    ORDER BY COUNT(*) DESC
                    LIMIT 1
                )
                SELECT *
                FROM cte_accept_difficulty
                CROSS JOIN cte_submit_overall
                CROSS JOIN cte_current_streak
                CROSS JOIN cte_longest_streak
                CROSS JOIN cte_contest_participate
                CROSS JOIN cte_main_language
            """

            cursor.execute(query)
            df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

    except Exception as e:
        st.error(title="Get error while execute load_overall_data", icon="🚨", body="")
    return df
@st.cache_data
def load_submission_data():
    df = pd.DataFrame({'activity_year': pd.Series(dtype='int16')})

    try:
        with connection.cursor() as cursor:
            query = f"""
                SELECT 
                    YEAR(sub_date) as activity_year,
                    sub_date as activity_date,
                    COUNT(sub_date) as submission_count
                FROM mart_submission_difficulty
                GROUP BY activity_date
                ORDER BY activity_date 
            """
            cursor.execute(query)
            df_submission=pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

        # Generate full month in available_years then left join submission 
        df_submission['activity_date'] = pd.to_datetime(df_submission['activity_date'])  
        available_years = sorted(df_submission["activity_year"].unique().tolist(),reverse=True)
        date_range = pd.date_range(start=f"{available_years[-1]}-01-01", end = f"{available_years[0]}-12-31")
        df_date = pd.DataFrame({
            "activity_date": date_range,
            "activity_year": date_range.year
        })

        df = pd.merge(df_date,df_submission, on = ["activity_date","activity_year"], how = "left")

    except Exception as e:
        st.error(title="Get error while execute load_submission_data", icon="🚨", body="")
    return df

@st.cache_data
def load_difficulty_data():
    df = pd.DataFrame({'activity_year': pd.Series(dtype='int16')})

    try:
        with connection.cursor() as cursor:
            query="""
                SELECT 
                    YEAR(sub_date) as activity_year,
                    MONTH(sub_date) as activity_month,
                    difficulty,
                    SUM(CASE WHEN status_display = 'Accepted' THEN 1 ELSE 0 END) AS solved_count
                FROM mart_submission_difficulty
                GROUP BY activity_year,activity_month,difficulty
                ORDER BY activity_year DESC
            """

            cursor.execute(query)
            df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

    except Exception as e:
        st.error(title="Get error while execute load_difficulty_data", icon="🚨", body="")
    return df

@st.cache_data
def load_attempt_data():
    df = pd.DataFrame({'activity_year': pd.Series(dtype='int16')})

    try:
        with connection.cursor() as cursor:
            query="""
                SELECT 
                    YEAR(sub_date) as activity_year,
                    MONTH(sub_date) as activity_month,
                    ROUND(SUM(CASE WHEN status_display!= 'Accepted' THEN 1 ELSE 0 END)*1.0 /SUM(CASE WHEN status_display= 'Accepted' THEN 1 ELSE 0 END),2) as avg_failed_attempts
                FROM mart_submission_difficulty
                GROUP BY activity_year,activity_month
                ORDER BY activity_year,activity_month
            """

            cursor.execute(query)
            df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
    except Exception as e:
        st.error(title="Get error while execute load_attempt_data", icon="🚨", body="")
    return df

@st.cache_data
def load_contest_status_data():
    df = pd.DataFrame()
    try:
        cursor = connection.cursor()

        query = """
            WITH cte_contest_overall AS
            (
                SELECT 
                    contest_id,
                    CONCAT("Q",dense_rank() OVER(PARTITION BY contest_id ORDER BY credit,question_id)) question_level,
                    status_display
                FROM mart_submission_contest
            )
            SELECT 
                question_level,
                status_display,
                COUNT(*) as count,
                ROUND(count*100.0 / SUM(COUNT(*)) OVER(PARTITION BY question_level),2) AS percent
            FROM cte_contest_overall
            WHERE status_display IN ('Accepted','Wrong Answer','Time Limit Exceeded','Runtime Error')
            GROUP BY question_level,status_display
        """
        cursor.execute(query)
        df = pd.DataFrame(
            cursor.fetchall(), columns=[desc[0] for desc in cursor.description]
        )
    except Exception as e:
        st.error(
            title="Get error while execute load_contest_status_data", icon="🚨", body=""
        )
    return df

def render_difficulty_distribution_stack_average_attempt_line(df_diff,df_eff):
    st.divider()
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        with st.container(border=True):
            st.markdown("#### 📊 Difficulty Distribution")
            st.caption("Problem volume by difficulty: Easy/Medium/Hard")

            if not df_diff.empty:
                fig_diff = px.bar(
                    df_diff, 
                    x='activity_month', 
                    y='solved_count', 
                    color='difficulty',
                    color_discrete_map={'Easy': '#00b8a3', 'Medium': '#ffc01e', 'Hard': '#ff375f'},
                    barmode='stack',
                    labels={'activity_month': 'Month', 'solved_count': 'Count'}
                )
                fig_diff.update_layout(xaxis=dict(tickmode='linear', dtick=1), margin=dict(t=20))
                st.plotly_chart(fig_diff, width='stretch')
            else:
                st.warning(title="No data",body="")

    with col_chart2:
        with st.container(border=True):
            st.markdown("#### 📉 Average Failed Attempts")
            st.caption("Average Failed Attempts Before Acceptance")

            if not df_eff.empty:
                fig_eff = px.line(
                    df_eff, 
                    x='activity_month', 
                    y='avg_failed_attempts',
                    markers=True,
                    labels={'activity_month': 'Month', 'avg_failed_attempts': 'Average Failed Attempts'}
                )
                fig_eff.update_traces(line_color='#1a8cff', line_width=3, marker_size=8)
                fig_eff.update_layout(xaxis=dict(tickmode='linear', dtick=1), margin=dict(t=20))
                st.plotly_chart(fig_eff, width='stretch')
            else:
                st.warning(title="No data",body="")
              
def render_submission_heatmap(df_submission):
    st.divider()
    with st.container(border=True):
        st.markdown("#### 🟩 Activity Heatmap")
        if not df_submission.empty:
            df_submission = df_submission.copy()
            df_submission['weekday'] = df_submission['activity_date'].dt.weekday
            df_submission['week'] = df_submission['activity_date'].dt.isocalendar().week
            df_submission['year'] = df_submission['activity_date'].dt.year
            df_submission['month'] = df_submission['activity_date'].dt.month

            df_submission.loc[(df_submission['month'] == 1) & (df_submission['week'] >= 52), 'week'] = 0
            df_submission.loc[(df_submission['month'] == 12) & (df_submission['week'] == 1), 'week'] = 53

            pivot = df_submission.pivot(index='weekday', columns='week', values='submission_count').fillna(0)
            for i in range(7):
                if i not in pivot.index:
                    pivot.loc[i] = 0
            pivot = pivot.sort_index(ascending=False)

            github_colors = [
                [0.0, '#161b22'],     # 0 bài
                [0.01, '#0e4429'],    # 1 - 3 bài
                [0.25, '#006d32'],    # 4 - 6 bài
                [0.5, '#26a641'],     # 7 - 9 bài
                [1.0, '#39d353']      # >= 10 bài
            ]

            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            month_ticks = []
            month_labels = []
            current_month_tick = None

            current_year = datetime.now().year
            current_month = datetime.now().month

            year_months = df_submission[['year', 'month']].drop_duplicates()

            for _, row in year_months.iterrows():
                y = row['year']
                m = row['month']
                
                first_day = df_submission[(df_submission['year'] == y) & (df_submission['month'] == m)].iloc[0]
                week_val = first_day['week']
                month_ticks.append(week_val)
                
                if y == current_year and m == current_month:
                    month_labels.append(f"<b><span style='color: white;'>{month_names[m-1]}</span></b>")
                    current_month_tick = week_val
                else:
                    month_labels.append(month_names[m-1])
                    
            fig_heatmap = go.Figure(data=go.Heatmap(
                z=pivot.values,
                x=pivot.columns,
                y=pivot.index,
                colorscale=github_colors,
                showscale=False,      
                xgap=3, ygap=3,      
                hoverinfo="text",
                text=[[f"Week: {w}<br>Submissions: {int(val)}" for w, val in zip(pivot.columns, row)] for row in pivot.values]
            ))

            fig_heatmap.update_layout(
                plot_bgcolor='#0d1117', 
                paper_bgcolor='#0d1117',
                height=220,
                margin=dict(t=30, b=20, l=40, r=20),
                xaxis=dict(
                    tickmode='array',
                    tickvals=month_ticks,
                    ticktext=month_labels,
                    showgrid=False,
                    zeroline=False,
                    side='top',         
                    tickfont=dict(color='#c9d1d9', size=13)
                ),
                yaxis=dict(
                    tickmode='array',
                    tickvals=[1, 3, 5], 
                    ticktext=['Fri', 'Wed', 'Mon'], 
                    showgrid=False,
                    zeroline=False,
                    tickfont=dict(color='#c9d1d9', size=13)
                )
            )
            if current_month_tick is not None:
                fig_heatmap.add_shape(
                    type="circle",
                    xref="x", 
                    yref="paper",
                    x0=current_month_tick - 1.1,
                    x1=current_month_tick + 1.1,
                    y0=1.20,
                    y1=1.10,
                    line_color="red",
                    line_width=2
                )
            st.plotly_chart(fig_heatmap, width='stretch', config={'displayModeBar': False})
        else:
            st.warning(title="No data",body="")
            
def render_overall_metric(df_overall):
    st.divider()
    if not df_overall.empty:
        ac_rate = (df_overall['accepted_submissions'] / df_overall['total_submissions']) * 100

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("✅ Total Solved", df_overall['total_solved'], border=True)
        col2.metric("🎯 Accepted Rate", f"{ac_rate.iloc[0]:.1f}%", border=True)
        col4.metric("👑 Longest Streak", df_overall['longest_streak'],border=True)
        col5.metric("🏆 Contests", df_overall['contests_participated'],border=True)

        if df_overall["current_streak"].iloc[0] == 0:
            col3.metric("⚡ Current Streak",value= f"{df_overall['current_streak'].iloc[0]} ❄️", border= True)
        else:
            col3.metric("⚡ Current Streak",value= f"{df_overall['current_streak'].iloc[0]} 🔥", border= True)
    else:
        st.warning(title="No data",body="")
def render_error_sunburst_topic_bubble(df_error,df_topic):
    st.divider()
    col_sun,col_bubble=st.columns([1,2])

    with col_sun:    
        with st.container(border=True):
            st.markdown("#### 🎯 Error Distribution")
            st.caption("Proportion of errors by difficulty level")

            if not df_error.empty:
                color_map = {'Easy': '#00b8a3', 'Medium': '#ffc01e', 'Hard': '#ff375f'}
                df_melted = df_error.melt(
                    id_vars=['difficulty'], 
                    value_vars=['wa_count', 'tle_count', 're_count'],
                    var_name='error_type', 
                    value_name='count'
                )
                error_name_map = {'wa_count': 'Wrong Answer', 'tle_count': 'Time Limit', 're_count': 'Runtime Error'}
                df_melted['error_type'] = df_melted['error_type'].map(error_name_map)
                
                fig_sunburst = px.sunburst(
                    df_melted, 
                    path=['difficulty', 'error_type'], 
                    values='count',
                    color='difficulty',
                    color_discrete_map=color_map
                )
                fig_sunburst.update_layout(margin=dict(t=20, l=20, r=20, b=20), height=350)
                st.plotly_chart(fig_sunburst, width='stretch')
            else:
                st.warning(title="No data",body="")


    with col_bubble:
        with st.container(border=True):

            col_infor,col_filter = st.columns([1,2.5])
            with col_infor:
                st.markdown("#### 🫧 Topic Focus")
                st.caption("Bubble size represents practice intensity")
            with col_filter: 
                all_topics = df_topic['topic_name'].unique().tolist()            
                selected_topics = st.multiselect(
                    "Topic",
                    options=all_topics,
                    default=all_topics[:5],
                    max_selections=5,
                    key="multiselect_topic_overview"
                )
            
            if not df_topic.empty:
                if selected_topics:
                    df_topic_plot = df_topic[df_topic['topic_name'].isin(selected_topics)]
                    df_topic_plot = df_topic_plot[df_topic_plot['solved_count'] > 0]
                    fig_bubble = px.scatter(
                        df_topic_plot,
                        x='activity_month',
                        y='topic_name',
                        size='solved_count',       
                        color='topic_name',        
                        size_max=35,               
                        labels={
                            'activity_month': 'Month', 
                            'topic_name': 'Topic', 
                            'solved_count': 'Count'
                        },
                        hover_data={'topic_name': False}
                    )
                    mo_st=df_topic_plot["activity_month"].tolist()[0]-0.5
                    mo_ed=df_topic_plot["activity_month"].tolist()[-1]+0.5

                    fig_bubble.update_layout(
                        xaxis=dict(
                            tickmode='linear', 
                            dtick=1, 
                            range=[mo_st, mo_ed], 
                            showgrid=True,
                            gridcolor='rgba(200,200,200,0.1)'
                        ),
                        yaxis=dict(
                            showgrid=True,
                            gridcolor='rgba(200,200,200,0.1)',
                            title=""
                        ),
                        showlegend=False, 
                        margin=dict(t=20, b=10, l=10, r=20),
                        plot_bgcolor='rgba(0,0,0,0)',
                        height=350
                    )
                    st.plotly_chart(fig_bubble, width='stretch')
                else:
                    st.warning("Select at least one topic to view the chart")
            else:
                st.warning(title="No data",body="")

def render_contest_status_anatomy(df_contest_status):
    st.divider()
    with st.container(border=True):
        st.markdown("#### 🚨 Contest Question Status")
        st.caption("Analyzing user attempts and performance in the contest")
        if not df_contest_status.empty:
            fig_penalty = px.bar(
                df_contest_status,
                x="question_level",
                y="percent",
                color="status_display",
                text_auto=".1f",
                color_discrete_map={
                    "Accepted": "#33CCFF",
                    "Wrong Answer": "#ff375f",
                    "Time Limit": "#ffc01e",
                    "Runtime Error": "#8e44ad",
                },
                labels={
                    "question_level": "Question",
                    "percent": "Percent %",
                    "status_display": "Status Display",
                },
            )
            fig_penalty.update_layout(
                barmode="stack",
                height=350,
                margin=dict(t=20, b=20),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
            )
            st.plotly_chart(fig_penalty, width="stretch")
        else:
            st.warning("No data")

def render_overview():
    # Init
    df_overall = load_overall_data()
    df_submision = load_submission_data()
    df_error = load_error_data()
    df_topic = load_topic_data()
    df_diff = load_difficulty_data()
    df_attempt = load_attempt_data()
    df_contest_status = load_contest_status_data()

    # Filter
    col_title,col_filter= st.columns([5,1])
    with col_title:
        st.markdown("### Overview")
        st.caption("LeetCode Profile at a Glance")

    with col_filter:
        available_years = sorted(df_submision["activity_year"].unique().tolist(),reverse=True)
        selected_year = st.selectbox("Year", options=available_years, index=0, key="selectbox_year_overview")
        if not available_years:
            st.warning("No data available")
        df_submision_yr = df_submision[df_submision["activity_year"]== selected_year]
        df_diff_yr = df_diff[df_diff['activity_year'] == selected_year]
        df_attempt_yr = df_attempt[df_attempt['activity_year'] == selected_year]
        df_error_yr = df_error[df_error['activity_year'] == selected_year]
        df_topic_yr = df_topic[df_topic["activity_year"]==selected_year]


    # Display
    render_overall_metric(df_overall)
    render_submission_heatmap(df_submision_yr)
    render_error_sunburst_topic_bubble(df_error_yr,df_topic_yr)
    render_difficulty_distribution_stack_average_attempt_line(df_diff_yr,df_attempt_yr)
    render_contest_status_anatomy(df_contest_status)
