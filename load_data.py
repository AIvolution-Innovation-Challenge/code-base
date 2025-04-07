import streamlit as st
import sqlite3
import os
import tempfile
import json
import time

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


def run_upload_data(conn, cursor, client, logger):
    st.title("Welcome! Upload training documents for your employees here")
    st.write("Upload your PDF or DOCX files by dragging and dropping them below.")

    # Business role selection widget
    business_role = st.selectbox(
        "Select the business role for these documents:",
        ["Business Analyst", "Data Scientist", "Manager", "Other"]
    )

    # File uploader widget (accepts multiple files)
    uploaded_files = st.file_uploader("Choose files", type=["pdf", "docx"], accept_multiple_files=True)

    def generate_questions(doc_text: str) -> list:
        """
        Generate 10 multiple-choice questions based on the provided document text
        using GROQ's llama3-8b-8192. Each question should have four options labeled A, B, C, D,
        with the correct answer indicated. The response is expected to be in JSON format,
        a list of objects with keys: 'question', 'options', and 'answer'.
        """
        system_prompt = (
            "You are an expert in creating multiple-choice questions for training purposes. "
            "Based on the provided text, generate 10 multiple-choice questions. "
            "Each question must include four answer options labeled A, B, C, and D, and clearly indicate "
            "the correct answer. Format your response strictly as a JSON list of objects, where each object has the keys: "
            "'question', 'options', and 'answer'. Do not include any other text, explanations, or formatting outside of this JSON structure.\n"
            "For example:\n"
            '[{"question": "What is ...?", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}, "answer": "A"}, ...]\n'
            "Please ensure that your response is **only** in the following JSON format without any extra explanation."
        )
        
        user_message = f"Document text:\n{doc_text}\n\nPlease generate the questions."
        
        attempts = 0
        max_attempts = 5
        while attempts < max_attempts:
            try:
                response = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ]
                )
                questions_str = response.choices[0].message.content.strip()
                questions = json.loads(questions_str)
                return questions
            except json.JSONDecodeError as e:
                st.error(f"Error parsing generated questions. Attempt {attempts + 1}/{max_attempts} failed: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
            attempts += 1
            time.sleep(2)
        st.error("Failed to generate valid questions after multiple attempts.")
        return []

    # Process documents and generate questions when the button is clicked
    if st.button("Process Documents"):
        if uploaded_files:
            documents = []
            # Create a temporary directory to save uploaded files
            with tempfile.TemporaryDirectory() as temp_dir:
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(temp_dir, uploaded_file.name)
                    # Save the uploaded file to disk
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Process file based on its extension
                    if uploaded_file.name.lower().endswith(".pdf"):
                        loader = PyPDFLoader(file_path)
                        docs = loader.load()
                        for d in docs:
                            # Add the filename as metadata (source)
                            d.metadata["source"] = uploaded_file.name
                        documents.extend(docs)
                    elif uploaded_file.name.lower().endswith(".docx"):
                        loader = Docx2txtLoader(file_path)
                        docs = loader.load()
                        for d in docs:
                            d.metadata["source"] = uploaded_file.name
                        documents.extend(docs)
            
            # Log document upload event
            for uploaded_file in uploaded_files:
                logger.log_event(
                    user_id=st.session_state.username,
                    page="Upload Docs",
                    action="Uploaded Document",
                    details=f"Document: {uploaded_file.name}, Role: {business_role}"
                )
            
            # Split documents into chunks and create a FAISS vector store
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=600,
                chunk_overlap=50,
                length_function=len,
            )
            processed_docs = text_splitter.split_documents(documents)
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
            vector_store = FAISS.from_documents(processed_docs, embeddings)
            vector_store.save_local("faiss_index")
            
            # Insert each processed document into the SQLite database
            for doc in processed_docs:
                cursor.execute('''
                    INSERT INTO processed_docs (page_content, metadata, business_role)
                    VALUES (?, ?, ?)
                ''', (doc.page_content, str(doc.metadata), business_role))
            
            conn.commit()
            st.success("Documents processed and stored successfully!")
            
            # Log document processing event
            logger.log_event(
                user_id=st.session_state.username,
                page="Upload Docs",
                action="Processed Documents",
                details=f"Processed {len(uploaded_files)} documents for role: {business_role}"
            )
            
            # Combine full text for each uploaded document (grouped by file/source)
            combined_texts = {}
            for doc in documents:
                source = doc.metadata.get("source", "unknown")
                if source not in combined_texts:
                    combined_texts[source] = ""
                combined_texts[source] += "\n" + doc.page_content
            
            # Generate questions for each document and store them in session state
            all_questions = {}
            for source, full_text in combined_texts.items():
                st.write(f"Generating questions for document: {source}")
                questions = generate_questions(full_text)
                all_questions[source] = questions
            
            st.session_state.all_questions = all_questions
        else:
            st.warning("Please upload at least one file.")
            logger.log_event(
                user_id=st.session_state.username,
                page="Upload Docs",
                action="No Documents Uploaded",
                details="User attempted to process without uploading files."
            )

    # Display generated questions if they exist in session state
    if "all_questions" in st.session_state:
        st.header("Generated Multiple Choice Questions")
        for source, questions in st.session_state.all_questions.items():
            with st.expander(f"Questions for {source}"):
                for i, q in enumerate(questions, start=1):
                    st.markdown(f"**Q{i}: {q.get('question', 'No question text provided')}**")
                    options = q.get("options", {})
                    for option, text in options.items():
                        st.write(f"{option}: {text}")
                    st.write(f"**Answer:** {q.get('answer', 'Not provided')}")
                    # Checkbox for user to select if they want to keep this question
                    st.checkbox("Keep this question", key=f"keep_{source}_{i}")

    # Button to save selected questions to the database
    if st.button("Save Selected Questions"):
        # Re-open (or create) the database and ensure the questions table exists
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY,
                document_title TEXT,
                business_role TEXT,
                question TEXT,
                options TEXT,
                answer TEXT
            )
        ''')
        conn.commit()

        if "all_questions" in st.session_state:
            all_questions = st.session_state.all_questions
            saved_count = 0
            for source, questions in all_questions.items():
                for i, q in enumerate(questions, start=1):
                    if st.session_state.get(f"keep_{source}_{i}", False):
                        cursor.execute('''
                            INSERT INTO questions (document_title, business_role, question, options, answer)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            source,
                            business_role,
                            q.get("question", ""),
                            json.dumps(q.get("options", {})),
                            q.get("answer", "")
                        ))
                        saved_count += 1
            conn.commit()
            st.success(f"Saved {saved_count} selected questions to the database.")
        else:
            st.warning("No questions available to save.")

        conn.close()