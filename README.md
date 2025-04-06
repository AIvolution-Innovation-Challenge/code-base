# Revolutionizing Employee Onboarding with AI

This project is part of [NUS-Guru Network AI Innovation Challenge 2025](https://www.sg-innovationchallenge.org) and aims to transform employee onboarding using AI. The system makes onboarding faster, smarter, and more engaging by leveraging OpenAI's API and vector search with FAISS. Users can upload documents, ask questions, and retrieve AI-generated answers based on the stored content.

---

## 🚀 Features

- 📊 **Dashboard Overview**: Visual summary of quizzes, scores, documents, and chats.
- 📁 **Document & Quiz Compliance**: Track pending or overdue document completions.
- 💬 **Chat Insights**: Analyze chat activity and common user queries.
- 🧑‍💼 **Per Role Analysis**: Deep dive into quiz scores by job role.
- 🧠 **Quiz Analytics**: Score trends by department and document.
- 🧪 **SQLite Database** backend for storing users, quiz data, chat logs, and system logs.

---

## 🏗️ File Structure

```
📁 HR-Onboarding/
├── main_app.py              # Entry point for Streamlit app
├── hr_dashboard.py          # Contains the dashboard layout and logic
├── ask_questions.py         # Handles quiz/question serving
├── answer_questions.py      # Handles quiz submission and scoring
├── load_data.py             # Utility for loading documents and user data
├── db_utils.py              # DB helper functions (CRUD ops, settings)
├── logger.py                # Event logger for tracking user actions
├── seed_dummy_data.py       # Script to seed initial users, questions, etc.
└── documents.db             # SQLite database storing all app data
```

---

## ⚙️ Requirements

- Python 3.8+
- Streamlit
- pandas
- numpy
- plotly
- sqlite3 (standard with Python)
- (Optional) `python-dotenv` if using environment variables

Install dependencies using:

```bash
pip install -r requirements.txt
```

---

## 🧪 Setting Up Locally

1. **Clone the repo**
```bash
git clone https://github.com/your-username/hr-onboarding-dashboard.git
cd hr-onboarding-dashboard
```

2. **(Optional)** Seed the database with dummy data
```bash
python seed_dummy_data.py
```

3. **Run the Streamlit App**
```bash
streamlit run main_app.py
```

---

## 🧠 How It Works

- Users are loaded into the system with their start dates, departments, and business roles.
- Each role has associated documents (and quizzes).
- The dashboard helps track:
  - Which users haven't completed their required documents.
  - Quiz scores by role and department.
  - Commonly asked chat queries.
- The backend uses SQLite with various tables like:
  - `users`, `questions`, `results`, `chat_logs`, `logs`, `settings`

---

## 🔒 Security & Logging

- All major interactions are logged using the `logger.py` module.
- Chat logs and quiz scores are stored against user IDs.
- No PII is processed externally; all operations are local to the app instance.

---

## 📬 Feedback / Contributions

If you find a bug or have a feature request, feel free to open an issue or submit a pull request!

---
