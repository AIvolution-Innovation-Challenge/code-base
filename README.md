# 🤖 AIvolution – AI-Powered Employee Onboarding

A submission for the [NUS-Guru Network AI Innovation Challenge 2025](https://www.sg-innovationchallenge.org), **AIvolution** reimagines the employee onboarding process through the power of AI. This solution offers an engaging, voice-enabled, and analytics-rich platform to onboard employees effectively, especially in hybrid or digitally diverse work environments.

---

## 🚀 Key Features

- 🎙️ **Voice Assistant Onboarding**: AI assistant trained on company documents to answer policy-related questions via voice interface.
- 📊 **Interactive HR Dashboard**: Track quiz scores, document compliance, and chat insights.
- 📁 **Smart Content Management**: Upload PDFs and train the assistant for role-specific or company-wide onboarding.
- 🧠 **AI-Powered Search**: Uses OpenAI + FAISS to retrieve accurate responses based on company documents.
- 📈 **Per Role & Department Analytics**: Visualize quiz performance by role and department.

---

## 🏗️ Folder Structure

```
AIvolution_Source_Code/
├── hr_dashboard.py                 # Streamlit-based HR dashboard
├── ask_questions.py               # Chat interface for document Q&A
├── answer_questions.py            # Handles embedding search and answer generation
├── voice_assistant_trainer_with_voice.py # Main voice assistant logic
├── create_dummy_users.py          # Utility to generate test users
├── seed_dummy_data.py             # Seeds initial document and quiz data
├── logger.py                      # Logging utility
├── requirements.txt               # Python dependencies
├── aivolution_logo.jpeg           # Branding asset
└── README.md                      # Project documentation
```

---

## ⚙️ How It Works

1. **Upload documents** via the dashboard or file system.
2. **Train AI Assistant** using embeddings powered by FAISS and OpenAI.
3. **Employees interact** with the AI via voice or chat, asking real-world onboarding questions.
4. **Track compliance** through the dashboard, including quiz completions and chat activity.
5. **Gain insights** from role-based quiz and training performance analytics.

---

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/aivolution.git
   cd aivolution
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   ```bash
   brew install espeak-ng ffmpeg
   ```


3. Run the app:
   ```bash
   streamlit run main_app.py
   ```

---

## 🧪 Tech Stack

- **Python**
- **Streamlit** – UI and dashboard
- **OpenAI API** – Language intelligence
- **FAISS** – Vector search for document retrieval
- **SQLite** – Local database
- **Pyttsx3 / SpeechRecognition** – Voice I/O

---

## 💡 Ideal For

- Organizations with **complex onboarding policies**
- Teams needing **24/7 onboarding support**
- **Hybrid or frontline workforces**
- Employees with **accessibility or low digital literacy**

---

## 👥 Contributors

This project was developed as part of the NUS MSBA cohort for the Guru Innovation Challenge 2025.
