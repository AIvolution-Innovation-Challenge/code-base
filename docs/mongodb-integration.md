# MongoDB Integration for HR Chatbot

## Overview
We modified the HR onboarding chatbot to **fetch HR policy documents from MongoDB** instead of relying on static JSON files.

### Key Changes:
- **Created a script (`sharepoint_to_mongodb.py`)** to import SharePoint `.docx` files into MongoDB.
- **Updated `main.py`** to query MongoDB for document content dynamically.
- **Improved document retrieval logic** to correctly match user queries to HR documents.
- **Fuzzy Matching (85%+ confidence required)** - Ensures partial matches.
- **TF-IDF (Term Frequency-Inverse Document Frequency)** - Prioritizes key words (e.g., “Supply Chain” is more important than “VP”).
- **Semantic Search (AI embeddings)** - Uses a neural network to rank results based on meaning.
-- **Final ranking system heavily favors Semantic Search (70%), with 15% each for Fuzzy & TF-IDF.**
---

## Step 1: Import SharePoint Files into MongoDB
## MongoDB Setup
- Ensure MongoDB is installed and running:
  mongod --dbpath /your/db/path
### Created `sharepoint_to_mongodb.py`
This script:
1. Connects to **MongoDB** (`hr_chatbot` database).
2. Extracts text from `.docx` files.
3. Stores the extracted text in MongoDB for chatbot use.
**Run the script:**
python sharepoint_to_mongodb.py

