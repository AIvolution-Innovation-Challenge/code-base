import streamlit as st
import sqlite3
import json
from datetime import datetime
from ask_questions import UserSession

def run_quiz_module(conn, cursor, logger):
    st.title("Please complete your onboarding quizzes below")

    # Fetch all available quizzes
    cursor.execute("SELECT DISTINCT document_title, business_role FROM questions")
    all_documents = cursor.fetchall()

    # Fetch completed quizzes for the current user
    cursor.execute("""
        SELECT DISTINCT document_title FROM results
        WHERE business_role = ? AND id LIKE ? AND score = total
    """, (st.session_state.user_session.progress["business_role"], f"{st.session_state.username}_%"))
    completed_documents = {row[0] for row in cursor.fetchall()}

    # Separate available and completed quizzes
    available_documents = [doc for doc in all_documents if doc[0] not in completed_documents]

    if not available_documents:
        st.info("No quiz available. All quizzes have been completed.")
    else:
        st.write("Select quiz to take:")
        doc_options = {doc[0]: doc[1] for doc in available_documents}
        selected_doc = st.selectbox("Document", list(doc_options.keys()))

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

        if st.session_state.get("quiz_loaded", False):
            st.header(f"Quiz for {st.session_state.selected_doc}")
            with st.form(key="quiz_form"):
                user_answers = {}
                for q in st.session_state.quiz_questions:
                    q_id, question_text, options_json, correct_answer = q
                    options = json.loads(options_json)
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
                    mistakes = []  # Track mistakes
                    for q in st.session_state.quiz_questions:
                        q_id, question_text, options_json, correct_answer = q
                        user_answer = user_answers.get(q_id)
                        if user_answer and user_answer.strip().upper() == correct_answer.strip().upper():
                            score += 1
                        else:
                            mistakes.append({
                                "question": question_text,
                                "correct_answer": correct_answer,
                                "user_answer": user_answer
                            })
                    
                    # Log mistakes if any
                    if mistakes:
                        logger.log_mistakes(
                            user_id=st.session_state.username,
                            mistakes=mistakes
                        )
                    
                    st.write(f"Your score: {score} out of {total}")
                    if score == total:
                        business_role = doc_options[st.session_state.selected_doc]
                        quiz_id = f"{st.session_state.username}_{st.session_state.selected_doc}"  # Ensure id is a valid string
                        cursor.execute("""
                            INSERT INTO results (id, document_title, business_role, score, total, submission_time)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (quiz_id, st.session_state.selected_doc, business_role, score, total, datetime.now()))
                        conn.commit()
                        st.success("Congratulations! Full marks achieved. Document marked as complete.")
                        st.session_state.user_session.progress
                    else:
                        st.info("Not full marks. Please try again!")
                    logger.log_event(
                        user_id=st.session_state.username,
                        page="Take Quiz",
                        action="Submitted Quiz",
                        details=f"Document: {st.session_state.selected_doc}, Score: {score}/{total}"
                    )

    # Display completed quizzes
    if completed_documents:
        st.subheader("Completed Quizzes")
        for doc in completed_documents:
            st.write(f"- {doc}")

    with st.sidebar:
        st.header("Your Learning Progress")
        progress = st.session_state.user_session.progress
        st.write(f"Business Role: {progress['business_role']}")
        st.write(f"Total Documents: {len(progress['all_documents'])}")
        st.write(f"Completed Documents: {len(progress['completed_modules'])}")
        st.progress(progress["overall_progress"] / 100)
        st.write(f"Overall Progress: {progress['overall_progress']:.2f}%")
        
        # Add a button to refresh the progress
        if st.button("Refresh Progress"):
            st.session_state.user_session.progress = st.session_state.user_session._load_progress()
            st.experimental_rerun()
