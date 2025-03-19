from fastapi import FastAPI, File, UploadFile, Form
import fitz  # PyMuPDF for PDF extraction
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import os

app = FastAPI()

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = " ".join([page.get_text("text") for page in doc])
    return text.strip()

def preprocess_text(text):
    """Tokenizes and cleans text data."""
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    return {word for word in tokens if word.isalnum() and word not in stop_words}

def compare_resume_with_job(resume_text, job_text):
    """Compares the resume with job description and highlights missing keywords."""
    resume_words = preprocess_text(resume_text)
    job_words = preprocess_text(job_text)
    missing_keywords = job_words - resume_words
    return list(missing_keywords)

@app.post("/process-resume/")
async def process_resume(file: UploadFile = File(...), job_description: str = Form(...)):
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    resume_text = extract_text_from_pdf(file_path)
    missing_keywords = compare_resume_with_job(resume_text, job_description)
    os.remove(file_path)

    return {"missing_keywords": missing_keywords}
