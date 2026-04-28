# main.py - Consolidated Document Identification and Extraction API
import os
import uuid
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from collections import defaultdict

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
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
    version="4.2.0"
)

# Add CORS middleware for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store extracted data in memory with enhanced structure
extracted_documents = {}
conversation_history = defaultdict(list)  # Store Q&A history per document

class QuestionRequest(BaseModel):
    question: str
    document_id: Optional[str] = None
    include_history: bool = True

class BatchQuestionRequest(BaseModel):
    questions: List[str]
    document_id: Optional[str] = None

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file with better error handling"""
    try:
        pdf_file = BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        if len(pdf_reader.pages) == 0:
            raise HTTPException(status_code=400, detail="PDF has no pages")
        
        text = ""
        metadata = {
            "num_pages": len(pdf_reader.pages),
            "has_form_fields": False
        }
        
        for page_num, page in enumerate(pdf_reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Page {page_num} ---\n{page_text}"
            else:
                text += f"\n--- Page {page_num} ---\n[No extractable text found]"
        
        return text.strip(), metadata
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

def identify_and_extract_logic(pdf_text: str, forced_type: str = None, custom_fields: List[str] = None) -> Dict[str, Any]:
    """
    Performs a single-pass API call to Gemini to identify document type 
    and extract data simultaneously.
    """
    if not GEMINI_API_KEY:
        return {"error": "Gemini API key not configured. Please check your .env file."}

    # Enhanced prompt with better instructions
    prompt = f"""
    You are an expert document analysis AI. Analyze the following document text and perform two tasks:

    TASK 1: Document Identification
    Identify the document type from these categories:
    - INSURANCE_POLICY (car, health, life, home insurance)
    - DRIVING_LICENSE (driver's license, learner's permit)
    - IDENTITY_CARD (passport, national ID, resident card)
    - VEHICLE_REGISTRATION (car registration, title deed)
    - BANK_STATEMENT (bank account statement, transaction history)
    - TAX_DOCUMENT (tax return, W-2, 1099, T4)
    - EMPLOYMENT_CONTRACT (job offer, employment agreement)
    - LEASE_AGREEMENT (rental agreement, lease contract)
    - INVOICE (bill, receipt, purchase order)
    - CERTIFICATE (diploma, degree, certification)
    - OTHER (any other document type)

    TASK 2: Data Extraction
    Extract relevant structured data based on the document type. Common fields include:
    - Names (person names, company names)
    - Dates (issue date, expiry date, effective date, dates of birth)
    - Numbers (policy numbers, account numbers, identification numbers)
    - Addresses (physical addresses, email addresses)
    - Monetary amounts (premiums, balances, payments)
    - Legal terms (clauses, conditions, restrictions)

    Specific Instructions:
    {"- Forced Document Type: " + forced_type if forced_type else "- Auto-detect document type"}
    {"- Custom Fields to Extract: " + ", ".join(custom_fields) if custom_fields else "- Extract all relevant fields"}
    
    - Confidence score should reflect how certain you are about the document type (0.0 to 1.0)
    - Provide brief reasoning for your identification
    - Return ONLY valid JSON without markdown formatting or extra text

    Document text (first 20000 characters):
    {pdf_text[:20000]}

    Return JSON in this exact format:
    {{
        "identification": {{
            "document_type": "TYPE_HERE",
            "confidence": 0.95,
            "reasoning": "Brief explanation of why you identified this document type"
        }},
        "extracted_data": {{
            "document_title": "Title or description of the document",
            "key_field_1": "extracted_value_1",
            "key_field_2": "extracted_value_2"
        }}
    }}
    """

    model_name = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "topP": 0.9,
            "topK": 40,
            "response_mime_type": "application/json"
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            raw_text = result['candidates'][0]['content']['parts'][0]['text']
            
            # Clean up the response in case it has markdown
            raw_text = raw_text.strip()
            if raw_text.startswith('```json'):
                raw_text = raw_text[7:]
            if raw_text.startswith('```'):
                raw_text = raw_text[3:]
            if raw_text.endswith('```'):
                raw_text = raw_text[:-3]
            
            parsed_result = json.loads(raw_text)
            
            # Validate response structure
            if 'identification' not in parsed_result or 'extracted_data' not in parsed_result:
                return {"error": "Invalid response structure from Gemini"}
            
            return parsed_result
        else:
            error_detail = f"Gemini API returned status {response.status_code}"
            try:
                error_json = response.json()
                error_detail += f": {error_json.get('error', {}).get('message', response.text)}"
            except:
                error_detail += f": {response.text}"
            return {"error": error_detail}
    except requests.exceptions.Timeout:
        return {"error": "Request to Gemini API timed out. Please try again."}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to Gemini API. Check your internet connection."}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse Gemini response: {str(e)}"}
    except Exception as e:
        return {"error": f"Processing failed: {str(e)}"}

@app.post("/extract")
async def extract_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Query(None),
    custom_fields: Optional[str] = Query(None)
):
    """Extract data from uploaded PDF document"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Validate file size (max 20MB)
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 20MB limit")
    
    pdf_text, metadata = extract_text_from_pdf(content)
    
    if not pdf_text.strip():
        raise HTTPException(status_code=400, detail="Document appears to be empty or unreadable. It might be scanned or image-based.")
    
    # Show warning for scanned documents
    if "No extractable text found" in pdf_text:
        return {
            "success": False,
            "error": "Document appears to be scanned or contains no extractable text. OCR is not currently supported."
        }

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
        "metadata": metadata,
        "timestamp": datetime.now().isoformat(),
        "file_size": len(content),
        "questions_asked": 0
    }

    # Initialize conversation history for this document
    conversation_history[doc_id] = []

    return {
        "success": True,
        "document_id": doc_id,
        "filename": file.filename,
        "file_size": len(content),
        "num_pages": metadata["num_pages"],
        "identification": result["identification"],
        "extracted_data": result["extracted_data"]
    }

