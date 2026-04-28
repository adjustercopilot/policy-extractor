# main.py - Consolidated Document Identification and Extraction API
import os
import uuid
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import PyPDF2
from io import BytesIO
import requests

# Load environment variables
load_dotenv()

# Get Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize FastAPI
app = FastAPI(
    title="Intelligent Document Extractor",
    description="Single-API call to identify and extract data from documents using Gemini AI",
    version="4.1.0"
)

# Store extracted data in memory (for demonstration/Q&A)
extracted_documents = {}

class QuestionRequest(BaseModel):
    question: str
    document_id: Optional[str] = None

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    try:
        pdf_file = BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page_num, page in enumerate(pdf_reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Page {page_num} ---\n{page_text}"
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

def identify_and_extract_logic(pdf_text: str, forced_type: str = None, custom_fields: List[str] = None) -> Dict[str, Any]:
    """
    Performs a single-pass API call to Gemini to identify document type 
    and extract data simultaneously.
    """
    if not GEMINI_API_KEY:
        return {"error": "Gemini API key not configured"}

    prompt = f"""
    Analyze the following document text and perform two tasks:
    1. Identify the document type: INSURANCE_POLICY, DRIVING_LICENSE, IDENTITY_CARD, 
       VEHICLE_REGISTRATION, BANK_STATEMENT, TAX_DOCUMENT, EMPLOYMENT_CONTRACT, 
       LEASE_AGREEMENT, INVOICE, CERTIFICATE, or OTHER.
    2. Extract relevant structured data based on that type.

    Specific Instructions:
    - Forced Type (if any): {forced_type}
    - Custom Fields (if any): {custom_fields}

    Document text (up to 15000 chars):
    {pdf_text[:15000]}

    Return ONLY valid JSON in this format:
    {{
        "identification": {{
            "document_type": "TYPE_HERE",
            "confidence": 0.95,
            "reasoning": "Brief explanation"
        }},
        "extracted_data": {{
            "key1": "value1",
            "key2": "value2"
        }}
    }}
    """

    # UPDATED MODEL NAME from your curl output
    model_name = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1, 
            "response_mime_type": "application/json"
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=45)
        if response.status_code == 200:
            result = response.json()
            raw_text = result['candidates'][0]['content']['parts'][0]['text']
            return json.loads(raw_text)
        else:
            return {"error": f"Gemini API returned status {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": f"Processing failed: {str(e)}"}

@app.post("/extract")
async def extract_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Query(None),
    custom_fields: Optional[str] = Query(None)
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    content = await file.read()
    pdf_text = extract_text_from_pdf(content)
    
    if not pdf_text:
        raise HTTPException(status_code=400, detail="Document appears to be empty or unreadable")

    fields_list = [f.strip() for f in custom_fields.split(",")] if custom_fields else None
    result = identify_and_extract_logic(pdf_text, document_type, fields_list)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    doc_id = str(uuid.uuid4())[:8]
    extracted_documents[doc_id] = {
        "id": doc_id,
        "filename": file.filename,
        "document_type": result["identification"]["document_type"],
        "extracted_data": result["extracted_data"],
        "full_text": pdf_text,
        "timestamp": datetime.now().isoformat()
    }

    return {
        "success": True,
        "document_id": doc_id,
        "identification": result["identification"],
        "extracted_data": result["extracted_data"]
    }

@app.post("/ask")
async def ask_document(request: QuestionRequest):
    if not extracted_documents:
        raise HTTPException(status_code=404, detail="No documents uploaded.")

    doc = extracted_documents.get(request.document_id) or list(extracted_documents.values())[-1]

    prompt = f"""
    Answer the following question using only the provided data from a {doc['document_type']}.
    Data: {json.dumps(doc['extracted_data'])}
    Question: {request.question}
    """

    model_name = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, json=payload, timeout=30)
        answer = response.json()['candidates'][0]['content']['parts'][0]['text']
        return {"answer": answer.strip(), "document_id": doc['id']}
    except:
        raise HTTPException(status_code=500, detail="QA failed.")

@app.get("/health")
async def health():
    return {"status": "online", "model_used": "gemini-2.5-flash"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)