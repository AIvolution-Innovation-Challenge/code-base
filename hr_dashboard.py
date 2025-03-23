import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime
from wordcloud import WordCloud

def run_dashboard():
    #st.image("aivolution_logo.jpeg", width=200)
    st.title("Your HR Onboarding Dashboard")
    conn = sqlite3.connect("documents.db")

    def load_data():
        results = pd.read_sql_query("SELECT * FROM results", conn)
        questions = pd.read_sql_query("SELECT * FROM questions", conn)
        try:
            chat_logs = pd.read_sql_query("SELECT * FROM chat_logs", conn)
        except:
            chat_logs = pd.DataFrame()
        return results, questions, chat_logs

    results_df, questions_df, chat_logs_df = load_data()

    roles = results_df['business_role'].unique().tolist()
    selected_role = st.sidebar.selectbox("Filter by Role", ["All"] + roles)

    if selected_role != "All":
        results_df = results_df[results_df['business_role'] == selected_role]
        questions_df = questions_df[questions_df['business_role'] == selected_role]
        if not chat_logs_df.empty:
            chat_logs_df = chat_logs_df[chat_logs_df['user_id'].str.contains(selected_role.replace(" ", ""), na=False)]

    overview, quiz_tab, chat_tab, doc_tab, role_tab = st.tabs(["Overview", "Quiz Analytics", "Chat Insights", "Document Stats", "Per Role Analysis"])

    with overview:
        st.subheader("Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Documents Uploaded", questions_df['document_title'].nunique())
        col2.metric("Quizzes Completed", results_df.shape[0])
        col3.metric("Avg Quiz Score", f"{results_df['score'].mean():.2f}" if not results_df.empty else "-")
        col4.metric("Chat Queries Logged", chat_logs_df.shape[0] if not chat_logs_df.empty else 0)

    with quiz_tab:
        st.subheader("Completion Rate per Document")
        if not results_df.empty:
            doc_counts = results_df.groupby('document_title').size().reset_index(name='Completions')
            fig1 = px.bar(doc_counts, x='document_title', y='Completions', title="Completions by Document")
            st.plotly_chart(fig1, use_container_width=True)

        st.subheader("Average Score per Document")
        if not results_df.empty:
            avg_scores = results_df.groupby('document_title')['score'].mean().reset_index()
            fig2 = px.bar(avg_scores, x='document_title', y='score', title="Average Quiz Scores")
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Submission Timeline")
        if not results_df.empty:
            results_df['submission_time'] = pd.to_datetime(results_df['submission_time'])
            timeline = results_df.groupby(results_df['submission_time'].dt.date).size().reset_index(name='Submissions')
            fig3 = px.line(timeline, x='submission_time', y='Submissions', title="Quiz Submissions Over Time")
            st.plotly_chart(fig3, use_container_width=True)

    with chat_tab:
        if not chat_logs_df.empty:
            st.subheader("Chat Activity Trends")
            chat_logs_df['timestamp'] = pd.to_datetime(chat_logs_df['timestamp'])
            chat_trend = chat_logs_df.groupby(chat_logs_df['timestamp'].dt.date).size().reset_index(name='Messages')
            fig4 = px.area(chat_trend, x='timestamp', y='Messages', title="Chat Volume Over Time")
            st.plotly_chart(fig4, use_container_width=True)

            st.subheader("Top 10 Most Common Queries")
            common_queries = chat_logs_df['message'].value_counts().nlargest(10).reset_index()
            common_queries.columns = ['Query', 'Count']
            st.dataframe(common_queries)

            st.subheader("Query Word Cloud")
            text = " ".join(chat_logs_df['message'])
            wordcloud = WordCloud(width=600, height=250, background_color='white', colormap='viridis', prefer_horizontal=1.0).generate(text)
            st.image(wordcloud.to_array(), width=600)
        else:
            st.info("No chat logs available.")

    with doc_tab:
        st.subheader("Documents Covered in Onboarding")
        doc_summary = results_df.groupby(['business_role', 'document_title']).size().reset_index(name='Completions')
        st.dataframe(doc_summary)

        st.subheader("Download Summary")
        csv = doc_summary.to_csv(index=False).encode('utf-8')
        st.download_button("Download as CSV", data=csv, file_name="doc_summary.csv", mime='text/csv')

    with role_tab:
        st.subheader("Deep Dive by Role")
        role_filter = st.selectbox("Choose a Role", roles)
        role_data = results_df[results_df['business_role'] == role_filter]

        if not role_data.empty:
            st.markdown(f"Score Trend for {role_filter}")
            fig5 = px.box(role_data, x='document_title', y='score', color='document_title', title="Score Distribution")
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.warning("No data available for this role.")

    #st.markdown("---")
