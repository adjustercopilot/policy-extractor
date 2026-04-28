import streamlit as st
import requests
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

# API Configuration
API_URL = "http://127.0.0.1:8000"

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

def show_error_details(error: Dict[str, Any]):
    """Display detailed error information"""
    st.markdown("""
    <div class="error-message">
        <strong>Error Processing Document</strong><br>
    </div>
    """, unsafe_allow_html=True)
    
    st.error(error.get("message", "An unknown error occurred"))
    
    with st.expander("View Error Details", expanded=True):
        if "status_code" in error:
            st.markdown(f"**Status Code:** `{error['status_code']}`")
        
        if "error_type" in error:
            st.markdown(f"**Error Type:** `{error['error_type']}`")
        
        if "details" in error:
            st.markdown("**Error Details:**")
            st.code(error["details"], language="json")
        
        if "api_response" in error:
            st.markdown("**API Response:**")
            st.json(error["api_response"])
        
        if "traceback" in error:
            st.markdown("**Traceback:**")
            st.code(error["traceback"], language="python")
        
        st.markdown("---")
        st.markdown("**Troubleshooting Tips:**")
        
        if error.get("status_code") == 500:
            st.markdown("- Check if the Gemini API key is valid in your backend")
            st.markdown("- Verify the PDF file is readable and not corrupted")
            st.markdown("- Check the backend logs for more details")
        elif error.get("status_code") == 400:
            st.markdown("- The file format might not be supported")
            st.markdown("- Check if the file is a valid PDF")
        elif error.get("status_code") == 404:
            st.markdown("- Make sure the backend server is running")
            st.markdown("- Check if the API endpoint URL is correct")
        elif error.get("status_code") == 413:
            st.markdown("- The file is too large for processing")
            st.markdown("- Try compressing the PDF file")
        elif error.get("status_code") == 429:
            st.markdown("- Rate limit exceeded. Please wait and try again")
            st.markdown("- Check your API quota limits")
        elif error.get("status_code") == 503:
            st.markdown("- Backend service is unavailable")
            st.markdown("- Check if the FastAPI server is running")
        else:
            st.markdown("- Verify the backend server is running at `http://127.0.0.1:8000`")
            st.markdown("- Check the API logs for more information")
            st.markdown("- Make sure all dependencies are installed")

