# api/routes/utils.py

import json
import math
import os
import io
from pdfminer.high_level import extract_text
from docx import Document

# --- JSON Encoding Utilities ---

class NaNHandlingEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle NaN and Infinity values,
    converting them to null, which is JSON compliant.
    """
    def default(self, obj):
        if isinstance(obj, float):
            # If the float is not a number or is infinite, return None (which becomes null)
            if math.isnan(obj) or math.isinf(obj):
                return None
        return super(NaNHandlingEncoder, self).default(obj)

def render_json_with_nan_handling(content):
    """
    A helper function to render a Python object into a JSON string
    using our custom encoder.
    """
    return json.dumps(content, cls=NaNHandlingEncoder)

# --- File & Path Utilities ---

# --- Constants for file handling ---
UPLOAD_DIR = "uploads"
RESUME_FILENAME_BASE = "user_resume"
ANALYSIS_FILE = "resume_analysis.json"
CACHE_DIR = "cache"

# Ensure necessary directories exist when the app starts
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# --- Reusable Helper Functions ---
def extract_text_from_pdf(file_contents: bytes) -> str:
    """Extracts text from PDF file bytes."""
    return extract_text(io.BytesIO(file_contents))

def extract_text_from_docx(file_contents: bytes) -> str:
    """Extracts text from DOCX file bytes."""
    doc = Document(io.BytesIO(file_contents))
    return "\n".join([para.text for para in doc.paragraphs])

def get_resume_path():
    """
    Checks for an existing resume in the uploads directory and returns its full path.
    """
    pdf_path = os.path.join(UPLOAD_DIR, f"{RESUME_FILENAME_BASE}.pdf")
    docx_path = os.path.join(UPLOAD_DIR, f"{RESUME_FILENAME_BASE}.docx")
    if os.path.exists(pdf_path):
        return pdf_path
    if os.path.exists(docx_path):
        return docx_path
    return None
