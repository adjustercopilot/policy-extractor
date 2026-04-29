# 🚀 DocuMind AI

DocuMind AI is an intelligent document processing application that allows users to upload documents, extract structured data, and ask follow-up questions using AI powered by Google Gemini.

---

## ✨ Features

- 📄 Upload and process documents (Policy, Driving License PDFs etc).
- 🤖 AI-powered data extraction using Gemini
- ❓ Ask follow-up questions on uploaded documents
- 📊 Visualize extracted data with confidence scores
- ⚡ FastAPI backend for scalable APIs
- 🎨 Streamlit frontend for interactive UI

---

## 🏗️ Tech Stack

- **Backend:** FastAPI  
- **Frontend:** Streamlit  
- **AI Model:** Google Gemini (gemini-2.5-flash)  
- **Visualization:** Plotly  
- **Language:** Python  

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository

```bash
git clone https://github.com/shivam-vecto/policy-extractor.git
cd policy-extractor
```

### 2️⃣ Create virtual environment

```bash
venv\Scripts\activate
```
### Activate it:
### Windows:
```bash
venv\Scripts\activate
```
### Mac/Linux:
```bash
source venv/bin/activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Set Environment Variables

Create a .env file or set environment variable:
```bash
GEMINI_API_KEY=your_api_key_here
```

### ▶️ Running the Application
#### 🔹 Run both backend & frontend (local)

```bash
python run.py
```
FastAPI will run on: http://127.0.0.1:8000
Streamlit will run on: http://localhost:8501

#### 🔹 Run individually
### Backend:
```bash
uvicorn main:app --reload
```
### Frontend:
```bash
streamlit run streamlit_app.py
```
# ⚠️ Known Issues
- Gemini free-tier API has strict rate limits (429 error)
- Limited number of requests per minute/day
- Recommended to enable billing for production usage

