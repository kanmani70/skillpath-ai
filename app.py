from flask import Flask, render_template, request, jsonify
import os
import PyPDF2
from groq import Groq
import re
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analysis")
def analysis():
    return render_template("analysis.html")

@app.route("/roadmap-page")
def roadmap_page():
    return render_template("roadmap.html")

@app.route("/interview-page")
def interview_page():
    return render_template("interview.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    if 'resume' not in request.files:
        return jsonify({"error": "No file received"})
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "Empty filename"})
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    resume_text = extract_text_from_pdf(filepath)
    target_job = request.form.get('target_job', 'Software Developer')
    analysis_result = analyze_with_ai(resume_text, target_job)
    return jsonify(analysis_result)

@app.route("/roadmap", methods=["POST"])
def roadmap():
    data = request.json
    skills_gap = data.get('skills_gap', [])
    target_job = data.get('target_job', 'Software Developer')
    roadmap_data = generate_roadmap(skills_gap, target_job)
    return jsonify(roadmap_data)

@app.route("/interview", methods=["POST"])
def interview():
    data = request.json
    user_answer = data.get('answer', '')
    question = data.get('question', '')
    feedback = get_interview_feedback(question, user_answer)
    return jsonify(feedback)
@app.route("/jobs")
def jobs():
    return render_template("jobs.html")

@app.route("/get-jobs", methods=["POST"])
def get_jobs():
    data = request.json
    target_job = data.get('target_job', 'Software Developer')
    skills = data.get('skills', [])
    jobs_data = generate_job_recommendations(target_job, skills)
    return jsonify(jobs_data)

@app.route("/quiz", methods=["POST"])
def quiz():
    data = request.json
    skill = data.get('skill', '')
    topic = data.get('topic', '')
    questions = generate_quiz(skill, topic)
    return jsonify(questions)

@app.route("/next-question", methods=["POST"])
def next_question():
    data = request.json
    target_job = data.get('target_job', 'Software Developer')
    question = generate_interview_question(target_job)
    return jsonify(question)

def extract_text_from_pdf(filepath):
    text = ""
    try:
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"
    return text