@app.post("/ask")
async def ask_document(request: QuestionRequest):
    """Ask questions about a document with conversation context"""
    if not extracted_documents:
        raise HTTPException(status_code=404, detail="No documents have been uploaded yet.")
    
    if request.document_id and request.document_id not in extracted_documents:
        raise HTTPException(status_code=404, detail=f"Document with ID {request.document_id} not found.")

    doc = extracted_documents.get(request.document_id) or list(extracted_documents.values())[-1]
    doc_id = doc['id']
    
    # Increment question count
    doc['questions_asked'] = doc.get('questions_asked', 0) + 1
    
    # Build context from conversation history
    history_context = ""
    if request.include_history and doc_id in conversation_history and conversation_history[doc_id]:
        last_5 = conversation_history[doc_id][-5:]  # Last 5 exchanges
        history_context = "\nPrevious conversation:\n"
        for i, exchange in enumerate(last_5, 1):
            history_context += f"Q{i}: {exchange['question']}\nA{i}: {exchange['answer']}\n"

    # Enhanced prompt with better instructions and context
    prompt = f"""
    You are DocuMind AI, an expert document analysis assistant. Answer the user's question based on the document below.

    Document Information:
    - Type: {doc['document_type']}
    - Filename: {doc['filename']}
    - Pages: {doc['metadata']['num_pages']}
    
    Extracted Structured Data:
    {json.dumps(doc['extracted_data'], indent=2)}
    
    Document Full Text (first 8000 chars for context):
    {doc['full_text'][:8000]}
    
    {history_context}
    
    User Question: {request.question}
    
    Instructions for response:
    1. Be specific and reference the document when possible
    2. If information is not found, say "I cannot find this information in the document"
    3. For dates, always include the format (e.g., "January 15, 2024")
    4. For numbers, preserve exact formatting
    5. If asked for summary, provide key points in bullet points
    6. Maintain conversation context from previous questions
    7. Be concise but thorough (aim for 2-5 sentences unless summary requested)
    
    Answer:
    """

    model_name = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.8,
            "topK": 40,
            "maxOutputTokens": 1000
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            answer = result['candidates'][0]['content']['parts'][0]['text'].strip()
            
            # Store in conversation history
            conversation_history[doc_id].append({
                "question": request.question,
                "answer": answer,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "answer": answer,
                "document_id": doc_id,
                "document_type": doc['document_type'],
                "question_number": doc['questions_asked']
            }
        else:
            error_msg = f"Gemini API error: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail.get('error', {}).get('message', 'Unknown error')}"
            except:
                pass
            raise HTTPException(status_code=500, detail=error_msg)
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=500, detail="Request timed out. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA failed: {str(e)}")

