import streamlit as st
import os
from typing import List, Dict
from datetime import datetime
import json
from groq import Groq

class OnboardingSystem:
    def __init__(self):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.learning_paths = self._load_learning_paths()


    def _load_learning_paths(self) -> Dict:
        """Load predefined learning paths from JSON files"""
        try:
            with open('learning_paths.json', 'r') as f:
                learning_paths = json.load(f)
            with open('module_content.json', 'r') as f:
                module_content = json.load(f)
                
            # Merge module content into learning paths
            for module in module_content:
                if module not in learning_paths['hr_generalist']['modules']:
                    learning_paths['hr_generalist']['modules'][module] = module_content[module]
                    
            return learning_paths
        except FileNotFoundError:
            # Fallback to default structure if files don't exist
            return {
                "hr_generalist": {
                    "modules": [
                        "company_policies",
                        "hr_systems",
                        "employee_relations",
                        "benefits_admin",
                        "recruitment",
                        "performance_mgmt"
                    ],
                    "required_completion": 100
                }
            }
        
    def get_ai_response(self, message: str, context: Dict) -> str:
        """Get response from Groq API"""
        try:
            system_prompt = f"""You are an HR onboarding assistant helping with {context['current_module']}.
            Current progress: {context['progress']}%.
            Expertise level: {context['expertise_level']}"""
            
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
            return f"Error: Unable to get response from AI. Please check your API key and connection. Details: {str(e)}"

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