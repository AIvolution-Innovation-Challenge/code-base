import streamlit as st
import sqlite3
import json

def run_assignments(conn, cursor, logger):
    st.title("Assignment Creator")
    
    # Step 1: Load usernames and business roles from the user table
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
    
    selected_quizzes = []
    if questions_data:
        st.subheader("Select Quizzes (Document Titles)")
        for row in questions_data:
            doc_title = row[0]
            if st.checkbox(doc_title, key=f"quiz_{doc_title}"):
                selected_quizzes.append(doc_title)
    else:
        st.warning("No quizzes found for the selected business role.")

    # Step 4: Query the scenarios table for scenarios related to the business role
    cursor.execute("SELECT name, conversation_type FROM scenarios WHERE business_role = ?", (selected_business_role,))
    scenarios_data = cursor.fetchall()

    selected_scenarios = []
    if scenarios_data:
        st.subheader("Select Scenarios")
        for row in scenarios_data:
            scenario_name, conversation_type = row
            label = f"{conversation_type} - {scenario_name}"
            if st.checkbox(label, key=f"scenario_{scenario_name}_{conversation_type}"):
                selected_scenarios.append(scenario_name)
    else:
        st.warning("No scenarios found for the selected business role.")

    # Step 5: Submit button to save the assignment into a new table
    if st.button("Submit Assignment"):
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