def analyze_with_ai(resume_text, target_job):
    cleaned_text = re.sub(r'(?<=[A-Z])\s(?=[A-Z])', '', resume_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

    prompt = f"""
You are a career guidance expert for Indian freshers.
Analyze this resume carefully even if text has spacing issues.

RESUME TEXT:
{cleaned_text}

TARGET JOB: {target_job}

Respond in this EXACT JSON format:
{{
    "name": "candidate name or Student if not found",
    "current_skills": ["skill1", "skill2", "skill3"],
    "experience_level": "fresher",
    "education": "degree if found or Not specified",
    "skills_gap": ["missing skill1", "missing skill2", "missing skill3"],
    "match_percentage": 45,
    "strengths": ["strength1", "strength2"],
    "summary": "2 line encouraging summary for this fresher"
}}

Return ONLY the JSON. No extra text. No markdown.
"""

    message = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.choices[0].message.content.strip()
    response_text = response_text.replace('```json', '').replace('```', '').strip()

    try:
        result = json.loads(response_text)
    except:
        result = {
            "name": "Student",
            "current_skills": ["HTML", "CSS", "Java"],
            "experience_level": "fresher",
            "education": "Engineering",
            "skills_gap": ["React", "SQL", "Git", "Python"],
            "match_percentage": 45,
            "strengths": ["Quick learner", "Good fundamentals"],
            "summary": "A motivated fresher with good foundational skills ready to grow."
        }
    return result

def generate_roadmap(skills_gap, target_job):
    prompt = f"""
You are a career coach for Indian freshers.
Create a practical day-by-day learning roadmap.

TARGET JOB: {target_job}
SKILLS TO LEARN: {', '.join(skills_gap)}

Respond in this EXACT JSON format:
{{
    "total_days": 21,
    "roadmap": [
        {{
            "days": "Day 1-3",
            "skill": "skill name",
            "topic": "exactly what to learn",
            "resource_name": "name of free resource",
            "resource_url": "https://youtube.com or free website"
        }}
    ],
    "tips": [
        "practical tip 1",
        "practical tip 2",
        "practical tip 3"
    ]
}}

Return ONLY the JSON. No extra text. No markdown.
"""

    message = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.choices[0].message.content.strip()
    response_text = response_text.replace('```json', '').replace('```', '').strip()

    try:
        result = json.loads(response_text)
    except:
        result = {
            "total_days": 21,
            "roadmap": [
                {
                    "days": "Day 1-3",
                    "skill": "HTML & CSS",
                    "topic": "Build a complete webpage from scratch",
                    "resource_name": "freeCodeCamp HTML CSS",
                    "resource_url": "https://www.youtube.com/watch?v=kUMe1FH4CHE"
                },
                {
                    "days": "Day 4-7",
                    "skill": "JavaScript",
                    "topic": "Variables, functions, DOM manipulation",
                    "resource_name": "JavaScript Full Course",
                    "resource_url": "https://www.youtube.com/watch?v=PkZNo7MFNFg"
                },
                {
                    "days": "Day 8-12",
                    "skill": "Python",
                    "topic": "Python basics, functions, file handling",
                    "resource_name": "Python for Beginners",
                    "resource_url": "https://www.youtube.com/watch?v=_uQrJ0TkZlc"
                },
                {
                    "days": "Day 13-17",
                    "skill": "SQL",
                    "topic": "SELECT, INSERT, JOIN queries",
                    "resource_name": "SQL Tutorial",
                    "resource_url": "https://www.youtube.com/watch?v=HXV3zeQKqGY"
                },
                {
                    "days": "Day 18-21",
                    "skill": "Git & GitHub",
                    "topic": "Version control basics",
                    "resource_name": "Git for Beginners",
                    "resource_url": "https://www.youtube.com/watch?v=RGOj5yH7evk"
                }
            ],
            "tips": [
                "Practice coding for at least 2 hours every day",
                "Build a small project after each skill",
                "Push all your code to GitHub daily"
            ]
        }
    return result

def get_interview_feedback(question, answer):
    prompt = f"""
You are a friendly interview coach for Indian freshers.

INTERVIEW QUESTION: {question}
CANDIDATE ANSWER: {answer}

Respond in this EXACT JSON format:
{{
    "score": 7,
    "good_points": ["what was good"],
    "improve_points": ["what to improve"],
    "better_answer": "give a better version of their answer",
    "next_question": "ask one follow up interview question"
}}

Return ONLY the JSON. No extra text. No markdown.
"""

    message = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.choices[0].message.content.strip()
    response_text = response_text.replace('```json', '').replace('```', '').strip()

    try:
        result = json.loads(response_text)
    except:
        result = {
            "score": 6,
            "good_points": ["Good attempt"],
            "improve_points": ["Be more specific"],
            "better_answer": "Try to include specific examples",
            "next_question": "Tell me about your projects"
        }
    return result

def generate_interview_question(target_job):
    prompt = f"""
Generate one interview question for a fresher
applying for {target_job} role at an Indian IT company.

Respond in this EXACT JSON format:
{{
    "question": "your interview question here",
    "type": "HR or Technical or Situational"
}}

Return ONLY the JSON. No extra text. No markdown.
"""

    message = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.choices[0].message.content.strip()
    response_text = response_text.replace('```json', '').replace('```', '').strip()

    try:
        result = json.loads(response_text)
    except:
        result = {
            "question": "Tell me about yourself.",
            "type": "HR"
        }
    return result

def generate_quiz(skill, topic):
    prompt = f"""
You are creating a strict quiz for an Indian fresher learning {skill}.
Topic: {topic}

Create exactly 3 multiple choice questions.
Questions must test REAL understanding — not memory.
Make wrong options believable — not obviously wrong.

Respond in this EXACT JSON format:
{{
    "questions": [
        {{
            "question": "clear specific question about {skill}",
            "options": ["option A", "option B", "option C", "option D"],
            "correct": 0,
            "explanation": "why this answer is correct"
        }},
        {{
            "question": "second question",
            "options": ["option A", "option B", "option C", "option D"],
            "correct": 1,
            "explanation": "why this answer is correct"
        }},
        {{
            "question": "third question",
            "options": ["option A", "option B", "option C", "option D"],
            "correct": 2,
            "explanation": "why this answer is correct"
        }}
    ]
}}

Return ONLY the JSON. No extra text. No markdown.
"""

    message = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1000,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.choices[0].message.content.strip()
    response_text = response_text.replace('```json','').replace('```','').strip()

    try:
        result = json.loads(response_text)
    except:
        result = {
            "questions": [
                {
                    "question": f"What is the main purpose of {skill}?",
                    "options": [
                        f"To build applications using {skill}",
                        "To design databases",
                        "To create graphics",
                        "To manage networks"
                    ],
                    "correct": 0,
                    "explanation": f"{skill} is primarily used to build applications."
                },
                {
                    "question": f"Which of these is a key feature of {skill}?",
                    "options": [
                        "It is only used for mobile apps",
                        "It supports multiple platforms",
                        "It cannot be used with databases",
                        "It requires expensive hardware"
                    ],
                    "correct": 1,
                    "explanation": f"{skill} supports multiple platforms and use cases."
                },
                {
                    "question": f"What should you do after learning {skill}?",
                    "options": [
                        "Stop learning immediately",
                        "Only read books about it",
                        "Build a real project using it",
                        "Avoid using it in interviews"
                    ],
                    "correct": 2,
                    "explanation": "Building real projects is the best way to solidify your learning."
                }
            ]
        }
    return result

def generate_job_recommendations(target_job, skills):
    prompt = f"""
You are a job placement expert for Indian freshers in 2024.

TARGET JOB: {target_job}
CANDIDATE SKILLS: {', '.join(skills)}

Generate realistic job recommendations for Indian freshers.

Respond in this EXACT JSON format:
{{
    "jobs": [
        {{
            "title": "Job Title",
            "company_type": "Product/Service/Startup",
            "location": "City, India or Remote",
            "salary": "3-5 LPA",
            "experience": "0-1 years",
            "skills_required": ["skill1", "skill2", "skill3"],
            "match_percentage": 85,
            "apply_link": "https://www.naukri.com",
            "tips": "One specific tip to get this job"
        }}
    ],
    "top_companies": ["Company1", "Company2", "Company3"],
    "application_tips": [
        "specific tip 1 for Indian freshers",
        "specific tip 2",
        "specific tip 3"
    ]
}}

Generate 5 job recommendations. Return ONLY JSON. No markdown.
"""

    message = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=2000,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.choices[0].message.content.strip()
    response_text = response_text.replace('```json','').replace('```','').strip()

    try:
        result = json.loads(response_text)
    except:
        result = {
            "jobs": [
                {
                    "title": "Junior Software Developer",
                    "company_type": "Service",
                    "location": "Chennai, India",
                    "salary": "3-5 LPA",
                    "experience": "0-1 years",
                    "skills_required": ["Python", "SQL", "Git"],
                    "match_percentage": 85,
                    "apply_link": "https://www.naukri.com",
                    "tips": "Highlight your personal projects in your resume"
                },
                {
                    "title": "Software Trainee",
                    "company_type": "Product",
                    "location": "Bangalore, India",
                    "salary": "4-6 LPA",
                    "experience": "Fresher",
                    "skills_required": ["Java", "HTML", "CSS"],
                    "match_percentage": 78,
                    "apply_link": "https://www.linkedin.com",
                    "tips": "Apply directly on company website"
                },
                {
                    "title": "Associate Engineer",
                    "company_type": "Service",
                    "location": "Hyderabad, India",
                    "salary": "3-4 LPA",
                    "experience": "0-2 years",
                    "skills_required": ["Python", "JavaScript", "Git"],
                    "match_percentage": 72,
                    "apply_link": "https://www.internshala.com",
                    "tips": "Mention your GitHub profile"
                }
            ],
            "top_companies": ["TCS", "Infosys", "Wipro", "HCL", "Cognizant"],
            "application_tips": [
                "Apply to at least 5 companies daily",
                "Customize your resume for each job",
                "Follow up after 1 week of applying"
            ]
        }
    return result

if __name__ == "__main__":
    app.run(debug=True)