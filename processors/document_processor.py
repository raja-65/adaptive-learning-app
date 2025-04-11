import os
from typing import Dict, List, Any
import pypdf
import docx
from bs4 import BeautifulSoup

def process_document(file_path: str) -> str:
    """
    Extract text from various document formats
    Supports: PDF, DOCX, TXT
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.pdf':
        return extract_from_pdf(file_path)
    elif file_extension == '.docx':
        return extract_from_docx(file_path)
    elif file_extension == '.txt':
        return extract_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")

def extract_from_pdf(file_path: str) -> str:
    """Extract text from PDF files"""
    text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = pypdf.PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n\n"
    return text

def extract_from_docx(file_path: str) -> str:
    """Extract text from DOCX files"""
    doc = docx.Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_from_txt(file_path: str) -> str:
    """Extract text from TXT files"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def clean_text(text: str) -> str:
    """Clean and normalize extracted text"""
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Replace multiple newlines with a single one
    text = text.replace('\n\n\n', '\n\n')
    
    return text