def upload_and_extract(file, document_type: Optional[str] = None, custom_fields: Optional[str] = None) -> Dict[str, Any]:
    """Upload file to FastAPI backend and get extraction results with detailed error handling"""
    files = {"file": file}
    params = {}
    
    if document_type and document_type != "AUTO_DETECT":
        params["document_type"] = document_type
    if custom_fields:
        params["custom_fields"] = custom_fields
    
    try:
        with st.spinner("Processing document..."):
            response = requests.post(
                f"{API_URL}/extract",
                files=files,
                params=params,
                timeout=60
            )
            
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                return {
                    "error": "Invalid response from API",
                    "details": {
                        "message": "API returned non-JSON response",
                        "status_code": response.status_code,
                        "response_text": response.text[:500],
                        "error_type": "JSONDecodeError"
                    }
                }
            
            if response.status_code != 200:
                return {
                    "error": f"API returned status code {response.status_code}",
                    "details": {
                        "status_code": response.status_code,
                        "message": response_data.get("detail", response_data.get("message", "Unknown error")),
                        "api_response": response_data
                    }
                }
            
            if "error" in response_data:
                return {
                    "error": response_data["error"],
                    "details": response_data.get("details", {})
                }
            
            return response_data
            
    except requests.exceptions.ConnectionError as e:
        return {
            "error": "Cannot connect to the API server",
            "details": {
                "message": str(e),
                "error_type": "ConnectionError",
                "suggestions": [
                    "Make sure the backend server is running",
                    f"Verify API URL: {API_URL}",
                    "Check if the server is accessible"
                ]
            }
        }
    except requests.exceptions.Timeout as e:
        return {
            "error": "Request timeout - document processing took too long",
            "details": {
                "message": str(e),
                "error_type": "Timeout",
                "suggestions": [
                    "Try with a smaller PDF file",
                    "Check your network connection",
                    "Increase the timeout in the backend"
                ]
            }
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Request failed: {str(e)}",
            "details": {
                "message": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
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

def ask_question(question: str, document_id: str, chat_history: List[Dict] = None, extracted_data: Dict = None) -> str:
    """Ask a question about the document with context from chat history and local fallback"""
    
    # First try to answer from locally extracted data
    if extracted_data:
        local_answer = answer_from_extracted_data(question, extracted_data)
        if local_answer:
            return local_answer
    
    try:
        with st.spinner("Thinking..."):
            # Prepare the request with conversation context
            request_data = {
                "question": question,
                "document_id": document_id
            }
            
            # Include recent chat history for context (last 8 messages)
            if chat_history and len(chat_history) > 0:
                # Format chat history for the API
                formatted_history = []
                for msg in chat_history[-8:]:  # Last 4 exchanges
                    formatted_history.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                request_data["chat_history"] = formatted_history
                request_data["conversation_context"] = True
            
            response = requests.post(
                f"{API_URL}/ask",
                json=request_data,
                timeout=30
            )
            
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                return f"Error: API returned invalid response - {response.text[:200]}"
            
            if response.status_code != 200:
                error_msg = response_data.get("detail", response_data.get("message", f"Status code: {response.status_code}"))
                return f"Error: {error_msg}"
            
            answer = response_data.get("answer", "No answer received from API")
            
            # If API answer is not helpful, try local context again
            if "I don't have enough information" in answer or "cannot find" in answer.lower():
                if extracted_data:
                    local_answer = answer_from_extracted_data(question, extracted_data)
                    if local_answer:
                        return local_answer
            
            return answer
            
    except requests.exceptions.ConnectionError:
        # Fallback to local answering if API is down
        if extracted_data:
            local_answer = answer_from_extracted_data(question, extracted_data)
            if local_answer:
                return local_answer + "\n\n(Note: Using local data as API is unavailable)"
        return "Error: Cannot connect to the API server. Make sure it's running at http://127.0.0.1:8000"
    except requests.exceptions.Timeout:
        return "Error: Request timed out. Please try again with a simpler question"
    except Exception as e:
        return f"Error: {str(e)}"

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
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("### System Status")
        try:
            health = requests.get(f"{API_URL}/health", timeout=2)
            if health.status_code == 200:
                st.markdown(":green[API: Online]")
                data = health.json()
                st.caption(f"Model: {data.get('model_used', 'Unknown')}")
                st.caption(f"Status: {data.get('status', 'OK')}")
            else:
                st.markdown(":red[API: Offline]")
                st.error("API issue detected")
        except:
            st.markdown(":red[API: Offline]")
            st.info("Run: python main.py to start the backend")
        
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

I've identified this as a **{result['identification']['document_type']}** with {result['identification']['confidence']:.1%} confidence.

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
            df = pd.DataFrame(list(st.session_state.extracted_data.items()), columns=["Field", "Value"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                word_counts = [len(str(v).split()) for v in st.session_state.extracted_data.values()]
                fig = go.Figure(data=[go.Bar(
                    x=list(st.session_state.extracted_data.keys()),
                    y=word_counts,
                    marker_color='#667eea'
                )])
                fig.update_layout(title="Word Count per Field", xaxis_title="Fields", yaxis_title="Word Count")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                char_counts = [len(str(v)) for v in st.session_state.extracted_data.values()]
                fig = go.Figure(data=[go.Pie(
                    labels=list(st.session_state.extracted_data.keys()),
                    values=char_counts,
                    hole=0.3,
                    marker_colors=['#667eea', '#764ba2', '#f093fb', '#4facfe']
                )])
                fig.update_layout(title="Data Size Distribution")
                st.plotly_chart(fig, use_container_width=True)
        
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
                csv_data = pd.DataFrame([st.session_state.extracted_data]).to_csv(index=False)
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
                    st.session_state.extracted_data
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
                        st.session_state.extracted_data
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