import fitz
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = " "
    for page in doc:
        text += page.get_text("text") + " "
    return text.strip()

def preprocess_text(text):
    """Tokenizes and cleans text data."""
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
    return set(filtered_tokens)

def compare_resume_with_job(resume_text, job_text):
    """Compares the resume with job description and highlights missing keywords."""
    resume_words = preprocess_text(resume_text)
    job_words = preprocess_text(job_text)
    missing_keywords = job_words - resume_words
    return missing_keywords

# Example Usage
resume_path = "resume.pdf"  # Change to the actual resume file path
job_description = """We are looking for a software engineer with experience in Python, Django, REST APIs,
                     and cloud technologies such as AWS or Azure. Familiarity with CI/CD is a plus."""

resume_text = extract_text_from_pdf(resume_path)
missing_keywords = compare_resume_with_job(resume_text, job_description)

print("Missing or weakly mentioned keywords in resume:", missing_keywords)