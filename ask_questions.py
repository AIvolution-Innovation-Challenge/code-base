import streamlit as st
import os
import json
import sqlite3
from typing import Dict
from datetime import datetime
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import openai

def run_ask_questions():
    # Set your API key for OpenAI
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # -------------------------------------------------------------------
    # 1. OnboardingSystem: Removed load_learning_paths; only get_ai_response remains.
    class OnboardingSystem:
        def get_ai_response(self, message: str, context: Dict) -> str:
            def classify_query(user_query: str) -> str:
                system_prompt = (
                    "You are a classifier for an HR onboarding tool. "
                    "Categorize the user input into one of these two categories:\n"
                    "- 'job': For queries about company policies, benefits, work responsibilities, "
                    "or technical skills (e.g., SQL, Python).\n"
                    "- 'general': For greetings, small talk, or other non-job related queries.\n"
                    "Respond with only one word: 'job' or 'general'."
                )
                user_message = f"User input: {user_query}\n\nClassify the input:"
                response = openai.ChatCompletion.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ]
                )
                return response["choices"][0]["message"]["content"].strip().lower()

            try:
                query_type = classify_query(message)
                if query_type == "job":
                    # Retrieve relevant documents from FAISS
                    retrieved_docs = st.session_state.faiss_retriever.get_relevant_documents(message)
                    retrieved_context = "\n\n".join([doc.page_content for doc in retrieved_docs])
                    system_prompt = (
                        f"You are an HR onboarding assistant. The following context is retrieved from the company's documents:\n\n"
                        f"{retrieved_context}\n\n"
                        f"Now answer the user's question related to {context.get('current_module', 'company_policies')}."
                    )
                else:
                    system_prompt = "You are a friendly HR onboarding assistant answering general queries and engaging in conversation."
                # Include the last few messages to maintain context
                max_messages = 3
                recent_messages = st.session_state.messages[-max_messages:]
                messages = [{"role": "system", "content": system_prompt}] + recent_messages + [{"role": "user", "content": message}]
                response = openai.ChatCompletion.create(
                    model="gpt-4-turbo",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                return response.choices[0].message["content"]
            except Exception as e:
                return f"Error: Unable to get response from AI. Please check your API key and connection. Details: {str(e)}"

    # -------------------------------------------------------------------
    # 2. UserSession: Now load progress from the database and allow business role selection.
    class UserSession:
        def __init__(self, user_id: str):
            self.user_id = user_id
            self.progress = self._load_progress()
            
        def _load_progress(self) -> Dict:
            # Let user choose their business role (default "Business Analyst")
            business_role = st.sidebar.selectbox(
                "Select your Business Role", 
                ["Business Analyst", "Data Scientist", "Manager", "Other"], 
                index=0
            )
            # Connect to the database to load document titles from processed_docs
            conn = sqlite3.connect("documents.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT metadata FROM processed_docs WHERE business_role = ?", 
                (business_role,)
            )
            docs = cursor.fetchall()
            document_titles = []
            for doc in docs:
                try:
                    # metadata was stored as a string representation of a dict.
                    meta = eval(doc[0])
                    if "source" in meta:
                        document_titles.append(meta["source"])
                except Exception:
                    pass
            document_titles = list(set(document_titles))
            
            # Query completed modules from the results table for this business role.
            cursor.execute(
                "SELECT DISTINCT document_title FROM results WHERE business_role = ?", 
                (business_role,)
            )
            completed_docs = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            total = len(document_titles)
            completed = len(completed_docs)
            progress_percent = (completed / total * 100) if total > 0 else 0
            return {
                "overall_progress": progress_percent,
                "completed_modules": completed_docs,
                "all_documents": document_titles,
                "business_role": business_role
            }
        
        def save_progress(self):
            # Optionally, add logic here to save progress if needed.
            pass

    # -------------------------------------------------------------------
    # 3. Initialize session state variables, including the FAISS retriever.
    def initialize_session_state():
        if 'onboarding_system' not in st.session_state:
            st.session_state.onboarding_system = OnboardingSystem()
        if 'user_session' not in st.session_state:
            st.session_state.user_session = UserSession("test_user")
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'faiss_retriever' not in st.session_state:
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
            # Loads the saved FAISS index from local folder "faiss_index"
            vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
            st.session_state.faiss_retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 2})
    
    # -------------------------------------------------------------------
    # 4. Main function to display the chat interface and sidebar progress.
    def main():
        st.title("HR Onboarding Assistant")
        
        # Initialize session state
        initialize_session_state()
        
        # Display previous chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input widget
        prompt = st.chat_input("What would you like to know about your role?")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Build context (here we set current_module statically since learning paths are removed)
            context = {"current_module": "company_policies"}
            
            # Get AI response (with document retrieval if needed)
            with st.chat_message("assistant"):
                response = st.session_state.onboarding_system.get_ai_response(prompt, context)
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Display progress in the sidebar.
        with st.sidebar:
            st.header("Your Learning Progress")
            progress = st.session_state.user_session.progress
            st.write(f"Business Role: {progress['business_role']}")
            st.write(f"Total Documents: {len(progress['all_documents'])}")
            st.write(f"Completed Documents: {len(progress['completed_modules'])}")
            st.progress(progress["overall_progress"] / 100)
            st.write(f"Overall Progress: {progress['overall_progress']:.2f}%")
    
    # Run the main chat interface
    main()

if __name__ == "__main__":
    run_ask_questions()
