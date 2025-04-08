import sqlite3
import streamlit as st
import json
import time
import os
from voice_assistant_trainer_with_voice import (
    record_audio,
    transcribe_audio,
    get_ai_response,
    tts_threaded_playback,
    evaluate_conversation,
)

MAX_DIALOGUES = 6

# ----------------------- Load Scenarios from SQLite Database -----------------------
def load_scenarios_from_db(db_path="database.db"):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    query = """
    SELECT id, name, conversation_type, persona_ai, persona_user, scenario_description, system_prompt, evaluation_criteria, business_role
    FROM scenarios;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    scenarios = {}
    for row in rows:
        scenario_id, name, conversation_type, persona_ai, persona_user, scenario_description, system_prompt, evaluation_criteria, business_role = row
        scenarios[name] = {
            "id": scenario_id,
            "name": name,
            "conversation_type": conversation_type,
            "persona_ai": persona_ai,
            "persona_user": persona_user,
            "scenario_description": scenario_description,
            "system_prompt": system_prompt,
            "evaluation_criteria": evaluation_criteria,
            "business_role": business_role
        }
    connection.close()
    return scenarios

# ----------------------- Conversation Module -----------------------
def run_conversation_module(conn, cursor, logger):
    st.title("Voice Conversation Module")
    st.write("Complete your conversation exercise by selecting a scenario and interacting with the AI below.")

    # 1. Fetch assigned scenarios for the current user from the assignments table.
    cursor.execute("SELECT scenarios FROM assignments WHERE user_id = ?", (st.session_state.username,))
    row = cursor.fetchone()
    if row:
        # Assuming the 'scenarios' column is stored as a JSON list of scenario names.
        assigned_scenarios = json.loads(row[0])
    else:
        assigned_scenarios = []

    # 2. Load all scenarios from the database.
    all_scenarios = load_scenarios_from_db("database.db")
    # Filter out scenarios that are not assigned to the user.
    scenario_options = {name: data for name, data in all_scenarios.items() if name in assigned_scenarios}

    if not scenario_options:
        st.info("No conversation scenarios assigned to you.")
        return

    # ----------------------- Scenario Selection in Main Area -----------------------
    if "scenario_key" not in st.session_state:
        st.session_state.scenario_key = list(scenario_options.keys())[0]

    selected_scenario_key = st.selectbox(
        "Choose Scenario",
        list(scenario_options.keys()),
        index=list(scenario_options.keys()).index(st.session_state.scenario_key)
    )
    st.session_state.scenario_key = selected_scenario_key
    scenario = scenario_options[selected_scenario_key]

    st.write(f"**Current Scenario:** {selected_scenario_key}")
    st.write("**Scenario Description:**")
    st.write(scenario["scenario_description"])

    # ----------------------- Session State Initialization -----------------------
    if "start_scenario" not in st.session_state:
        st.session_state.start_scenario = False
    if "dialogue_round" not in st.session_state:
        st.session_state.dialogue_round = 0
    if "messages_history" not in st.session_state:
        st.session_state.messages_history = []

    # ----------------------- Start Button -----------------------
    if not st.session_state.start_scenario:
        if st.button("Start Scenario"):
            st.session_state.start_scenario = True
            st.rerun()  # Trigger a rerun now that the scenario has started.
    else:
        st.write("### Conversation in Progress...")

        def run_conversation_round():
            st.write(f"**Dialogue Round {st.session_state.dialogue_round + 1}**")
            
            # Record user input (this blocks until recording stops)
            audio_file = record_audio("user_input.wav")
            user_text = transcribe_audio(audio_file)
            st.write(f"**{scenario['persona_user']} said:**", user_text)
            
            # Generate AI response using conversation history and the system prompt from the scenario
            ai_response = get_ai_response(
                user_text,
                st.session_state.messages_history,
                scenario["system_prompt"]
            )
            st.write(f"**{scenario['persona_ai']} says:**", ai_response)
            
            # Append messages to history for later evaluation
            st.session_state.messages_history.extend([
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": ai_response}
            ])
            
            # Play the AI response using TTS (this function blocks until playback is complete)
            tts_threaded_playback(ai_response, voice="af_heart", max_chunk_length=100)
            
            # Clean up the temporary audio file
            if os.path.exists(audio_file):
                os.remove(audio_file)
            
            # Increment dialogue round counter
            st.session_state.dialogue_round += 1

        # ----------------------- Conversation Rounds or Evaluation -----------------------
        if st.session_state.dialogue_round < MAX_DIALOGUES:
            run_conversation_round()
            time.sleep(0.5)  # Optional pause before the next round
            st.rerun()  # Automatically start the next conversation round
        else:
            st.write("### Conversation ended.")
            st.write("### Evaluating conversation...")
            evaluation = evaluate_conversation(st.session_state.messages_history, scenario)
            st.write("**Evaluation:**", evaluation)
            # Optionally play back the evaluation using TTS:
            # tts_threaded_playback(evaluation, voice="am_michael", max_chunk_length=100)
