import streamlit as st
import re
import json
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
import tempfile
import os

def get_ai_response(message, system_prompt, client):
    messages = [{"role": "system", "content": system_prompt}] + [{"role": "user", "content": message}]
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        temperature=0.7,
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()

def extract_json_block(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return None

def run_assignments(conn, cursor, client, logger):
    st.title("Assignment Creator")
    
    # --- Resume Upload Section ---
    uploaded_resume = st.file_uploader("Upload your resume (PDF or DOC/DOCX)", type=["pdf", "doc", "docx"])
    resume_summary = ""

    if uploaded_resume is not None:
        resume_text = ""
        file_type = uploaded_resume.name.split('.')[-1].lower()

        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp_file:
            tmp_file.write(uploaded_resume.read())
            tmp_path = tmp_file.name

        try:
            if file_type == "pdf":
                loader = PyPDFLoader(tmp_path)
            elif file_type in ["doc", "docx"]:
                loader = Docx2txtLoader(tmp_path)
            else:
                st.error("Unsupported file type.")
                loader = None

            if loader:
                docs = loader.load()
                resume_text = "\n".join(doc.page_content for doc in docs)

        except Exception as e:
            st.error(f"Error loading resume: {e}")
        finally:
            os.remove(tmp_path)

        if resume_text:
            system_prompt = (
                "Summarize the resume by highlighting the user's skillset, "
                "technical skills, and experience level."
            )
            resume_summary = get_ai_response(resume_text, system_prompt, client)
            st.text_area("Resume Summary", value=resume_summary, height=500)
    
    # --- Existing Assignment Creation Code ---
    # Step 1: Load usernames and business roles from the users table
    cursor.execute("SELECT username, business_role FROM users")
    users_data = cursor.fetchall()
    if not users_data:
        st.warning("No users found in the database.")
        return

    # Create a list of usernames for the drop-down
    user_options = [user[0] for user in users_data]

    # Step 2: Select a username from the drop-down
    selected_username = st.selectbox("Select a username", user_options)
    
    # Retrieve the business role for the selected user
    selected_business_role = None
    for user in users_data:
        if user[0] == selected_username:
            selected_business_role = user[1]
            break

    if not selected_business_role:
        st.error("Could not determine the business role for the selected user.")
        return

    st.write(f"Business Role for {selected_username}: **{selected_business_role}**")
    
    # Step 3: Query the questions table for quizzes related to the business role
    cursor.execute("SELECT document_title FROM questions WHERE business_role = ?", (selected_business_role,))
    questions_data = cursor.fetchall()
    available_quizzes = [row[0] for row in questions_data]
    
    # Step 4: Query the scenarios table for scenarios related to the business role
    cursor.execute("SELECT name, conversation_type FROM scenarios WHERE business_role = ?", (selected_business_role,))
    scenarios_data = cursor.fetchall()
    available_scenarios = [row[0] for row in scenarios_data]  # using scenario names

    # --- Auto-Recommendation based on Resume Summary ---
    recommended_quizzes = []
    recommended_scenarios = []
    recommended_reason = ""
    if resume_summary:
        recommendation_prompt = (
            "Based on the resume summary below, recommend which quizzes and scenarios are most relevant. "
            "The resume summary is:\n"
            f"{resume_summary}\n\n"
            "Available Quizzes (Document Titles):\n"
            f"{', '.join(available_quizzes)}\n\n"
            "Available Scenarios:\n"
            f"{', '.join(available_scenarios)}\n\n"
            "Return a JSON object with three keys: 'quizzes', 'scenarios', and 'reason'. "
            "The 'quizzes' and 'scenarios' values should be lists of items from the available options that should be auto-selected, "
            "and 'reason' should be the reason for the recommendations."
        )
        recommendation_response = get_ai_response(
            recommendation_prompt,
            "You are an assistant that recommends relevant quizzes and scenarios based on a resume.",
            client
        )
        cleaned_json = extract_json_block(recommendation_response)
        if not cleaned_json:
            raise ValueError("No JSON block found in AI response.")
        try:
            rec_data = json.loads(cleaned_json)
            recommended_quizzes = rec_data.get("quizzes", [])
            recommended_scenarios = rec_data.get("scenarios", [])
            recommended_reason = rec_data.get("reason", "No recommendation reason provided.")
        except Exception as e:
            st.error(f"Error parsing recommendations: {e}")

        # Display the extracted reason for recommendation
        st.text_area("Recommendation Reason", value=recommended_reason, height=150)

    # Step 5: Display checkboxes with auto-selection based on recommendations
    selected_quizzes = []
    if available_quizzes:
        st.subheader("Select Quizzes (Document Titles)")
        for doc_title in available_quizzes:
            # Auto-check if the doc_title is in the recommended list
            is_checked = doc_title in recommended_quizzes
            if st.checkbox(doc_title, key=f"quiz_{doc_title}", value=is_checked):
                selected_quizzes.append(doc_title)
    else:
        st.warning("No quizzes found for the selected business role.")

    selected_scenarios = []
    if scenarios_data:
        st.subheader("Select Scenarios")
        for row in scenarios_data:
            scenario_name, conversation_type = row
            label = f"{conversation_type} - {scenario_name}"
            # Auto-check if the scenario_name is in the recommended list
            is_checked = scenario_name in recommended_scenarios
            if st.checkbox(label, key=f"scenario_{scenario_name}_{conversation_type}", value=is_checked):
                selected_scenarios.append(scenario_name)
    else:
        st.warning("No scenarios found for the selected business role.")

    # Step 6: Submit button to save the assignment into a new table
    if st.button("Assign"):
        # Create the assignments table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY,
                user_id TEXT,
                quizzes TEXT,
                scenarios TEXT
            )
        ''')
        conn.commit()

        # Convert the selected quizzes and scenarios to JSON lists
        quizzes_json = json.dumps(selected_quizzes)
        scenarios_json = json.dumps(selected_scenarios)
        
        # Insert the new assignment record
        cursor.execute('''
            INSERT INTO assignments (user_id, quizzes, scenarios)
            VALUES (?, ?, ?)
        ''', (selected_username, quizzes_json, scenarios_json))
        conn.commit()
        
        st.success("Assignment created successfully!")
        logger.log_event(
            user_id=st.session_state.username,  # or use selected_username if appropriate
            page="Assignment",
            action="Created Assignment",
            details=f"Assigned quizzes: {quizzes_json} and scenarios: {scenarios_json} to {selected_username}"
        )
