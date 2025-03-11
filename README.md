# Revolutionizing Employee Onboarding with AI

This project is part of [NUS-Guru Network AI Innovation Challenge 2025](https://www.sg-innovationchallenge.org) and aims to transform employee onboarding using AI. The system makes onboarding faster, smarter, and more engaging by leveraging OpenAI's API and vector search with FAISS. Users can upload documents, ask questions, and retrieve AI-generated answers based on the stored content.

## Features
- AI-powered employee onboarding assistance
- Upload and process PDF and DOCX documents
- Store and retrieve document embeddings using FAISS
- Ask AI-powered questions based on stored documents
- Log and track user interactions and responses

## Prerequisites
Ensure you have the following installed:
- Python 3.8+
- `pip` (Python package manager)
- OpenAI API key (set as an environment variable)

## Installation
```sh
# Clone the repository
git clone <repository-url>
cd <project-directory>

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install required dependencies
pip install -r requirements.txt
```

## Environment Variables
Ensure the OpenAI API key is set before running the application:
```sh
export OPENAI_API_KEY="your-api-key-here"  # On Windows, use `set OPENAI_API_KEY=your-api-key-here`
```

## Usage

### 1. Load Data
Run the following command to start the document upload interface:
```sh
streamlit run load_data.py
```
Upload PDF or DOCX files. These will be processed and stored in the SQLite database (`documents.db`).

### 2. Ask Questions
To query the uploaded documents, run:
```sh
streamlit run ask_questions.py
```
This will launch an interactive Q&A interface where users can ask questions and receive AI-generated responses based on the stored documents.

### 3. Log Responses
To view and analyze logged interactions, run:
```sh
streamlit run answer_questions.py
```
This will allow you to track submitted responses and log AI interactions.

## Database (`documents.db`)
The SQLite database stores:
- Processed documents and their embeddings
- User questions and responses
- Metadata (timestamps, scores, etc.)

## Dependencies
The following key libraries are used:
- `Streamlit` (for UI components)
- `sqlite3` (for database storage)
- `LangChain` (for document processing and vector search)
- `FAISS` (for fast retrieval of relevant document segments)
- `HuggingFaceEmbeddings` (for embeddings generation)
- `OpenAI API` (for question-answering)

## License
This project is licensed under the MIT License.

## Acknowledgments
Special thanks to OpenAI and Hugging Face for their NLP capabilities.

