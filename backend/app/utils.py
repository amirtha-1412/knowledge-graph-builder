import PyPDF2
from io import BytesIO

def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extracts plain text from a PDF file provided as bytes.
    """
    text = ""
    try:
        reader = PyPDF2.PdfReader(BytesIO(file_content))
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        print(f"PDF Extraction Error: {e}")
        return ""
    
    return text.strip()
