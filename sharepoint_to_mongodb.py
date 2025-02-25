import os
import gridfs
from pymongo import MongoClient
from docx import Document  # Import the library to read DOCX files
import mimetypes

# 🔹 Connect to MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["hr_chatbot"]
collection = db["documents"]
fs = gridfs.GridFS(db)  # Use GridFS for storing full DOCX files

# 🔹 Local folder where DOCX files are stored
folder_path = "/Users/snehamore/Downloads/Roles and Responsibilities Documents/Roles and Responsibilities"

def extract_text_from_docx(file_path):
    """Extracts and returns text from a DOCX file."""
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])  # Join all paragraphs
    except Exception as e:
        print(f"❌ Failed to extract text from {file_path}: {e}")
        return None

for file_name in os.listdir(folder_path):
    file_path = os.path.join(folder_path, file_name)

    mime_type, _ = mimetypes.guess_type(file_path)  # Detect file type
    is_docx = mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    if is_docx:
        # 🔹 Extract text from DOCX
        file_content = extract_text_from_docx(file_path)

        if file_content:
            # 🔹 Store extracted text in MongoDB
            doc = {
                "file_name": file_name,
                "content": file_content
            }
            collection.insert_one(doc)
            print(f"✅ Stored TEXT in MongoDB: {file_name}")
        
        # 🔹 Store the full DOCX file in GridFS
        with open(file_path, "rb") as f:
            file_id = fs.put(f, filename=file_name)
        print(f"✅ Stored FULL DOCX in GridFS: {file_name}")

    else:
        print(f"⚠️ Skipped non-DOCX file: {file_name}")

print("✅ All DOCX files are now processed & stored in MongoDB!")
