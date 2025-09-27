from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.tools import tool

@tool
def load_pdf(file_path: str) -> str:
    """Load and extract text from a PDF file.
    
    Args:
        file_path: Path to the PDF file to load
        
    Returns:
        Extracted text content from the PDF
    """
    loader = PyMuPDFLoader(file_path)
    documents = loader.load()
    return "\n".join([doc.page_content for doc in documents])