@app.post("/ask-batch")
async def ask_batch(request: BatchQuestionRequest):
    """Ask multiple questions about a document in batch"""
    if not extracted_documents:
        raise HTTPException(status_code=404, detail="No documents have been uploaded yet.")
    
    doc = extracted_documents.get(request.document_id) or list(extracted_documents.values())[-1]
    
    results = []
    for question in request.questions:
        # Create a single question request
        q_request = QuestionRequest(question=question, document_id=doc['id'])
        try:
            result = await ask_document(q_request)
            results.append({
                "question": question,
                "answer": result["answer"],
                "success": True
            })
        except Exception as e:
            results.append({
                "question": question,
                "answer": str(e),
                "success": False
            })
    
    return {
        "document_id": doc['id'],
        "total_questions": len(request.questions),
        "results": results
    }

@app.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    docs = []
    for doc_id, doc in extracted_documents.items():
        docs.append({
            "id": doc_id,
            "filename": doc['filename'],
            "document_type": doc['document_type'],
            "timestamp": doc['timestamp'],
            "questions_asked": doc.get('questions_asked', 0),
            "num_pages": doc['metadata']['num_pages']
        })
    return {
        "total_documents": len(docs),
        "documents": sorted(docs, key=lambda x: x['timestamp'], reverse=True)
    }

@app.get("/document/{document_id}")
async def get_document(document_id: str):
    """Get detailed information about a specific document"""
    if document_id not in extracted_documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = extracted_documents[document_id]
    return {
        "id": doc['id'],
        "filename": doc['filename'],
        "document_type": doc['document_type'],
        "extracted_data": doc['extracted_data'],
        "metadata": doc['metadata'],
        "timestamp": doc['timestamp'],
        "questions_asked": doc.get('questions_asked', 0),
        "conversation_history": conversation_history.get(document_id, [])
    }

@app.delete("/document/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its conversation history"""
    if document_id not in extracted_documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    del extracted_documents[document_id]
    if document_id in conversation_history:
        del conversation_history[document_id]
    
    return {"success": True, "message": f"Document {document_id} deleted"}

@app.post("/clear-all")
async def clear_all_documents():
    """Clear all documents and conversation history"""
    global extracted_documents, conversation_history
    extracted_documents.clear()
    conversation_history.clear()
    return {"success": True, "message": "All documents cleared"}

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    total_docs = len(extracted_documents)
    total_questions = sum(doc.get('questions_asked', 0) for doc in extracted_documents.values())
    document_types = {}
    
    for doc in extracted_documents.values():
        doc_type = doc['document_type']
        document_types[doc_type] = document_types.get(doc_type, 0) + 1
    
    return {
        "total_documents": total_docs,
        "total_questions_asked": total_questions,
        "document_type_distribution": document_types,
        "api_status": "online",
        "model_used": "gemini-2.5-flash"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "online",
        "model_used": "gemini-2.5-flash",
        "documents_loaded": len(extracted_documents),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Intelligent Document Extractor API...")
    print(f"📍 API will be available at: http://127.0.0.1:8000")
    print(f"📚 API Documentation: http://127.0.0.1:8000/docs")
    print(f"🔧 Environment: Development")
    print("-" * 50)
    
    # Method 1: Run without reload for direct script execution
    uvicorn.run(
        "main:app",  # Change this: use import string instead of app directly
        host="127.0.0.1", 
        port=8000,
        log_level="info",
        reload=True  # reload works with import string
    )