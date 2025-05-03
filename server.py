from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
import fitz  # PyMuPDF
import openai
import uuid
import os

app = FastAPI()

# Set your OpenAI API key (or use an env variable)
openai.api_key = "your_openai_api_key"

def extract_summary_and_skills(text: str) -> tuple[str, str]:
    """Very basic extraction based on keywords. Improve with regex or NLP if needed."""
    lower_text = text.lower()
    summary = ""
    skills = ""
    
    if "summary" in lower_text:
        summary_start = lower_text.find("summary")
        skills_start = lower_text.find("skills", summary_start + 1)
        summary = text[summary_start:skills_start].strip() if skills_start != -1 else text[summary_start:].strip()

    if "skills" in lower_text:
        skills_start = lower_text.find("skills")
        end = lower_text.find("\n\n", skills_start)
        skills = text[skills_start:end].strip() if end != -1 else text[skills_start:].strip()

    return summary, skills

def ask_gpt_to_rewrite(summary: str, skills: str, job_description: str) -> tuple[str, str]:
    prompt = f"""
        You are a professional resume editor. Enhance the following resume sections to better align with the job description.

        Job Description:
        {job_description}

        Original Summary:
        {summary}

        Original Skills:
        {skills}

        Please rewrite the Summary and Skills using relevant keywords from the job description, keeping the tone professional.
        """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{ "role": "user", "content": prompt }],
        temperature=0.7
    )
    output = response.choices[0].message.content
    rewritten_summary = ""
    rewritten_skills = ""
    if "Summary:" in output and "Skills:" in output:
        summary_idx = output.find("Summary:")
        skills_idx = output.find("Skills:")
        if summary_idx < skills_idx:
            rewritten_summary = output[summary_idx + 8:skills_idx].strip()
            rewritten_skills = output[skills_idx + 7:].strip()
    return rewritten_summary, rewritten_skills

def overlay_text_on_pdf(original_path: str, summary: str, skills: str) -> str:
    doc = fitz.open(original_path)
    modified_path = f"optimized_{uuid.uuid4().hex}.pdf"

    for page in doc:
        blocks = page.get_text("blocks")
        for block in blocks:
            x0, y0, x1, y1, text, _, _, _ = block
            if "summary" in text.lower():
                page.draw_rect((x0, y0, x1, y1), fill=(1, 1, 1))
                page.insert_text((x0, y0), f"Summary\n{summary}", fontsize=11, wrap=300)
            elif "skills" in text.lower():
                page.draw_rect((x0, y0, x1, y1), fill=(1, 1, 1))
                page.insert_text((x0, y0), f"Skills\n{skills}", fontsize=11, wrap=300)

    doc.save(modified_path)
    doc.close()
    return modified_path

@app.post("/optimize-resume/")
async def optimize_resume(file: UploadFile = File(...), job_description: str = Form(...)):
    temp_filename = f"temp_{file.filename}"
    with open(temp_filename, "wb") as f:
        f.write(await file.read())

    doc = fitz.open(temp_filename)
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    summary, skills = extract_summary_and_skills(full_text)
    rewritten_summary, rewritten_skills = ask_gpt_to_rewrite(summary, skills, job_description)
    updated_pdf_path = overlay_text_on_pdf(temp_filename, rewritten_summary, rewritten_skills)
    os.remove(temp_filename)

    return FileResponse(
        path=updated_pdf_path,
        filename="optimized_resume.pdf",
        media_type="application/pdf"
    )
