import streamlit as st
import sqlite3
import json
from datetime import datetime

# Connect to (or create) the SQLite database
conn = sqlite3.connect("documents.db", check_same_thread=False)
cursor = conn.cursor()

# Create the results table if it does not exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY,
        document_title TEXT,
        business_role TEXT,
        score INTEGER,
        total INTEGER,
        submission_time DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

st.title("MCQ Quiz Interface")

# Query distinct document titles and their associated business roles from the questions table
cursor.execute("SELECT DISTINCT document_title, business_role FROM questions")
documents = cursor.fetchall()

if not documents:
    st.info("No quiz available. Please upload questions first.")
else:
    st.write("Select quiz to take:")
    # Build a mapping for document title to business role
    doc_options = {doc[0]: doc[1] for doc in documents}
    selected_doc = st.selectbox("Document", list(doc_options.keys()))

    # Button to load the quiz; store quiz details in session state
    if st.button("Load Quiz"):
        cursor.execute(
            "SELECT id, question, options, answer FROM questions WHERE document_title = ?",
            (selected_doc,)
        )
        quiz_questions = cursor.fetchall()
        if quiz_questions:
            st.session_state.quiz_loaded = True
            st.session_state.selected_doc = selected_doc
            st.session_state.quiz_questions = quiz_questions
        else:
            st.info("No questions found for the selected document.")

    # If the quiz has been loaded, display the quiz form
    if st.session_state.get("quiz_loaded", False):
        st.header(f"Quiz for {st.session_state.selected_doc}")
        with st.form(key="quiz_form"):
            user_answers = {}
            for q in st.session_state.quiz_questions:
                q_id, question_text, options_json, correct_answer = q
                options = json.loads(options_json)
                # Use format_func to display both the option key and its associated text.
                answer = st.radio(
                    f"Q: {question_text}",
                    options=list(options.keys()),
                    key=f"q_{q_id}",
                    format_func=lambda x, opts=options: f"{x}: {opts[x]}"
                )
                user_answers[q_id] = answer
            submitted = st.form_submit_button("Submit Answers")
            if submitted:
                total = len(st.session_state.quiz_questions)
                score = 0
                # Evaluate the answers
                for q in st.session_state.quiz_questions:
                    q_id, question_text, options_json, correct_answer = q
                    user_answer = user_answers.get(q_id)
                    if user_answer and user_answer.strip().upper() == correct_answer.strip().upper():
                        score += 1
                st.write(f"Your score: {score} out of {total}")
                # If full marks, insert a row into the results table
                if score == total:
                    business_role = doc_options[st.session_state.selected_doc]
                    cursor.execute("""
                        INSERT INTO results (document_title, business_role, score, total, submission_time)
                        VALUES (?, ?, ?, ?, ?)
                    """, (st.session_state.selected_doc, business_role, score, total, datetime.now()))
                    conn.commit()
                    st.success("Congratulations! Full marks achieved. Document marked as complete.")
                else:
                    st.info("Not full marks. Please try again!")

conn.close()
