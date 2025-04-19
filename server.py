from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
import fitz  # PyMuPDF for PDF reading
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import os
import uuid
import openai
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Download NLTK data
nltk.download('punkt')
nltk.download('stopwords')

# FastAPI app
app = FastAPI()

# OpenAI key (replace with your key or use environment variable)
openai.api_key = "your_openai_api_key"

# === UTILS ===

def extract_text_from_pdf(pdf_path):
    """Extracts all text from a PDF."""
    doc = fitz.open(pdf_path)
    text = " ".join([page.get_text("text") for page in doc])
    return text.strip()

def preprocess_text(text):
    """Tokenize and clean text for comparison."""
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    return {word for word in tokens if word.isalnum() and word not in stop_words}

def compare_resume_with_job(resume_text, job_text):
    """Find keywords missing from resume."""
    resume_words = preprocess_text(resume_text)
    job_words = preprocess_text(job_text)
    return list(job_words - resume_words)

def optimize_resume(resume_text, missing_keywords):
    """Use GPT to rewrite resume using missing keywords."""
    prompt = f"""
    Here is a resume:
    {resume_text}

    The job description suggests these keywords are missing: {', '.join(missing_keywords)}.
    Please enhance the resume using these keywords in a natural way.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

def generate_pdf_from_text(text, filename):
    """Generate a PDF file from plain text."""
    file_path = f"{filename}.pdf"
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter
    y = height - 40

    for line in text.splitlines():
        if y < 40:
            c.showPage()
            y = height - 40
        c.drawString(40, y, line)
        y -= 15

    c.save()
    return file_path

# === ROUTES ===

@app.post("/process-resume/")
async def process_resume(file: UploadFile = File(...), job_description: str = Form(...)):
    """Check resume vs job description and return missing keywords."""
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    resume_text = extract_text_from_pdf(file_path)
    missing_keywords = compare_resume_with_job(resume_text, job_description)
    os.remove(file_path)

    return {"missing_keywords": missing_keywords}

@app.post("/optimize-resume/")
async def optimize_resume_api(file: UploadFile = File(...), job_description: str = Form(...)):
    """Optimize resume and return a downloadable PDF."""
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    resume_text = extract_text_from_pdf(file_path)
    missing_keywords = compare_resume_with_job(resume_text, job_description)
    optimized_text = optimize_resume(resume_text, missing_keywords)
    os.remove(file_path)

    pdf_filename = f"optimized_resume_{uuid.uuid4().hex}"
    pdf_path = generate_pdf_from_text(optimized_text, pdf_filename)

    return FileResponse(
        path=pdf_path,
        filename="optimized_resume.pdf",
        media_type="application/pdf"
    )
