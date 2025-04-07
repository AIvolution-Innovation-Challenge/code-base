import streamlit as st
import sqlite3
import json
from datetime import datetime
from ask_questions import UserSession

def run_quiz_module(conn, cursor, logger):
    st.title("Please complete your onboarding quizzes below")

    # 1. Fetch assigned quizzes for the current user from the assignments table.
    cursor.execute("SELECT quizzes FROM assignments WHERE user_id = ?", (st.session_state.username,))
    row = cursor.fetchone()
    if row:
        # Assuming the 'quizzes' column is stored as a JSON list of quiz names.
        assigned_quizzes = json.loads(row[0])
    else:
        assigned_quizzes = []

    # 2. Fetch completed quizzes for the current user from the results table (only those with full marks).
    cursor.execute("""
        SELECT DISTINCT document_title FROM results
        WHERE id LIKE ? AND score = total
    """, (f"{st.session_state.username}_%",))
    completed_documents = {row[0] for row in cursor.fetchall()}

    # Filter out quizzes that are already completed.
    available_quizzes = [quiz for quiz in assigned_quizzes if quiz not in completed_documents]

    if not available_quizzes:
        st.info("No quiz available. All quizzes have been completed.")
    else:
        st.write("Select quiz to take:")
        selected_quiz = st.selectbox("Quiz", available_quizzes)

        if st.button("Load Quiz"):
            cursor.execute(
                "SELECT id, question, options, answer FROM questions WHERE document_title = ?",
                (selected_quiz,)
            )
            quiz_questions = cursor.fetchall()
            if quiz_questions:
                st.session_state.quiz_loaded = True
                st.session_state.selected_quiz = selected_quiz
                st.session_state.quiz_questions = quiz_questions
            else:
                st.info("No questions found for the selected quiz.")

        if st.session_state.get("quiz_loaded", False):
            st.header(f"Quiz for {st.session_state.selected_quiz}")
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
                    mistakes = []
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
                    
                    if mistakes:
                        logger.log_mistakes(
                            user_id=st.session_state.username,
                            mistakes=mistakes
                        )
                    
                    st.write(f"Your score: {score} out of {total}")
                    if score == total:
                        quiz_id = f"{st.session_state.username}_{st.session_state.selected_quiz}"
                        cursor.execute("""
                            INSERT INTO results (id, document_title, score, total, submission_time)
                            VALUES (?, ?, ?, ?, ?)
                        """, (quiz_id, st.session_state.selected_quiz, score, total, datetime.now()))
                        conn.commit()
                        st.success("Congratulations! Full marks achieved. Quiz marked as complete.")
                    else:
                        st.info("Not full marks. Please try again!")
                    logger.log_event(
                        user_id=st.session_state.username,
                        page="Take Quiz",
                        action="Submitted Quiz",
                        details=f"Quiz: {st.session_state.selected_quiz}, Score: {score}/{total}"
                    )

    # Display completed quizzes.
    if completed_documents:
        st.subheader("Completed Quizzes")
        for quiz in completed_documents:
            st.write(f"- {quiz}")

    with st.sidebar:
        st.header("Your Learning Progress")
        progress = st.session_state.user_session.progress
        # Optionally, you might remove the Business Role display if it's no longer relevant.
        # st.write(f"Business Role: {progress['business_role']}")
        st.write(f"Total Quizzes: {len(progress['all_documents'])}")
        st.write(f"Completed Quizzes: {len(progress['completed_modules'])}")
        st.progress(progress["overall_progress"] / 100)
        st.write(f"Overall Progress: {progress['overall_progress']:.2f}%")
        
        if st.button("Refresh Progress"):
            st.session_state.user_session.progress = st.session_state.user_session._load_progress()
            st.rerun()
