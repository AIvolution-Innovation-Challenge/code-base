import streamlit as st
import requests

BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

def query_groq_model(prompt, model="mixtral-8x7b-32768"):
    api_key = st.secrets["groq"]["api_key"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,  # mixtral-8x7b-32768, llama2-70b-chat, gemma-7b-it
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }

    response = requests.post(BASE_URL, json=payload, headers=headers)
    response.raise_for_status()

    result = response.json()
    return result["choices"][0]["message"]["content"]
