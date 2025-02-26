import streamlit as st
import os
from typing import Dict
import json
from pymongo import MongoClient
from groq import Groq
from fuzzywuzzy import process, fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np

# ✅ Ensure Streamlit UI loads correctly
st.title("HR Onboarding Assistant")

class OnboardingSystem:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.learning_paths = self._load_learning_paths()

    def _load_learning_paths(self) -> dict:
        """Load HR document content from MongoDB and create embeddings for better search."""
        learning_paths = {}

        # Connect to MongoDB
        mongo_client = MongoClient("mongodb://localhost:27017/")
        db = mongo_client["hr_chatbot"]
        collection = db["documents"]

        # Retrieve stored HR documents
        documents = list(collection.find({}))

        for doc in documents:
            file_name = doc["file_name"].replace(".docx", "").strip().lower()
            learning_paths[file_name] = doc["content"]

        print(f"📌 DOCUMENT TITLES LOADED FROM DB: {list(learning_paths.keys())}")

        # ✅ Define document names and content before using them
        self.doc_names = list(learning_paths.keys())
        self.doc_contents = list(learning_paths.values())

        # ✅ TF-IDF Vectorization
        custom_stopwords = ["vp", "manager", "director", "role", "responsibilities"]
        self.vectorizer = TfidfVectorizer(stop_words=custom_stopwords, max_df=0.6, min_df=0.05)
        self.doc_vectors = self.vectorizer.fit_transform(self.doc_contents)

        # ✅ Semantic Search Model
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.doc_embeddings = self.embedder.encode(self.doc_contents, normalize_embeddings=True)

        return learning_paths

    def get_ai_response(self, message: str, context: dict) -> str:
        """Find the best-matching document using Fuzzy Matching, TF-IDF, and Semantic Search."""
        query_lower = message.lower()
        print(f"🔍 QUERY: {message}")

        # ✅ Step 1: Fuzzy Matching (Fixed unpacking issue)
        fuzzy_matches = process.extract(query_lower, self.doc_names, limit=5, scorer=fuzz.WRatio)

        matched_doc = None
        if fuzzy_matches:
            best_match, fuzzy_score = fuzzy_matches[0]
            if fuzzy_score >= 85:
                matched_doc = best_match

        # ✅ Step 2: TF-IDF Matching
        ranked_tfidf = []
        if not matched_doc:
            query_vector = self.vectorizer.transform([message])
            similarities = cosine_similarity(query_vector, self.doc_vectors).flatten()
            ranked_tfidf = sorted(zip(self.doc_names, similarities), key=lambda x: x[1], reverse=True)

            best_match_idx = similarities.argmax()
            tfidf_score = similarities[best_match_idx]
            if tfidf_score >= 0.3:
                matched_doc = self.doc_names[best_match_idx]

        # ✅ Step 3: Semantic Search
        ranked_semantic = []
        if not matched_doc:
            query_embedding = self.embedder.encode([message], normalize_embeddings=True)
            similarities = cosine_similarity(query_embedding, self.doc_embeddings).flatten()
            ranked_semantic = sorted(zip(self.doc_names, similarities), key=lambda x: x[1], reverse=True)

            best_match_idx = np.argmax(similarities)
            semantic_score = similarities[best_match_idx]
            if semantic_score >= 0.3:
                matched_doc = self.doc_names[best_match_idx]

        # ✅ Final Selection: Ensure scoring works safely
        if ranked_tfidf and fuzzy_matches and ranked_semantic:
            combined_scores = {
                doc: 0.15 * tfidf_score + 0.15 * fuzzy_score + 0.7 * semantic_score
                for (doc, tfidf_score), (_, fuzzy_score), (_, semantic_score)
                in zip(ranked_tfidf, fuzzy_matches, ranked_semantic)
            }
            best_doc = max(combined_scores, key=combined_scores.get, default=None)
        else:
            best_doc = None

        if best_doc:
            matched_doc = best_doc

        if not matched_doc:
            return "I'm sorry, I couldn't find relevant information."

        return self.learning_paths[matched_doc]


# ✅ Ensure Streamlit Chatbot UI is correctly initialized
def initialize_session_state():
    if 'onboarding_system' not in st.session_state:
        st.session_state.onboarding_system = OnboardingSystem()
    if 'messages' not in st.session_state:
        st.session_state.messages = []

def main():
    initialize_session_state()

    # ✅ Show previous chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ✅ Input chat box
    if prompt := st.chat_input("What would you like to know?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # ✅ Get AI response
        with st.chat_message("assistant"):
            response = st.session_state.onboarding_system.get_ai_response(prompt, {})
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
