# 🚀 MongoDB Integration for HR Chatbot

## 📌 Overview
We modified the HR onboarding chatbot to **fetch HR policy documents from MongoDB** instead of relying on static JSON files.

### ✅ Key Changes:
- **Created a script (`sharepoint_to_mongodb.py`)** to import SharePoint `.docx` files into MongoDB.
- **Updated `main.py`** to query MongoDB for document content dynamically.
- **Improved document retrieval logic** to correctly match user queries to HR documents.

---

## 📌 Step 1: Import SharePoint Files into MongoDB

### 🔹 Created `sharepoint_to_mongodb.py`
This script:
1. Connects to **MongoDB** (`hr_chatbot` database).
2. Extracts text from `.docx` files.
3. Stores the extracted text in MongoDB for chatbot use.

**Run the script:**
```bash
python sharepoint_to_mongodb.py

