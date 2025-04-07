import streamlit as st
import sqlite3
import os
import json
from groq import Groq
import re

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["GROQ_API_KEY"] = "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"
client = Groq(api_key=os.environ["GROQ_API_KEY"])

def get_ai_response(message, messages_history, system_prompt):
    messages = [{"role": "system", "content": system_prompt}] + messages_history + [{"role": "user", "content": message}]
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

# Ensure the scenarios table exists in your SQLite database.
conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS scenarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        conversation_type TEXT,
        persona_ai TEXT,
        persona_user TEXT,
        scenario_description TEXT,
        system_prompt TEXT,
        evaluation_criteria TEXT,
        business_role TEXT
    )
""")
conn.commit()

def run_generate_scenario_module(conn, cursor, logger):
    st.title("Customer Service Agent Support Scenario Input")
    
    # --- Generate Scenario with AI Section ---
    st.header("Generate Scenario with AI")
    ai_input = st.text_area("Enter a brief description of the scenario you want to generate",
                            "Provide your scenario description here...")
    
    if st.button("Generate"):
        with st.spinner("Generating scenario..."):
            # Define a detailed system prompt instructing the AI to output a JSON object.
            ai_system_prompt = (
                "You are an expert scenario generator for workplace training simulations. "
                "Your task is to generate realistic roleplay scenarios in JSON format. "
                "Return only a valid JSON object with the following keys: "
                "`name`, `conversation_type`, `persona_ai`, `persona_user`, `scenario_description`, `system_prompt`, and `evaluation_criteria`.\n\n"
                "Each key should have rich, relevant content suitable for training customer service agents. "
                "Limit the length of each field to a reasonable size.\n\n"
                "Here is an example of the format and level of detail:\n"
                "{\n"
                "  \"name\": \"Sarah Williams - Overheating Laptop\",\n"
                "  \"conversation_type\": \"customer service\",\n"
                "  \"persona_ai\": \"Sarah Williams\",\n"
                "  \"persona_user\": \"customer support agent\",\n"
                "  \"scenario_description\": \"You are a customer support agent. You just received a call from a customer. Try to help her solve her issue!\",\n"
                "  \"system_prompt\": \"You are Sarah Williams, a 37-year-old Project Manager at a mid-sized tech firm.\\n"
                "You recently purchased a TechMaster Pro 15X laptop on March 12, 2025 for $1,899 USD from the TechMaster Official Online Store.\\n"
                "Your invoice number is TM-INV-58743921 and the laptop comes with a 2-year extended warranty with on-site support.\\n"
                "Specifications:\\n"
                "- Processor: Intel Core i9-13900H (14-core, up to 5.4GHz)\\n"
                "- RAM: 32GB DDR5\\n"
                "- Storage: 1TB NVMe SSD\\n"
                "- Graphics: NVIDIA GeForce RTX 4070 8GB\\n"
                "- Display: 15.6” 4K UHD (3840x2160) IPS, 120Hz\\n"
                "- Operating System: Windows 11 Pro\\n\\n"
                "You are experiencing issues with your laptop: it overheats, shuts down unexpectedly during video calls or heavy multitasking, and the fans are unusually loud.\\n"
                "You have already tried updating drivers, cleaning vents, and running diagnostics, but the problems persist.\\n"
                "You're disappointed and under pressure — you rely on this laptop for critical work and meetings.\\n"
                "This is a phone conversation, so speak briefly and conversationally. Limit your replies to 2 sentences.\\n"
                "DO NOT give any details regarding the laptop unless asked. When asked for details, only give details relevant to the question.\",\n"
                "  \"evaluation_criteria\": \"Evaluate the customer support agent’s performance based on the following 3 criteria. Assign a score from 1 to 5 for each (higher is better), and provide a brief justification. Total score should be out of 15. DON'T USE line breaks in your response.\\n\\n"
                "1. Empathy and Tone (1–5):\\n"
                "Did the agent acknowledge the customer's frustration? Was their tone polite, understanding, and respectful throughout?\\n\\n"
                "2. Clarity and Communication (1–5):\\n"
                "Were the agent’s responses clear, concise, and easy to follow? Did they avoid jargon and explain steps well?\\n\\n"
                "3. Problem-Solving and Initiative (1–5):\\n"
                "Did the agent take meaningful steps to resolve the issue, ask relevant questions, and/or escalate when appropriate?\\n\\n"
                "Respond in this format:\\n\\n"
                "Good work with the conversation! Here is how you did.\\n"
                "For Empathy and Tone, you scored [X out of 5]. [Short comment]\\n"
                "For Clarity and Communication, you scored[X out of 5]. [Short comment]\\n"
                "For Problem-Solving and Initiative, you scored [X out of 5]. [Short comment]\\n"
                "Hence, your total score is [X out of 15]\"\n"
                "}\n\n"
                "Use the above as a reference, but generate a new and original scenario."
            )
    
            try:
                generated_output = get_ai_response(ai_input, messages_history=[], system_prompt=ai_system_prompt)
                cleaned_json = extract_json_block(generated_output)
                if not cleaned_json:
                    raise ValueError("No JSON block found in AI response.")
                scenario_data = json.loads(cleaned_json)
                # Store generated data in session state so that the form fields are pre-filled.
                st.session_state["name"] = scenario_data.get("name", "")
                st.session_state["conversation_type"] = scenario_data.get("conversation_type", "")
                st.session_state["persona_ai"] = scenario_data.get("persona_ai", "")
                st.session_state["persona_user"] = scenario_data.get("persona_user", "")
                st.session_state["scenario_description"] = scenario_data.get("scenario_description", "")
                st.session_state["system_prompt"] = scenario_data.get("system_prompt", "")
                st.session_state["evaluation_criteria"] = scenario_data.get("evaluation_criteria", "")
                st.success("Scenario generated successfully!")
            except Exception as e:
                st.error("Error generating scenario: " + str(e))
    
    # --- Form Section ---
    st.header("Scenario Details")
    
    name = st.text_input("Name", st.session_state.get("name", ""))
    conversation_type = st.text_input("Conversation Type", st.session_state.get("conversation_type", ""))
    persona_ai = st.text_input("Persona (AI)", st.session_state.get("persona_ai", ""))
    persona_user = st.text_input("Persona (User)", st.session_state.get("persona_user", ""))
    scenario_description = st.text_area("Scenario Description", st.session_state.get("scenario_description", ""))
    system_prompt = st.text_area("System Prompt", st.session_state.get("system_prompt", ""))
    evaluation_criteria = st.text_area("Evaluation Criteria", st.session_state.get("evaluation_criteria", ""))
    business_role = st.text_input("Business Role", "")
    
    if st.button("Submit Scenario"):
        cursor.execute("""
            INSERT INTO scenarios (name, conversation_type, persona_ai, persona_user, scenario_description, system_prompt, evaluation_criteria, business_role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, conversation_type, persona_ai, persona_user, scenario_description, system_prompt, evaluation_criteria, business_role))
        conn.commit()
        st.success("Scenario added successfully!")

# To run this module in your main app, simply call:
# run_generate_scenario_module(conn, cursor)
