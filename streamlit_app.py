import streamlit as st
import json
import os
from pathlib import Path
import tempfile
from typing import Optional, Dict, Any, List
import PyPDF2
from io import BytesIO
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import traceback
import re
import google.generativeai as genai

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure Gemini
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("❌ GEMINI_API_KEY not found in .env file")
    st.stop()

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# Page configuration
st.set_page_config(
    page_title="DocuMind AI - Intelligent Document Extractor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI with uniform buttons
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 1rem;
        animation: fadeInDown 0.8s ease-out;
    }
    
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        animation: fadeInUp 0.8s ease-out;
    }
    
    /* Card styling */
    .card {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: 1px solid rgba(102, 126, 234, 0.1);
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 60px rgba(0,0,0,0.15);
    }
    
    /* Document info card */
    .doc-info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    
    /* Chat message styling */
    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 15px;
        margin-bottom: 1rem;
        word-wrap: break-word;

    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 20px 20px 5px 20px;
        margin-bottom: 1rem;
        max-width: 80%;
        margin-left: auto;
        animation: slideInRight 0.3s ease-out;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .assistant-message {
        background: white;
        color: #333;
        padding: 1rem;
        border-radius: 20px 20px 20px 5px;
        margin-bottom: 1rem;
        max-width: 80%;
        margin-right: auto;
        animation: slideInLeft 0.3s ease-out;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 15px;
        padding: 1rem;

        /* EQUAL HEIGHT FIX */
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;

        text-align: center;
        transition: all 0.3s ease;
        border: 1px solid #e0e0e0;
    }
    
    .metric-card:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Uniform button styling - ALL BUTTONS SAME HEIGHT */
    /* Universal button fix */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 0.8rem;
        font-weight: 600;
        
        /* RESPONSIVE FIX */
        width: 100%;
        min-height: 42px;
        height: auto;

        /* TEXT WRAP FIX */
        white-space: normal !important;
        word-break: break-word;
        overflow-wrap: break-word;
        text-align: center;

        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Error message styling */
    .error-message {
        background: #fee2e2;
        border-left: 4px solid #dc2626;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: #991b1b;
    }
    
    .error-details {
        background: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 0.75rem;
        border-radius: 8px;
        margin-top: 0.5rem;
        font-family: monospace;
        font-size: 0.85rem;
        color: #78350f;
    }
    
    /* File uploader button */
    .stFileUploader > div > button {
        height: 42px !important;
    }
    
    /* Download buttons in tabs */
    .stDownloadButton > button {
        height: 42px !important;
        width: 100% !important;
    }
    
    /* File uploader styling */
    .upload-container {
        border: 2px dashed #667eea;
        border-radius: 20px;
        padding: 1.5rem;
        text-align: center;
        background: #faf9ff;
        width: 100%;
    }
    
    .upload-container:hover {
        border-color: #764ba2;
        background: #f5f3ff;
    }
    
    /* Animations */
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }
    
    /* Status indicator */
    .status-online {
        display: inline-block;
        width: 10px;
        height: 10px;
        background-color: #10b981;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(16, 185, 129, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
        }
    }
    
    /* Loading spinner */
    .loading-spinner {
        display: inline-block;
        width: 40px;
        height: 40px;
        border: 3px solid rgba(102, 126, 234, 0.3);
        border-radius: 50%;
        border-top-color: #667eea;
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        font-weight: 600;
    }
    
    /* Divider styling */
    hr {
        background: linear-gradient(90deg, transparent, #667eea, #764ba2, transparent);
        height: 2px;
        border: none;
        margin: 2rem 0;
    }
    
    /* Fix for suggestion buttons to have same height */
    /* Suggestion buttons responsive */
    div[data-testid="column"] .stButton button {
        width: 100%;
        min-height: 42px;
        height: auto;

        font-size: 0.85rem;
        padding: 0.5rem;

        white-space: normal !important;
        word-break: break-word;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_doc_id" not in st.session_state:
        st.session_state.current_doc_id = None
    if "current_doc_info" not in st.session_state:
        st.session_state.current_doc_info = None
    if "extracted_data" not in st.session_state:
        st.session_state.extracted_data = None
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False
    if "last_error" not in st.session_state:
        st.session_state.last_error = None
    if "conversation_context" not in st.session_state:
        st.session_state.conversation_context = []
    if "document_text" not in st.session_state:
        st.session_state.document_text = None

def flatten_value(value):
    """Convert complex values to string for display in DataFrame"""
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, indent=2)
    return str(value)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
        text = "\n".join([page.extract_text() or "" for page in pdf_reader.pages])
        return text
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def upload_and_extract(file, document_type: Optional[str] = None, custom_fields: Optional[str] = None) -> Dict[str, Any]:
    """Extract data directly using Gemini AI"""
    try:
        with st.spinner("Processing document with Gemini AI..."):
            file_name, file_bytes, _ = file
            
            # Extract text from PDF
            document_text = extract_text_from_pdf(file_bytes)
            
            if not document_text.strip():
                return {
                    "error": "No text could be extracted from the PDF",
                    "details": {
                        "message": "The PDF might be scanned or empty",
                        "suggestion": "Try using an OCR-enabled PDF"
                    }
                }
            
            # Store document text for Q&A
            st.session_state.document_text = document_text
            
            # Prepare custom fields instruction
            custom_fields_instruction = ""
            if custom_fields and custom_fields.strip():
                custom_fields_instruction = f"""
Important: Specifically look for these custom fields:
{custom_fields}

Include them in the extracted_data object even if you need to infer them from context."""
            
            # Document type override instruction
            doc_type_instruction = ""
            if document_type and document_type != "AUTO_DETECT":
                doc_type_instruction = f"""
Document Type: {document_type}
The user has specified that this is a {document_type} document. Use this information to guide your extraction."""
            
            # Build extraction prompt
            prompt = f"""
You are an expert document extraction AI. Analyze the following document and extract key information.

{document_text[:30000]}

{doc_type_instruction}

{custom_fields_instruction}

Extract all relevant fields based on the document type. Common fields might include:
- For INSURANCE_POLICY: policy_number, effective_date, expiration_date, insured_name, premium_amount, coverage_details
- For DRIVING_LICENSE: license_number, full_name, date_of_birth, address, expiry_date, restrictions
- For INVOICE: invoice_number, date, due_date, vendor_name, customer_name, total_amount, line_items

Return a JSON object with EXACTLY this structure (no additional text before or after):
{{
  "document_type": "identified document type (e.g., INSURANCE_POLICY, DRIVING_LICENSE, INVOICE)",
  "confidence": 0.95,
  "reasoning": "Brief explanation of why you identified this document type and what key fields you found",
  "extracted_data": {{
    "field_name": "field_value",
    "another_field": "another_value"
  }}
}}

IMPORTANT: All values in extracted_data must be simple strings or numbers. Do NOT use nested objects or arrays.
If you need to represent multiple values, combine them into a single string separated by commas or newlines.

Guidelines:
1. Use descriptive field names (e.g., policy_number instead of just number)
2. Extract dates in YYYY-MM-DD format when possible
3. Include as much relevant information as you can find
4. For missing fields, omit them from extracted_data
5. Set confidence between 0.0 and 1.0 based on certainty
6. Keep field names lowercase with underscores
7. IMPORTANT: Return ONLY valid JSON, no markdown formatting, no explanatory text outside the JSON
"""

            # Get response from Gemini
            response = model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text
            
            # Clean up markdown code blocks if present
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*', '', response_text)
            
            # Find JSON object
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not match:
                raise ValueError("Could not extract JSON from Gemini response")
            
            data = json.loads(match.group())
            
            # Validate required fields
            if "document_type" not in data:
                data["document_type"] = "UNKNOWN"
            if "confidence" not in data:
                data["confidence"] = 0.5
            if "reasoning" not in data:
                data["reasoning"] = "Document processed successfully"
            if "extracted_data" not in data:
                data["extracted_data"] = {}
            
            # Flatten any nested data structures in extracted_data
            flattened_data = {}
            for key, value in data["extracted_data"].items():
                flattened_data[key] = flatten_value(value)
            
            data["extracted_data"] = flattened_data
            
            return {
                "document_id": f"doc_{hash(file_name)}_{datetime.now().timestamp()}",
                "identification": {
                    "document_type": data["document_type"],
                    "confidence": float(data["confidence"]),
                    "reasoning": data["reasoning"]
                },
                "extracted_data": data["extracted_data"]
            }
            
    except json.JSONDecodeError as e:
        return {
            "error": "Failed to parse Gemini response as JSON",
            "details": {
                "message": str(e),
                "response": response_text[:500] if 'response_text' in locals() else "No response",
                "error_type": "JSONDecodeError"
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "details": {
                "message": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        }

def answer_from_extracted_data(question: str, extracted_data: dict) -> Optional[str]:
    """Try to answer questions using locally stored extracted data"""
    question_lower = question.lower()
    
    # Map common questions to extracted fields with more intelligent matching
    field_mappings = {
        "policy number": ["policy_number", "policy_no", "policy id", "policy #"],
        "effective date": ["effective_date", "start_date", "policy_start", "effective"],
        "expiration date": ["expiration_date", "end_date", "policy_end", "expiry_date", "expires"],
        "name": ["name", "full_name", "insured_name", "policyholder", "applicant"],
        "address": ["address", "mailing_address", "residence"],
        "phone": ["phone", "telephone", "mobile", "contact"],
        "email": ["email", "email_address", "e-mail"],
        "amount": ["amount", "premium", "sum_insured", "coverage_amount", "limit"],
        "vehicle": ["vehicle", "car", "automobile", "make", "model", "vin"],
        "license": ["license", "driving_license", "license_number", "dl"],
        "date of birth": ["dob", "birth_date", "date_of_birth", "birth"],
        "company": ["company", "insurer", "insurance_company", "carrier"],
        "document type": ["document_type", "doc_type", "type"],
        "status": ["status", "policy_status", "document_status"]
    }
    
    # Search for matching fields
    answers = []
    for key, variations in field_mappings.items():
        if key in question_lower or any(var in question_lower for var in variations):
            for field in variations:
                if field in extracted_data and extracted_data[field] and str(extracted_data[field]).strip():
                    field_name = field.replace('_', ' ').title()
                    answers.append(f"{field_name}: {extracted_data[field]}")
                    break
    
    if answers:
        return "Based on the extracted data:\n" + "\n".join(answers)
    
    # Check for field presence in extracted data directly
    direct_matches = []
    for field, value in extracted_data.items():
        if value and str(value).strip():
            field_clean = field.replace('_', ' ')
            if any(word in question_lower for word in field_clean.lower().split()):
                direct_matches.append(f"{field_clean.title()}: {value}")
    
    if direct_matches:
        return "Here's what I found:\n" + "\n".join(direct_matches[:5])
    
    # If no specific field found, provide summary of available data
    if any(word in question_lower for word in ["what", "tell", "show", "list", "information", "details", "summary"]):
        relevant_data = {k: v for k, v in extracted_data.items() if v and str(v).strip()}
        if relevant_data:
            response = "Here's the information available in the document:\n"
            for k, v in list(relevant_data.items())[:10]:
                response += f"\n- {k.replace('_', ' ').title()}: {v}"
            return response
    
    return None

def ask_question(question: str, document_id: str, chat_history: List[Dict] = None, extracted_data: Dict = None, document_text: str = None) -> str:
    """Ask a question using Gemini AI with document context"""
    
    # First try to answer from locally extracted data for quick responses
    if extracted_data:
        local_answer = answer_from_extracted_data(question, extracted_data)
        if local_answer:
            return local_answer
    
    try:
        with st.spinner("Thinking..."):
            # Build context from extracted data
            extracted_context = json.dumps(extracted_data, indent=2) if extracted_data else "No extracted data available"
            
            # Build chat history context
            history_context = ""
            if chat_history and len(chat_history) > 0:
                recent_history = chat_history[-8:]  # Last 4 exchanges
                for msg in recent_history:
                    role = "User" if msg["role"] == "user" else "Assistant"
                    history_context += f"{role}: {msg['content']}\n"
            
            # Document text context (first 8000 chars for efficiency)
            doc_context = ""
            if document_text:
                doc_context = f"\n\nFull Document Text (excerpt):\n{document_text[:8000]}"
            
            # Build Q&A prompt
            prompt = f"""
You are DocuMind AI, an intelligent document assistant. Answer the user's question based on the document information provided.

EXTRACTED DATA FROM DOCUMENT:
{extracted_context}

PREVIOUS CONVERSATION:
{history_context if history_context else "No previous conversation"}

{doc_context}

USER QUESTION:
{question}

INSTRUCTIONS:
1. Answer based ONLY on the extracted data and document text provided above
2. If the information is not available, say "I don't have that information in the document"
3. Be concise and helpful
4. If you find relevant information, quote it directly
5. For date-related questions, provide the dates in a clear format
6. If asked for a summary, list the key fields and their values

YOUR ANSWER:
"""
            
            # Get response from Gemini
            response = model.generate_content(prompt)
            answer = response.text
            
            # Clean up answer
            answer = answer.strip()
            
            return answer
            
    except Exception as e:
        # Fallback to local answering if API call fails
        if extracted_data:
            local_answer = answer_from_extracted_data(question, extracted_data)
            if local_answer:
                return local_answer + f"\n\n(Note: Using local data - Gemini API error: {str(e)})"
        return f"Error: {str(e)}"

def show_error_details(error: Dict[str, Any]):
    """Display detailed error information"""
    st.markdown("""
    <div class="error-message">
        <strong>Error Processing Document</strong><br>
    </div>
    """, unsafe_allow_html=True)
    
    st.error(error.get("error", "An unknown error occurred"))
    
    with st.expander("View Error Details", expanded=True):
        if "details" in error:
            details = error["details"]
            
            if "error_type" in details:
                st.markdown(f"**Error Type:** `{details['error_type']}`")
            
            if "message" in details:
                st.markdown("**Error Details:**")
                st.code(details["message"])
            
            if "traceback" in details:
                st.markdown("**Traceback:**")
                st.code(details["traceback"], language="python")
            
            if "response" in details:
                st.markdown("**Gemini Response:**")
                st.code(details["response"], language="json")
        
        st.markdown("---")
        st.markdown("**Troubleshooting Tips:**")
        st.markdown("- Check if your GEMINI_API_KEY is valid in the .env file")
        st.markdown("- Make sure the PDF file is readable and contains extractable text")
        st.markdown("- Try with a smaller PDF file (under 10MB)")
        st.markdown("- Check your internet connection")

def create_confidence_gauge(confidence: float):
    """Create a confidence gauge chart"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = confidence * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Confidence Score", 'font': {'size': 14}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1},
            'bar': {'color': "#667eea"},
            'steps': [
                {'range': [0, 50], 'color': "#fee2e2"},
                {'range': [50, 75], 'color': "#fef3c7"},
                {'range': [75, 100], 'color': "#d1fae5"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(t=0, b=0, l=0, r=0))
    return fig

def main():
    initialize_session_state()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<h1 class="main-header">DocuMind AI</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Intelligent Document Understanding with Gemini AI</p>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### Document Workspace")
        st.markdown("---")
        
        uploaded_file = st.file_uploader(
            "Drop your PDF here or click to browse",
            type="pdf",
            help="Upload a PDF document for intelligent extraction"
        )
        
        if uploaded_file:
            st.success(f"Loaded: {uploaded_file.name}")
        
        st.markdown("---")
        
        with st.expander("Advanced Settings", expanded=False):
            document_type = st.selectbox(
                "Document Type Override",
                ["AUTO_DETECT", "INSURANCE_POLICY", "DRIVING_LICENSE", "IDENTITY_CARD", 
                 "VEHICLE_REGISTRATION", "BANK_STATEMENT", "TAX_DOCUMENT", 
                 "EMPLOYMENT_CONTRACT", "LEASE_AGREEMENT", "INVOICE", "CERTIFICATE"],
                help="Force document type detection"
            )
            
            custom_fields_input = st.text_area(
                "Custom Extraction Fields",
                placeholder="Enter field names separated by commas\nExample: policy_number, effective_date, beneficiary",
                help="Specify additional fields to extract"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            # Fixed: Changed use_container_width to width='stretch'
            upload_button = st.button("Extract & Analyze", type="primary", use_container_width=True)
        with col2:
            clear_button = st.button("Clear Session", use_container_width=True)
        
        if clear_button:
            st.session_state.messages = []
            st.session_state.current_doc_id = None
            st.session_state.current_doc_info = None
            st.session_state.extracted_data = None
            st.session_state.last_error = None
            st.session_state.conversation_context = []
            st.session_state.document_text = None
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("### System Status")
        # Check Gemini API key status
        if API_KEY:
            st.markdown(":green[Gemini AI: Ready]")
            st.caption("Model: gemini-2.5-flash")
            st.caption("Powered by Google Gemini")
        else:
            st.markdown(":red[Gemini AI: Not Configured]")
            st.info("Add GEMINI_API_KEY to .env file")
        
        st.markdown("---")
    
    if uploaded_file and upload_button:
        with st.container():
            progress_text = st.empty()
            progress_bar = st.progress(0)
            
            progress_text.text("Reading document...")
            progress_bar.progress(20)
            
            custom_fields = custom_fields_input if custom_fields_input else None
            
            result = upload_and_extract(
                (uploaded_file.name, uploaded_file.getvalue(), "application/pdf"),
                document_type if document_type != "AUTO_DETECT" else None,
                custom_fields
            )
            
            progress_bar.progress(100)
            progress_text.empty()
            
            if "error" not in result:
                st.session_state.current_doc_id = result["document_id"]
                st.session_state.current_doc_info = result["identification"]
                st.session_state.extracted_data = result["extracted_data"]
                st.session_state.last_error = None
                st.session_state.conversation_context = []
                st.session_state.messages = []
                
                st.balloons()
                st.success("Document processed successfully")
                
                welcome_msg = f"""Document processed successfully

I've identified this as a **{result['identification']['document_type'].replace('_', ' ').title()}** with {result['identification']['confidence']:.1%} confidence.

{result['identification']['reasoning']}

You can now ask me anything about this document. What would you like to know?"""
                st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
                st.rerun()
            else:
                st.session_state.last_error = result
                show_error_details(result)
                
                error_msg = f"**Error:** {result['error']}\n\nPlease check the error details above for troubleshooting."
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    if st.session_state.current_doc_info:
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            doc_type = st.session_state.current_doc_info['document_type']
            formatted_doc_type = doc_type.replace('_', ' ').title()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="font-size: 1.2rem;">{formatted_doc_type}</div>
                <div style="color: #666; font-size: 0.9rem;">Document Type</div>
            </div>
        """, unsafe_allow_html=True)
        
        with col2:
            confidence = st.session_state.current_doc_info['confidence']
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{confidence:.1%}</div>
                <div style="color: #666; font-size: 0.9rem;">Confidence Score</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            data_points = len(st.session_state.extracted_data)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{data_points}</div>
                <div style="color: #666; font-size: 0.9rem;">Data Points Extracted</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            timestamp = datetime.now().strftime("%H:%M")
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{timestamp}</div>
                <div style="color: #666; font-size: 0.9rem;">Last Processed</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("Detailed Analysis", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                fig = create_confidence_gauge(st.session_state.current_doc_info['confidence'])
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown("**AI Reasoning**")
                st.info(st.session_state.current_doc_info['reasoning'])
    
    if st.session_state.extracted_data:
        st.markdown("---")
        tab1, tab2, tab3 = st.tabs(["Extracted Data", "Analytics", "Export"])
        
        with tab1:
            # FIXED: Convert complex values to strings before creating DataFrame
            flat_data = {}
            for key, value in st.session_state.extracted_data.items():
                flat_data[key] = flatten_value(value)
            
            df = pd.DataFrame(list(flat_data.items()), columns=["Field", "Value"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                # Filter out non-string values for word count
                word_counts = []
                field_names = []
                for key, value in st.session_state.extracted_data.items():
                    str_value = flatten_value(value)
                    if str_value:
                        word_counts.append(len(str_value.split()))
                        field_names.append(key)
                
                if word_counts:
                    fig = go.Figure(data=[go.Bar(
                        x=field_names,
                        y=word_counts,
                        marker_color='#667eea'
                    )])
                    fig.update_layout(title="Word Count per Field", xaxis_title="Fields", yaxis_title="Word Count")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for analytics")
            with col2:
                char_counts = []
                field_names_pie = []
                for key, value in st.session_state.extracted_data.items():
                    str_value = flatten_value(value)
                    if str_value:
                        char_counts.append(len(str_value))
                        field_names_pie.append(key)
                
                if char_counts:
                    fig = go.Figure(data=[go.Pie(
                        labels=field_names_pie,
                        values=char_counts,
                        hole=0.3,
                        marker_colors=['#667eea', '#764ba2', '#f093fb', '#4facfe']
                    )])
                    fig.update_layout(title="Data Size Distribution")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for analytics")
        
        with tab3:
            col1, col2 = st.columns(2)
            with col1:
                json_str = json.dumps(st.session_state.extracted_data, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name="extracted_data.json",
                    mime="application/json",
                    use_container_width=True
                )
            with col2:
                if st.session_state.extracted_data:
                    # Flatten data for CSV
                    flat_csv_data = {k: flatten_value(v) for k, v in st.session_state.extracted_data.items()}
                    csv_data = pd.DataFrame([flat_csv_data]).to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name="extracted_data.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
    
    st.markdown("---")
    st.markdown("### Intelligent Q&A")
    st.markdown("Ask questions about your document in natural language")
    
    chat_container = st.container()
    with chat_container:
        chat_html = '<div class="chat-container">'
        for message in st.session_state.messages:
            if message["role"] == "user":
                chat_html += f'<div class="user-message"><strong>You</strong><br>{message["content"]}</div>'
            else:
                chat_html += f'<div class="assistant-message"><strong>DocuMind AI</strong><br>{message["content"]}</div>'
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
    
    if st.session_state.current_doc_id:
        # Use a form with clear_on_submit to automatically clear input
        with st.form(key="question_form", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                question = st.text_input(
                    "Ask a question:",
                    placeholder="e.g., What is the policy number? When does it expire? Who are the involved parties?",
                    label_visibility="collapsed"
                )
            with col2:
                send_button = st.form_submit_button("Send", type="primary", use_container_width=True)
            
            if send_button and question:
                st.session_state.messages.append({"role": "user", "content": question})
                answer = ask_question(
                    question, 
                    st.session_state.current_doc_id, 
                    st.session_state.messages[:-1],
                    st.session_state.extracted_data,
                    st.session_state.document_text
                )
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun()
        
        st.markdown("**Quick Questions:**")
        suggestion_cols = st.columns(4)
        suggestions = [
            "What type of document is this?",
            "What are the key dates?",
            "Who are the parties involved?",
            "Summarize this document"
        ]
        
        for idx, suggestion in enumerate(suggestions):
            with suggestion_cols[idx % 4]:
                if st.button(suggestion, key=f"suggestion_{idx}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": suggestion})
                    answer = ask_question(
                        suggestion, 
                        st.session_state.current_doc_id, 
                        st.session_state.messages[:-1],
                        st.session_state.extracted_data,
                        st.session_state.document_text
                    )
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    st.rerun()
    else:
        st.info("Please upload a document to start asking questions")
        st.caption("Supported formats: PDF only")
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col2:
        st.caption("Powered by Google Gemini AI")

if __name__ == "__main__":
    main()