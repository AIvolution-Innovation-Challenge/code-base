# HR Onboarding Assistant

A personalized chat-based onboarding tool for HR professionals using Streamlit and Groq AI. This system provides interactive learning paths, progress tracking, and AI-assisted guidance for new HR employees.

## Features

- 🤖 AI-powered chat interface using Groq API
- 📚 Structured learning paths for HR roles
- 📊 Progress tracking and visualization
- 🎯 Module-based learning approach
- 💡 Interactive assessments and tasks
- 📋 Comprehensive HR content modules

## Prerequisites

- Python 3.8 or higher
- Groq API key
- Git (for version control)

## Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd hr-onboarding-assistant
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your Groq API key:
```
GROQ_API_KEY=your_groq_api_key_here
```

## Project Structure

```
hr-onboarding-assistant/
├── app.py                  # Main application file
├── learning_paths.json     # Learning path configurations
├── module_content.json     # Detailed module content
├── requirements.txt        # Project dependencies
├── .env                    # Environment variables
└── progress_files/         # User progress storage
```

## Configuration Files

### requirements.txt
```
streamlit==1.32.0
groq==0.4.0
python-dotenv==1.0.0
```

### learning_paths.json and module_content.json
These files contain the structured content for the HR onboarding program. They define:
- Learning modules and their order
- Topic content and resources
- Assessment criteria
- Completion requirements

## Running the Application

1. Make sure your virtual environment is activated

2. Start the Streamlit application:
```bash
streamlit run app.py
```

3. Access the application in your web browser at `http://localhost:8501`


## 📌 MongoDB Integration
We have implemented MongoDB for document storage and retrieval.

📌 **[View Full Documentation](docs/mongodb-integration.md)**


## Usage Guide

### For Administrators

1. **Content Management**:
   - Modify `learning_paths.json` to adjust learning paths
   - Update `module_content.json` to modify module content
   - Changes will be reflected automatically on next app restart

2. **Adding New Modules**:
   - Add new module definitions to `module_content.json`
   - Update learning paths in `learning_paths.json` to include new modules
   - Follow existing JSON structure for consistency

3. **Monitoring Progress**:
   - User progress is stored in `progress_files/`
   - Each user has a separate progress file
   - Progress can be reset by deleting the respective file

### For Users

1. **Getting Started**:
   - Launch the application
   - Enter your questions or concerns in the chat interface
   - The AI assistant will guide you through your onboarding journey

2. **Navigation**:
   - Use the sidebar to track your progress
   - Current module and completion status are always visible
   - Click through different modules as needed

3. **Completing Modules**:
   - Follow the AI assistant's guidance
   - Complete all required tasks in each module
   - Take assessments when prompted
   - Progress is automatically saved

## Troubleshooting

1. **API Key Issues**:
   - Verify your Groq API key in the `.env` file
   - Ensure the environment variable is loaded correctly
   - Check API key permissions and quota

2. **Application Errors**:
   - Confirm all dependencies are installed
   - Verify JSON files are properly formatted
   - Check progress file permissions

3. **Common Solutions**:
   - Restart the application
   - Clear browser cache
   - Recreate virtual environment
   - Update dependencies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your chosen license]

## Support

For support, please [contact information or link to support resources]
