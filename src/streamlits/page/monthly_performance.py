import streamlit as st
import pandas as pd
import plotly.express as px
from src.utility.streamlit_utils import connection
import plotly.graph_objects as go
import calendar
from datetime import date

@st.cache_data
def load_score_data():
    df = pd.DataFrame({
        'activity_year': pd.Series(dtype='int16'),
        'activity_month': pd.Series(dtype='int8')
    })

    try:
        cursor=connection.cursor()
        query="""
            WITH cte_monthly_overall AS
            (
                SELECT 
                    year(sub_date) as activity_year,
                    month(sub_date) as activity_month,
                    COUNT(DISTINCT CASE WHEN status_display = "Accepted" and difficulty = "Easy" THEN question_id END) as easy_count,
                    COUNT(DISTINCT CASE WHEN status_display = "Accepted" and difficulty = "Medium" THEN question_id END) as medium_count,
                    COUNT(DISTINCT CASE WHEN status_display = "Accepted" and difficulty = "Hard" THEN question_id END) as hard_count,
                    COUNT(CASE WHEN status_display != "Accepted" THEN question_id END) as failed_attempt,
                    COUNT(DISTINCT day(sub_date)) as active_day 
                FROM mart_submission_difficulty
                GROUP BY activity_year,activity_month
            )
            SELECT 
                activity_year,
                activity_month,
                easy_count+3*medium_count+5*hard_count-0.5*failed_attempt + 2*active_day as performance_score,
                CASE 
                    WHEN easy_count+3*medium_count+5*hard_count-0.5*failed_attempt + 2*active_day > AVG(easy_count+3*medium_count+5*hard_count-0.5*failed_attempt + 2*active_day)OVER() THEN 1
                    ELSE 0
                END is_above_avg,
                easy_count,
                medium_count,
                hard_count,
                failed_attempt
            FROM cte_monthly_overall
            ORDER BY activity_year,activity_month
            """

        cursor.execute(query)

        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        df["performance_score"]=df["performance_score"].astype(float)

    except Exception as e:
        st.error(title="Get error while execute load_score_data", icon="🚨", body="")
    return df

@st.cache_data
def load_daily_pace():
    df = pd.DataFrame({
        'activity_year': pd.Series(dtype='int16'),
        'activity_month': pd.Series(dtype='int8')
    })

    try:
        cursor=connection.cursor()
        query="""
            SELECT 
                year(sub_date) as activity_year,
                month(sub_date) as activity_month,
                day(sub_date) as day_of_month,
                COUNT(DISTINCT CASE WHEN status_display = "Accepted" THEN question_id END) as solved_count,
                COUNT(question_id) as submission_count
            FROM mart_submission_difficulty
            GROUP BY activity_year,activity_month,day_of_month
            ORDER BY activity_year,activity_month,day_of_month            
        """
        cursor.execute(query)
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

    except Exception as e:
        st.error(title="Get error while execute load_daily_pace", icon="🚨", body="")
    return df

@st.cache_data
def load_topic_spotlight():
    df = pd.DataFrame({
        'activity_year': pd.Series(dtype='int16'),
        'activity_month': pd.Series(dtype='int8')
    })

    try:
        cursor=connection.cursor()
        query="""
            SELECT
                YEAR(sub_date) as activity_year,
                MONTH(sub_date) as activity_month,
                topic_tag as topic_name,
                COUNT(DISTINCT CASE WHEN status_display = "Accepted" THEN question_id END) as solved_count,
                ROUND(solved_count*100.0 / COUNT(*),2) as accuracy_rate
            FROM mart_submission_topic
            GROUP BY activity_year,activity_month,topic_name
            ORDER BY solved_count DESC, accuracy_rate DESC
        """
        cursor.execute(query)
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

    except Exception as e:
        st.error(title="Get error while execute load_topic_spotlight", icon="🚨", body="")
    return df
    
@st.cache_data
def load_daily_challenge_data():
    df = pd.DataFrame({
        'activity_year': pd.Series(dtype='int16'),
        'activity_month': pd.Series(dtype='int8')
    })

    try:
        cursor=connection.cursor()
        query="""
            SELECT
                year(daily_date) as activity_year,
                month(daily_date) as activity_month,
                day(daily_date) as day_of_month,
                daily_date as activity_date,
                COUNT(DISTINCT CASE WHEN daily_date = sub_date and status_display = "Accepted" THEN 1 END) as is_completed,
                concat(question_frontend_id,". ",question_title) as problem_name
            FROM mart_submission_daily
            GROUP BY activity_year,activity_month,day_of_month,activity_date,question_frontend_id,question_title
            ORDER BY activity_year,activity_month,day_of_month,activity_date
        """
        cursor.execute(query)
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
    except Exception as e:
        st.error(title="Get error while execute load_daily_challenge_data", icon="🚨", body="")
    return df

