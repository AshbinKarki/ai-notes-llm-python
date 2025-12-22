<p align="center">
  <img src="assets/banner.png" alt="AI Powered Notes Management System" width="100%">
</p>


## AI-Powered Multi-User Notes Management System  
Backend: Flask + SQLite + LangChain + Ollama  
Frontend: Streamlit  
LLM: Open-Source (Llama 3 via Ollama)

---

## Project Overview

This project implements a **full-stack CRUD Notes Management System** that supports:

- Multi-user authentication  
- Note creation, reading, updating, and deletion  
- **Natural-language interaction using an open-source LLM**  
- Dashboard-style manual CRUD interface  
- Python Flask backend connected to SQLite  
- Frontend built using Streamlit  
- LangChain + Ollama used to process user instructions into structured SQL actions  

Users can either use:

1. **Manual Mode** → Normal Create/Read/Update/Delete buttons  
2. **AI Mode** → Natural language can be used to create/read/update and delete.


#Technology used

 | Component     | Technology                |
| ------------- | ------------------------- |
| Frontend      | Streamlit                 |
| Backend       | Flask                     |
| Database      | SQLite                    |
| ORM           | SQLAlchemy                |
| LLM           | Llama 3 via Ollama        |
| LLM Framework | LangChain                 |
| Security      | Werkzeug password hashing |
   

#Folder_Structure

project/
│
├── backend/
│   ├── app.py               # Flask backend
│   ├── models.py            # Database models
│   ├── llm_agent.py         # Natural Language → Structured Action
│   ├── notes.db             # SQLite database (auto-created)
│
└── frontend/
    ├── streamlit_app.py     # Streamlit UI

⚙️ Installation Instructions
Step 1: Install Python packages

        pip install -r requirements.txt

Step 2:Run ollama

       ollama pull llama3

Step 3:Run the Flask Backend

       cd backend
       python app.py        

Step 4:Run the Streamlit Frontend

       cd frontend
       streamlit run streamlit_app.py       



