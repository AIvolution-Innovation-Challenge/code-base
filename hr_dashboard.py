import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

def run_dashboard(logger):
    st.markdown("""
        <style>
            .stApp {
                font-size: 1.2rem;
            }
            .stTable th {
                text-align: left !important;
                text-transform: capitalize;
            }
            .stTable td {
                text-align: left !important;
            }
            .stTabs [data-baseweb="tab"] {
                font-size: 1.2rem;
                font-weight: 700;
                padding: 14px 28px;
                text-transform: uppercase;
                border: 1px solid #ccc;
                border-radius: 8px 8px 0 0;
                margin-right: 6px;
                background-color: #f7f7f7;
            }
            .stTabs [aria-selected="true"] {
                background-color: #ffffff !important;
                border-bottom: none;
            }
        </style>
    """, unsafe_allow_html=True)

    st.title("Your HR Onboarding Dashboard")

    logger.log_event(
        user_id=st.session_state.username,
        page="HR Dashboard",
        action="Accessed Dashboard",
        details="User accessed the HR Dashboard."
    )

    conn = sqlite3.connect("documents.db")

    def load_data():
        results = pd.read_sql_query("SELECT * FROM results", conn)
        questions = pd.read_sql_query("SELECT * FROM questions", conn)
        users = pd.read_sql_query("SELECT * FROM users", conn)
        try:
            chat_logs = pd.read_sql_query("SELECT * FROM chat_logs", conn)
        except:
            chat_logs = pd.DataFrame()
        try:
            logs = pd.read_sql_query("SELECT * FROM logs", conn)
        except:
            logs = pd.DataFrame()
        return results, questions, users, chat_logs, logs

    def get_overdue_users():
        users_df = pd.read_sql_query("SELECT username, business_role, department, start_date FROM users", conn)
        results_df = pd.read_sql_query("SELECT id, document_title, business_role, submission_time FROM results", conn)

        users_df['start_date'] = pd.to_datetime(users_df['start_date'])
        results_df['submission_time'] = pd.to_datetime(results_df['submission_time'])
        results_df['username'] = results_df['id'].apply(lambda x: x.split("_")[0] if "_" in x else x)

        submissions = results_df.groupby('username')['document_title'].apply(set).to_dict()

        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'quiz_deadline_days'")
        row = cursor.fetchone()
        deadline_days = int(row[0]) if row else 7

        cursor.execute("SELECT DISTINCT document_title, business_role FROM questions")
        rows = cursor.fetchall()
        doc_map = {}
        for doc, role in rows:
            doc_map.setdefault(role, set()).add(doc)

        today = datetime.today()
        overdue_users = []
        completed_users = []

        for _, row in users_df.iterrows():
            username = row['username']
            start_date = row['start_date']
            role = row['business_role']
            deadline = start_date + timedelta(days=deadline_days)
            due_docs = doc_map.get(role, set())
            submitted_docs = submissions.get(username, set()) or set()
            missing_docs = due_docs - submitted_docs

            if missing_docs:
                status = "OVERDUE" if today > deadline else "PENDING"
                overdue_users.append({
                    "Username": username,
                    "Role": role,
                    "Department": row['department'],
                    "Start Date": start_date.date(),
                    "Deadline": deadline.date(),
                    "Missing Documents": ", ".join(missing_docs),
                    "Status": status
                })
            else:
                completed_users.append({"Username": username, "Role": role, "Department": row['department']})

        return (
        pd.DataFrame(overdue_users),
        pd.DataFrame(completed_users, columns=["Username", "Role", "Department"]),
        users_df
    )

    def get_completion_summary(completed_users_df, users_df):
        summary = users_df.groupby('business_role').size().reset_index(name='Total Users')
        completed = completed_users_df.groupby('Role').size().reset_index(name='Completed Users')
        merged = pd.merge(summary, completed, left_on='business_role', right_on='Role', how='left')
        merged['Completed Users'] = merged['Completed Users'].fillna(0).astype(int)
        merged['Completion Rate (%)'] = (merged['Completed Users'] / merged['Total Users'] * 100).round(2)
        merged['Completion Rate (%)'] = merged['Completion Rate (%)'].map(lambda x: f"{x:.2f}")
        merged = merged[['business_role', 'Total Users', 'Completed Users', 'Completion Rate (%)']].rename(columns={"business_role": "Business Role"})
        return merged

    results_df, questions_df, users_df, chat_logs_df, logs_df = load_data()

    roles = results_df['business_role'].unique().tolist()
    selected_role = st.sidebar.selectbox("Filter by Role", ["All"] + roles)

    if selected_role != "All":
        results_df = results_df[results_df['business_role'] == selected_role]
        questions_df = questions_df[questions_df['business_role'] == selected_role]
        if not chat_logs_df.empty:
            chat_logs_df = chat_logs_df[chat_logs_df['user_id'].str.contains(selected_role.replace(" ", ""), na=False)]

    overview, chat_tab, compliance_tab, role_tab, quiz_tab = st.tabs([
        "Overview", "Chat Insights", "Compliance", "Per Role Analysis", "Quiz Analytics"
    ])

    with overview:
        st.subheader("Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Documents Uploaded", questions_df['document_title'].nunique())
        col2.metric("Quizzes Completed", results_df.shape[0])
        col3.metric("Avg Quiz Score", f"{results_df['score'].mean():.2f}" if not results_df.empty else "-")
        col4.metric("Chat Queries Logged", chat_logs_df.shape[0] if not chat_logs_df.empty else 0)

    with chat_tab:
        if not chat_logs_df.empty:
            st.subheader("Chat Activity Trends")
            chat_logs_df['timestamp'] = pd.to_datetime(chat_logs_df['timestamp'])
            chat_trend = chat_logs_df.groupby(chat_logs_df['timestamp'].dt.date).size().reset_index(name='Messages')
            fig4 = px.area(chat_trend, x='timestamp', y='Messages', title="Chat Volume Over Time")
            fig4.update_layout(plot_bgcolor='white', paper_bgcolor='white')
            st.plotly_chart(fig4)

            st.subheader("Top 10 Most Common Queries")
            common_queries = chat_logs_df['message'].value_counts().nlargest(10).reset_index()
            common_queries.columns = ['Query', 'Count']
            st.table(common_queries.set_index(pd.Index(range(1, len(common_queries)+1))))
        else:
            st.info("No chat logs available.")

    with compliance_tab:
        st.subheader("Onboarding Compliance Overview")
        overdue_df, completed_users_df, users_df = get_overdue_users()

        st.markdown("### Completion Summary by Role")
        completion_summary = get_completion_summary(completed_users_df, users_df).round(2)
        st.table(completion_summary.set_index(pd.Index(range(1, len(completion_summary)+1))))

        st.markdown("### Completion Summary by Document")
        doc_summary = results_df.groupby(['business_role', 'document_title']).size().reset_index(name='Completions')
        doc_summary.columns = ['Business Role', 'Document Title', 'Completions']
        st.table(doc_summary.set_index(pd.Index(range(1, len(doc_summary)+1))))

        csv = doc_summary.to_csv(index=False).encode('utf-8')
        st.download_button("Download Document Summary", data=csv, file_name="doc_summary.csv", mime='text/csv')

        st.markdown("### Overdue or At-Risk Users")
        if not overdue_df.empty:
            overdue_df = overdue_df.round(2)
            overdue_df = overdue_df.set_index(pd.Index(range(1, len(overdue_df) + 1)))
            styled_df = overdue_df.style.map(
                lambda val: 'color: red; font-weight: bold;' if val == 'OVERDUE' else 'color: orange;',
                subset=['Status']
            )
            st.dataframe(styled_df)
            csv = overdue_df.reset_index().to_csv(index=False).encode('utf-8')
            st.download_button("Download Overdue Report", data=csv, file_name="overdue_users_report.csv", mime='text/csv')
        else:
            st.success("All users are compliant so far!")

    with role_tab:
        st.subheader("Deep Dive by Role")
        role_filter = st.selectbox("Choose a Role", roles)
        role_data = results_df[results_df['business_role'] == role_filter]

        if not role_data.empty:
            st.markdown(f"### Average Scores for {role_filter}")
            avg_doc_scores = role_data.groupby('document_title')['score'].mean().reset_index()
            avg_doc_scores.columns = ['Document Title', 'Average Score']
            avg_doc_scores['Average Score'] = avg_doc_scores['Average Score'].round(2)
            avg_doc_scores['Average Score'] = avg_doc_scores['Average Score'].map(lambda x: f"{x:.2f}")
            st.table(avg_doc_scores.set_index(pd.Index(range(1, len(avg_doc_scores)+1))))

            st.markdown(f"### Score Distribution for {role_filter}")
            role_data['score'] = role_data['score'].astype(float)

            # Create histogram bins and labels
            counts, bin_edges = np.histogram(role_data['score'], bins=10)
            bin_labels = [f"{int(bin_edges[i])}-{int(bin_edges[i+1])}" for i in range(len(bin_edges) - 1)]
            binned_scores = pd.cut(role_data['score'], bins=bin_edges, labels=bin_labels, include_lowest=True, ordered=False)
            
            bin_counts = binned_scores.value_counts().reindex(bin_labels).fillna(0).reset_index()
            bin_counts.columns = ['Score Range', 'Number of Users']

            # Plot with correct bin labels
            fig2 = px.bar(
                bin_counts,
                x='Score Range',
                y='Number of Users',
                title="Score Distribution",
                color_discrete_sequence=['#636EFA']
            )
            fig2.update_layout(
                xaxis_title="Score",
                yaxis_title="Number of Users",
                plot_bgcolor="white",
                paper_bgcolor="white"
            )

            st.plotly_chart(fig2)
        else:
            st.warning("No data available for this role.")


    with quiz_tab:
        st.subheader("Quiz Analytics")
        results_df['username'] = results_df['id'].str.extract(r'^(.*?)_')
        merged_df = results_df.merge(users_df[['username', 'department']], on='username', how='left')
        department_stats = merged_df.groupby('department').agg(
            Quizzes_Completed=('id', 'count'),
            Average_Score=('score', 'mean')
        ).reset_index()
        department_stats.columns = ['Department', 'Quizzes Completed', 'Average Score']
        department_stats['Average Score'] = department_stats['Average Score'].round(2)
        department_stats['Average Score'] = department_stats['Average Score'].map(lambda x: f"{x:.2f}")
        st.markdown("### Quiz Summary by Department")
        st.table(department_stats.set_index(pd.Index(range(1, len(department_stats)+1))))

        st.subheader("Average Score by Document")
        avg_doc_scores = results_df.groupby('document_title')['score'].mean().reset_index()
        avg_doc_scores.columns = ['Document', 'Average Score']
        avg_doc_scores['Average Score'] = avg_doc_scores['Average Score'].round(2)
        avg_doc_scores['Average Score'] = avg_doc_scores['Average Score'].map(lambda x: f"{x:.2f}")
        st.table(avg_doc_scores.set_index(pd.Index(range(1, len(avg_doc_scores)+1))))

        st.subheader("Quiz Submission Timeline")
        results_df['submission_time'] = pd.to_datetime(results_df['submission_time'])
        timeline = results_df.groupby(results_df['submission_time'].dt.date).size().reset_index(name='Submissions')
        fig3 = px.line(timeline, x='submission_time', y='Submissions', title="Submission Trend")
        fig3.update_layout(plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig3)