def render_preformance_score_area(df_score):
    st.divider()
    with st.container(border=True):
        st.markdown("#### 🏆 Performance Score")
        st.caption("A comprehensive assessment index based on assignment difficulty, submission optimization, and discipline")
        if not df_score.empty:
            avg_score = df_score['performance_score'].mean()

            min_x = df_score['activity_month'].min()
            max_x = df_score['activity_month'].max()
            fig_score = px.area(
                df_score, 
                x='activity_month', 
                y='performance_score',
                markers=True,
                labels={'activity_month': 'Month', 'performance_score': 'Performance Score'}
            )
            fig_score.update_traces(
                line_color='#26a641', 
                fillcolor='rgba(38, 166, 65, 0.2)', 
                line_width=3,
                marker=dict(size=8, color='#006d32')
            )
            
            fig_score.add_hline(
                y=avg_score, 
                line_dash="dash", 
                line_color="#ffc01e", 
                annotation_text=f"Avarage Year: {avg_score:.1f}", 
                annotation_position="bottom right"
            )
            fig_score.update_layout(
                xaxis=dict(
                    tickmode='linear', 
                    dtick=1, 
                    showgrid=False,
                    range=[min_x - 0.05, max_x + 0.05]
                ),
                yaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.1)'),
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=20, b=10, l=10, r=20),
                height=300
            )
            st.plotly_chart(fig_score, width='stretch')
        else:
            st.warning("No data")
