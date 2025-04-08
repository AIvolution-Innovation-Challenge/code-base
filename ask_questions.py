import streamlit as st
import sqlite3
from typing import Dict
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

class OnboardingSystem:
    def __init__(self, client):
        self.client = client

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
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ]
            )
            return response.choices[0].message.content.strip().lower()

        try:
            query_type = classify_query(message)
            job_role = context.get("business_role", "Employee")
            
            if query_type == "job":
                retrieved_docs = st.session_state.faiss_retriever.get_relevant_documents(message)
                retrieved_context = "\n\n".join([doc.page_content for doc in retrieved_docs])
                system_prompt = (
                    f"You are an HR onboarding assistant. The following context is retrieved from the company's documents:\n\n"
                    f"{retrieved_context}\n\n"
                    f"Now answer the user's question related to the role of a {job_role}."
                )
            else:
                system_prompt = "You are a friendly HR onboarding assistant answering general queries and engaging in conversation."
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: Unable to get response from AI. Details: {str(e)}"

class UserSession:
    def __init__(self, id: str):
        self.id = id
        self.progress = self._load_progress()

    def _load_progress(self) -> Dict:
        business_role = st.sidebar.selectbox(
            "Select your Business Role", 
            ["Business Analyst", "Data Scientist", "Manager", "Other"], 
            index=0
        )
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT metadata FROM processed_docs WHERE business_role = ?", 
            (business_role,)
        )
        docs = cursor.fetchall()
        document_titles = list({eval(doc[0]).get("source", "") for doc in docs if doc[0]})
        
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
    

def initialize_session_state(client):
    if 'onboarding_system' not in st.session_state:
        st.session_state.onboarding_system = OnboardingSystem(client)
    if 'user_session' not in st.session_state:
        st.session_state.user_session = UserSession("test_user")
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'faiss_retriever' not in st.session_state:
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        try:
            vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
            st.session_state.faiss_retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})
        except Exception:
            st.warning("FAISS index not found. Please ensure it's generated correctly.")

def run_ask_questions(client, logger):
    st.title("Your HR Onboarding Assistant")
    initialize_session_state(client)
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    prompt = st.chat_input("What would you like to know about your role?")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        context = {"business_role": st.session_state.user_session.progress["business_role"]}
        
        logger.log_event(
            user_id=st.session_state.username,
            page="AI Assistant",
            action="User Query",
            details=f"Query: {prompt}"
        )
        
        with st.chat_message("assistant"):
            response = st.session_state.onboarding_system.get_ai_response(prompt, context)
            st.markdown(response)
        
        logger.log_event(
            user_id=st.session_state.username,
            page="AI Assistant",
            action="AI Response",
            details=f"Response: {response}"
        )
        
        st.session_state.messages.append({"role": "assistant", "content": response})
    
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