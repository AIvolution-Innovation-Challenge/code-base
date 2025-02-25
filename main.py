import streamlit as st
import os
from typing import List, Dict
from datetime import datetime
import json
from pymongo import MongoClient
from groq import Groq


class OnboardingSystem:
    def __init__(self):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.learning_paths = self._load_learning_paths()

    def _load_learning_paths(self) -> dict:
        """Load HR document content from MongoDB"""
        learning_paths = {}

        # Connect to MongoDB
        mongo_client = MongoClient("mongodb://localhost:27017/")
        db = mongo_client["hr_chatbot"]
        collection = db["documents"]

        # Retrieve stored HR documents
        documents = collection.find({})
        for doc in documents:
            file_name = doc["file_name"].replace(".docx", "").strip().lower()  # Normalize name
            learning_paths[file_name] = doc["content"]

        print("📌 LOADED DOCUMENTS:", learning_paths.keys())  # Debug print
        return learning_paths

    def get_ai_response(self, message: str, context: dict) -> str:
        """Find the best-matching document for the user query"""
        
        query_lower = message.lower()

        # 🔹 Find the most relevant document based on query keywords
        matched_doc = None
        for doc_name in self.learning_paths.keys():
            if doc_name in query_lower:
                matched_doc = doc_name
                break  # Stop at the first match

        if matched_doc is None:
            return "I'm sorry, but I couldn't find specific information related to your query in our HR documents."

        module_content = self.learning_paths.get(matched_doc, "No information available.")

        print(f"📌 QUERY: {message}")
        print(f"📌 MATCHED DOCUMENT: {matched_doc}")
        print(f"📌 DOCUMENT CONTENT (First 500 chars): {module_content[:500]}")

        # Construct system prompt
        system_prompt = f"""You are an HR onboarding assistant.
        Here is information from company documents related to {matched_doc}:
        {module_content}
        Now answer the following question based on this information:
        """

        # Call Groq AI
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                model="mixtral-8x7b-32768",
                temperature=0.7,
                max_tokens=1000
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"Error fetching response: {str(e)}"


class UserSession:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.progress = self._load_progress()

    def _load_progress(self) -> Dict:
        """Load user progress from database (simplified with file storage for now)"""
        try:
            with open(f"progress_{self.user_id}.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "overall_progress": 0,
                "completed_modules": [],
                "current_module": "company_policies",
                "expertise_level": "beginner"
            }

    def save_progress(self):
        """Save current progress to storage"""
        with open(f"progress_{self.user_id}.json", "w") as f:
            json.dump(self.progress, f)


def initialize_session_state():
    """Initialize all session state variables"""
    if 'onboarding_system' not in st.session_state:
        st.session_state.onboarding_system = OnboardingSystem()

    if 'user_session' not in st.session_state:
        st.session_state.user_session = UserSession("test_user")

    if 'messages' not in st.session_state:
        st.session_state.messages = []


def main():
    st.title("HR Onboarding Assistant")

    # Initialize session state
    initialize_session_state()

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What would you like to know about your HR role?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Show user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            context = {
                "current_module": st.session_state.user_session.progress["current_module"],
                "progress": st.session_state.user_session.progress["overall_progress"],
                "expertise_level": st.session_state.user_session.progress["expertise_level"]
            }

            response = st.session_state.onboarding_system.get_ai_response(prompt, context)
            st.markdown(response)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Display progress sidebar
    with st.sidebar:
        st.header("Your Learning Progress")
        st.progress(st.session_state.user_session.progress["overall_progress"] / 100)
        st.write(f"Current Module: {st.session_state.user_session.progress['current_module']}")
        st.write(f"Completed Modules: {len(st.session_state.user_session.progress['completed_modules'])}")


if __name__ == "__main__":
    main()