def render_practice_pace_barline_daily_challenge_calender(df_pace,df_daily,selected_year,selected_month):
    st.divider()
    col_bar_line,col_calender = st.columns(2)
    with col_bar_line:
        with st.container(border=True):
            st.markdown("#### 🏃 Daily Practice Pace")
            st.caption("Total Submissions vs Accepted Submissions")

            if not df_pace.empty:
                df_pace = df_pace.copy()
                df_pace['day_of_month'] = df_pace['day_of_month'].astype(str)
                fig_pace = go.Figure()
                
                # Bar
                fig_pace.add_trace(go.Bar(
                    x=df_pace['day_of_month'], 
                    y=df_pace['solved_count'],
                    name='Solved Count',
                    marker_color='#00b8a3'
                ))
                # Line
                fig_pace.add_trace(go.Scatter(
                    x=df_pace['day_of_month'], 
                    y=df_pace['submission_count'],
                    name='Submissions',
                    mode='lines+markers',
                    line=dict(color='#ffc01e', width=3),
                    marker=dict(size=6)
                ))
                
                fig_pace.update_layout(
                    xaxis=dict(title="Day of month", type = 'category'),
                    yaxis=dict(title="Count"),
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1),
                    margin=dict(t=30, b=10),
                    height=400
                )
                st.plotly_chart(fig_pace, width='stretch')
            else: 
                st.warning("No data")

    with col_calender:
        with st.container(border=True,height=522):
            st.markdown("#### 🗓️ Daily Coding Challenge")
            st.caption("Monthly Challenge Tracking")

            if not df_daily.empty:
                today = date.today()
                st.markdown("""
                    <style>
                    .day-cell { height: 60px; display: flex; flex-direction: column; justify-content: center; align-items: center; cursor: pointer; color: #eff2f6; }
                    .day-num { font-size: 16px; margin-bottom: 4px; }
                    .dot-missed { width: 4px; height: 4px; background-color: #ef4743; border-radius: 50%; }
                    .icon-completed { width: 28px; height: 28px; border: 2.5px solid #007aff; border-radius: 50%; display: flex; justify-content: center; align-items: center; color: #007aff; font-weight: bold; font-size: 14px; }
                    .icon-today { width: 34px; height: 34px; background-color: #2cbb5d; border-radius: 50%; display: flex; justify-content: center; align-items: center; color: white; font-weight: bold; font-size: 16px; }
                    </style>
                """, unsafe_allow_html=True)

                calendar.setfirstweekday(calendar.SUNDAY)
                cal = calendar.monthcalendar(selected_year, selected_month)
                weekdays = ["S", "M", "T", "W", "T", "F", "S"]
                
                header_cols = st.columns(7)
                for i, day_name in enumerate(weekdays):
                    header_cols[i].markdown(f"<div style='text-align: center; font-weight: bold; color: #8a8a8a;'>{day_name}</div>", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                for week in cal:
                    week_cols = st.columns(7)
                    for i, day in enumerate(week):
                        if selected_year== today.year and selected_month==today.month and day>today.day:
                            cell_html = f"<div class='day-cell' {""}><div class='day-num'>{day}</div></div>"
                            week_cols[i].markdown(cell_html, unsafe_allow_html=True)
                            continue
                        if day == 0:
                            week_cols[i].write("") # Ô trống
                        else:
                            df_filter = df_daily[df_daily['day_of_month'] == day]
                            if df_filter.empty:
                                cell_date = date(selected_year,selected_month,day)
                                is_completed = None
                                problem_name = "No data available, please upload new data"

                            else:
                                row_data = df_filter.iloc[0]
                                cell_date = row_data['activity_date']
                                is_completed = row_data['is_completed']
                                problem_name = row_data['problem_name']
                                
                            tooltip = f"title='{problem_name}'"
                            
                            if cell_date == today:
                                # Hôm nay: Nền xanh lá
                                cell_html = f"<div class='day-cell' {tooltip}><div class='icon-today'>{day}</div></div>"
                            elif is_completed == 1:
                                # Hoàn thành: Tick xanh dương
                                cell_html = f"""
                                            <div class='day-cell' {tooltip}>
                                                <div class='icon-completed'>✓</div>
                                            </div>
                                """
                            else:
                                # Bỏ lỡ: Số + Chấm đỏ
                                cell_html = f"""
                                <div class='day-cell' {tooltip}>
                                    <div class='day-num'>{day}</div>
                                    <div class='dot-missed'></div>
                                </div>
                                """
                            week_cols[i].markdown(cell_html, unsafe_allow_html=True)
                st.html("<div style='height: 15px;'></div>")
            else:
                st.warning("No data")
def render_topic_bubble(df_topic):
    st.divider()
    with st.container(border=True):
        st.markdown("#### 🫧 Core Topic Landscape")
        st.caption("Acceptance Rate of Top-Submitted Topics")

        if not df_topic.empty:
            fig_bubble = px.scatter(
                df_topic,
                x='topic_name',
                y='accuracy_rate',
                size='solved_count',
                color='topic_name',
                size_max=45,
                labels={'topic_name': 'Topic', 'accuracy_rate': 'Accepted Rate %', 'solved_count': 'Solved'},
            )
            fig_bubble.update_layout(
                yaxis=dict(title="Accepted Rate %"),
                xaxis=dict(title=""),
                showlegend=False,
                margin=dict(t=10, b=20),
                height=350
            )
            st.plotly_chart(fig_bubble, width='stretch')
        else:
            st.warning("No data")
def render_monthly_performance_dashboard():
    # Load data
    df_score = load_score_data()
    df_pace = load_daily_pace()
    df_topic = load_topic_spotlight()
    df_daily= load_daily_challenge_data()

    # Filter
    col_title,col_yr,col_mo = st.columns([3,1,1])

    with col_title:
        st.markdown("### 📈 Monthly Performance")
        st.caption("Track progress, performance, and shifting learning focus month over month")

    with col_yr:
        available_years = sorted(df_daily["activity_year"].unique().tolist(),reverse=True)
        selected_year = st.selectbox("Year:", options=available_years, index=0, key="selectbox_year_monthly_performance")

        df_pace_yr=df_pace[df_pace["activity_year"]== selected_year]
        df_topic_yr=df_topic[df_topic["activity_year"]== selected_year]
        df_daily_yr=df_daily[df_daily["activity_year"]==selected_year]
        df_score_yr = df_score[df_score['activity_year'] == selected_year]

    with col_mo:
        available_month = sorted(df_daily_yr["activity_month"].unique().tolist(),reverse=True)
        selected_month = st.selectbox("Month:", options=available_month, index=0, key= "selectbox_month_monthly_performance") 

        df_pace_yr_mo=df_pace_yr[df_pace_yr["activity_month"]==selected_month]
        df_topic_yr_mo=df_topic_yr[df_topic_yr["activity_month"]==selected_month].head(8)
        df_daily_yr_mo = df_daily_yr[df_daily_yr["activity_month"]==selected_month]
    if not available_years and not available_month:
        st.info("No data available")

    # Display
    render_preformance_score_area(df_score_yr)    
    render_practice_pace_barline_daily_challenge_calender(df_pace_yr_mo,df_daily_yr_mo,selected_year,selected_month)
    render_topic_bubble(df_topic_yr_mo)


