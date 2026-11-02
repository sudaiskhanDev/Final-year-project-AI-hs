# AI-Based Recruitment System - Backend

This is the backend (server side) of our Final Year Project: an AI-powered recruitment platform.
It is built with **Django** (plain function-based views, no Django REST Framework) and exposes a **JSON REST API** that any frontend can use.

If you are a teammate who just received this repo link: follow the steps below from top to bottom and the backend will run on your computer. You do **not** need to read the code to use it.

---

## Table of Contents

1. [What does this backend do?](#1-what-does-this-backend-do)
2. [What you need before starting](#2-what-you-need-before-starting)
3. [Folder structure](#3-folder-structure)
4. [Quick start (short version)](#4-quick-start-short-version)
5. [Full setup, step by step](#5-full-setup-step-by-step)
6. [Database tables](#6-database-tables)
7. [API guide](#7-api-guide)
8. [Recommended order to test the API](#8-recommended-order-to-test-the-api)
9. [AI models](#9-ai-models)
10. [Notes for the frontend developer](#10-notes-for-the-frontend-developer)
11. [Common problems and fixes](#11-common-problems-and-fixes)
12. [Security notes](#12-security-notes)
13. [Team](#13-team)

---

## 1. What does this backend do?

There are three types of users:

| Role | What they can do |
|------|------------------|
| **Candidate** | Register, upload CV, add skills/experience/qualifications/languages, apply for jobs, attend AI interviews |
| **HR** | Post jobs, see applications, manage interviews and scores |
| **Admin** | Manage users, HR profiles and final hiring decisions |

Main features:

- Register, login, logout (session-based login)
- Candidate and HR profiles (created automatically when a user registers)
- Master lists: skills, qualifications, languages
- Resume upload (PDF / DOCX)
- Job posting with required skills and qualifications
- Job applications
- Resume vs job matching scores
- AI interviews with questions, answers and scores
- Video analysis scores (eye contact, dress, confidence)
- Final hiring results (score, ranking, selected / shortlisted / rejected)
- **2 AI models:**
  - **CV Parser** - reads a PDF/DOCX CV and returns structured data (name, email, skills, education, experience...)
  - **Question Generator** - creates interview questions from a job title, description and skills

Numbers at a glance: **20 database tables**, **6 Django apps**, **100+ API endpoints**.

---

## 2. What you need before starting

Install these first:

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.13 (3.12 should also work) | Tick "Add Python to PATH" on Windows |
| Git | any recent | To clone the repo |
| pip | comes with Python | Or use `uv` if you prefer |
| VS Code (optional) | any | Recommended |
| Thunder Client or Postman (optional) | any | To test the API |

Also make sure you have:

- About **5 GB free disk space** (PyTorch and the AI models are big)
- A decent internet connection for the first install

MySQL is **not required**. The project uses **SQLite** by default, which needs no setup.

---

## 3. Folder structure

```
Final year project/
├── backend/                         <- EVERYTHING you need is in this folder
│   ├── manage.py                    # Django command runner (runserver, migrate...)
│   ├── requirements.txt             # All Python packages
│   ├── db.sqlite3                   # Local database file (created after migrate)
│   │
│   ├── config/                      # Project settings
│   │   ├── settings.py              # Main settings (apps, database, CORS, media)
│   │   ├── urls.py                  # Root URL file - connects all apps
│   │   ├── asgi.py
│   │   └── wsgi.py
│   │
│   ├── apps/                        # All Django apps (one per feature area)
│   │   │
│   │   ├── accounts/                # Users, login, HR + candidate profiles
│   │   │   ├── models.py            # User, HRProfile, CandidateProfile
│   │   │   ├── signals.py           # Auto-creates a profile after registration
│   │   │   ├── urls.py
│   │   │   └── views/
│   │   │       ├── auth_views.py             # register, login, logout, me
│   │   │       ├── user_views.py             # user CRUD
│   │   │       ├── hr_profile_views.py       # HR profile CRUD
│   │   │       └── candidate_profile_views.py
│   │   │
│   │   ├── masterdata/              # Lookup tables
│   │   │   ├── models.py            # Skill, Qualification, Language
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   │
│   │   ├── candidates/              # Everything that belongs to a candidate
│   │   │   ├── models.py            # Resume, CandExperience, CandidateSkill,
│   │   │   │                        # CandidateQualification, CandLanguage
│   │   │   ├── urls.py
│   │   │   └── views/
│   │   │       ├── resume_views.py
│   │   │       ├── cand_experience_views.py
│   │   │       ├── cand_skill_views.py
│   │   │       ├── cand_qualification_views.py
│   │   │       └── cand_language_views.py
│   │   │
│   │   ├── recruitment/             # Jobs and applications
│   │   │   ├── models.py            # Job, JobSkill, JobQualification, Application
│   │   │   ├── urls.py
│   │   │   └── views/
│   │   │       ├── jobs_views.py
│   │   │       ├── job_skill_views.py
│   │   │       ├── job_qualification_views.py
│   │   │       └── application_views.py
│   │   │
│   │   ├── hiring/                  # Matching, interviews, results
│   │   │   ├── models.py            # ResumeMatching, AIInterview, Question,
│   │   │   │                        # VideoAnalysis, HiringResult
│   │   │   ├── urls.py
│   │   │   └── views/
│   │   │       ├── resume_matching_views.py
│   │   │       ├── ai_interview_views.py
│   │   │       ├── question_views.py
│   │   │       ├── video_analysis_views.py
│   │   │       └── hiring_result_views.py
│   │   │
│   │   └── ai_services/             # Connects the AI models to the API
│   │       ├── views.py
│   │       ├── urls.py
│   │       └── services/
│   │           ├── cv_parser.py             # Uses the NER model
│   │           └── question_generator.py    # Uses the question model
│   │
│   ├── ai_models/                   # The trained AI models (large files)
│   │   ├── ner/                     # CV parsing model
│   │   │   ├── model.safetensors
│   │   │   ├── config.json, tokenizer.json, vocab.txt ...
│   │   │   ├── onnx/                # Faster ONNX version of the model
│   │   │   ├── training/            # Scripts used to train and export the model
│   │   │   ├── tests/
│   │   │   └── docs/
│   │   └── qs_model/                # Question generation model
│   │       ├── model.safetensors
│   │       ├── config.json
│   │       ├── generation_config.json
│   │       ├── tokenizer.json
│   │       └── tokenizer_config.json
│   │
│   ├── utils/                       # Small helpers used everywhere
│   │   ├── response.py              # success_response(), error_response()
│   │   ├── validators.py            # parse_json(), require_fields()
│   │   └── decorators.py            # login_required_json, admin_required_json
│   │
│   └── media/                       # Uploaded files (created automatically)
│       └── resumes/                 # Uploaded CVs go here
│
├── frontend/                        # Next.js frontend (NOT needed for backend setup)
├── index.html                       # Simple helper page
└── README.md                        # This file
```

Each Django app also has `migrations/` (database history), `admin.py`, `apps.py`, and `__init__.py`. You do not need to touch them. Ignore the `__pycache__` folders; Python creates them automatically.

**Tip:** all commands in this guide are run from inside the `backend` folder unless stated otherwise.

---

## 4. Quick start (short version)

For people who just want it running. Windows PowerShell commands shown; see Section 5 for Mac/Linux and details.

```powershell
git clone <your-repo-url>
cd "<repo-folder>/backend"

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Make sure backend/ai_models/ner and backend/ai_models/qs_model exist (see Step 6)

python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/ - the server is running. If anything fails, check Section 11.

---

## 5. Full setup, step by step

### Step 1: Clone the repository

```bash
git clone <your-repo-url>
cd "<repo-folder>/backend"
```

Replace `<your-repo-url>` with the GitHub link and `<repo-folder>` with the folder name Git created (for example `Final year project`). If the folder name has spaces, keep the quotes.

### Step 2: Create a virtual environment

A virtual environment keeps this project's packages separate from the rest of your computer.

```bash
python -m venv .venv
```

Now activate it:

**Windows PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows CMD**
```cmd
.venv\Scripts\activate.bat
```

**Mac / Linux**
```bash
source .venv/bin/activate
```

You will see `(.venv)` at the start of your terminal line. That means it worked.

> If PowerShell says "running scripts is disabled", run this once, then try again:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

> Using `uv` instead? Run `uv venv`, activate the same way, and use `uv pip install ...` in place of `pip install ...`.

### Step 3: Install the Python packages

```bash
pip install -r requirements.txt
```

This installs Django, PyTorch, Transformers, spaCy, pdfplumber, PyMuPDF, python-docx and more.
**This can take 5 to 15 minutes** because PyTorch is about 2 GB. Please be patient.

If the PyTorch install is too slow or fails, install the CPU version first, then run the command above again:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Step 4: Download the spaCy English model

```bash
python -m spacy download en_core_web_sm
```

If that fails, use the direct link:

```bash
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
```

### Step 5: (Optional) Environment variables

The default setup works without any `.env` file (SQLite database, debug mode on).
If the project contains a `.env.example` file, copy it and edit the values:

```bash
cp .env.example .env
```

Example `.env` (only needed if you switch to MySQL or want custom settings):

```env
SECRET_KEY=change-this-to-a-long-random-string
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=ai_recruitment
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306

CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Never upload your real `.env` to GitHub.

### Step 6: Check the AI models

The AI models are large files (about 2 GB or more). Look inside `backend/ai_models/`:

```
backend/ai_models/
├── ner/          <- CV parsing model
└── qs_model/     <- question generation model
```

- **If both folders are there and contain files** (for example `model.safetensors`), you are done. Go to Step 7.
- **If they are missing or empty**, GitHub could not store the big files. Download `ai_models.zip` from here:

  **[PASTE GOOGLE DRIVE LINK HERE]**

  Unzip it so the folders end up exactly at `backend/ai_models/ner` and `backend/ai_models/qs_model`.

Check from the terminal:

```bash
dir ai_models        # Windows
ls ai_models         # Mac / Linux
```

You should see `ner` and `qs_model`.

### Step 7: Create the database tables

```bash
python manage.py makemigrations
python manage.py migrate
```

This creates the `db.sqlite3` file (if it is not there) and builds all 20 tables.

### Step 8: Create an admin user

Open the Django shell:

```bash
python manage.py shell
```

Paste this:

```python
from apps.accounts.models import User
from django.contrib.auth.hashers import make_password

User.objects.create(
    full_name="System Admin",
    email="admin@example.com",
    phone_no="03000000000",
    role="admin",
    is_staff=True,
    is_superuser=True,
    password=make_password("admin12345"),
)
print("Admin created")
exit()
```

Admin login: `admin@example.com` / `admin12345`
(Change this password for anything other than local testing.)

Candidates and HR users do not need this step. They register through the API.

### Step 9: Start the server

```bash
python manage.py runserver
```

Server address: **http://127.0.0.1:8000/**

Keep this terminal open while you work. Press `Ctrl + C` to stop the server.

### Step 10: Check that it works

Open a second terminal and run:

```bash
curl http://127.0.0.1:8000/api/skills/
```

You should get JSON back. If you do, the backend is running.

---

## 6. Database tables

There are **20 tables** across 5 database apps (plus the AI services app, which has no tables).

**accounts**

| Table | What it stores |
|-------|----------------|
| user | Every user: full_name, email, phone_no, password, role (admin / hr / candidate) |
| hr_profile | HR details: department, designation (linked to a user) |
| candidate_profile | Candidate details: date_of_birth, gender, address (linked to a user) |

**masterdata**

| Table | What it stores |
|-------|----------------|
| skills | Master list of skills (Python, React...) |
| qualification | Master list of qualifications (BSCS, MBA...) |
| languages | Master list of languages (English, Urdu...) |

**candidates**

| Table | What it stores |
|-------|----------------|
| resume | Uploaded CV files |
| cand_experience | Work experience entries |
| candidate_skill | Which candidate has which skill |
| candidate_qualification | Which candidate has which qualification |
| cand_languages | Which candidate speaks which language, and how well |

**recruitment**

| Table | What it stores |
|-------|----------------|
| jobs | Job postings created by HR |
| job_skills | Skills required for a job |
| job_qualification | Qualifications required for a job |
| applications | A candidate applying to a job with a resume |

**hiring**

| Table | What it stores |
|-------|----------------|
| resume_matching | CV vs job scores |
| ai_interviews | Interview sessions |
| question | Interview questions, answers and scores |
| video_analysis | Eye contact, dress, confidence scores |
| hiring_results | Final score, ranking, decision |

**How the tables connect (simple version)**

```
User ──(1 to 1)── HRProfile          (if role = hr)
User ──(1 to 1)── CandidateProfile   (if role = candidate)

HRProfile        ──(1 to many)── Job
CandidateProfile ──(1 to many)── Resume, CandExperience, CandidateSkill,
                                 CandidateQualification, CandLanguage, Application

Job              ──(1 to many)── JobSkill, JobQualification, Application
Application      ──(1 to 1)────  ResumeMatching
Application      ──(1 to many)── AIInterview
Application      ──(1 to 1)────  HiringResult
AIInterview      ──(1 to many)── Question
AIInterview      ──(1 to 1)────  VideoAnalysis
```

**Very important for beginners:**
`candidate_id` means the **candidate profile ID**, and `hr_id` means the **HR profile ID**. They are **not** the same as `user_id`. Always get these IDs from the profile list endpoints.

**Rules the database enforces (you get a 409 error if you break them):**

- A candidate can apply to the same job only once
- One resume matching per application
- One video analysis per interview
- One hiring result per application
- The same skill / qualification / language cannot be added twice for one candidate

---

## 7. API guide

**Base URL:** `http://127.0.0.1:8000`

### 7.1 Response format

Every endpoint returns JSON in the same shape.

Success:

```json
{
  "success": true,
  "message": "Description of what happened",
  "data": { }
}
```

Error:

```json
{
  "success": false,
  "message": "What went wrong",
  "errors": null
}
```

Common status codes:

| Code | Meaning |
|------|---------|
| 200 / 201 | Success / created |
| 400 | Bad request (missing fields, invalid JSON) |
| 401 | Not logged in |
| 403 | Logged in but not allowed (for example, admin only) |
| 404 | Record not found |
| 409 | Duplicate (breaks a unique rule) |

### 7.2 How login works

The backend uses **session login** (cookies), not tokens.

1. Call `POST /api/auth/login/`
2. The server sends back a `sessionid` cookie
3. Send that cookie with every later request (Thunder Client / Postman do it automatically; in browser code use `credentials: 'include'`)

Two helper decorators in `utils/decorators.py` protect endpoints:

- `login_required_json` - returns 401 if not logged in
- `admin_required_json` - returns 401 if not logged in, 403 if the user is not an admin

Some endpoints may be left open while we test. Check the views before going live (see Section 12).

### 7.3 Authentication (`/api/auth/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Create an account (role: `candidate` or `hr`) |
| POST | `/api/auth/login/` | Login (sets the session cookie) |
| POST | `/api/auth/logout/` | Logout |
| GET | `/api/auth/me/` | Get the currently logged-in user |

Register:

```json
{
  "full_name": "Ali Khan",
  "email": "ali@example.com",
  "password": "test12345",
  "confirm_password": "test12345",
  "phone_no": "03001234567",
  "role": "candidate"
}
```

Login:

```json
{
  "email": "ali@example.com",
  "password": "test12345"
}
```

After registering, a candidate profile (or HR profile) is created automatically.

### 7.4 Users (`/api/users/`)

| Method | Endpoint |
|--------|----------|
| GET | `/api/users/` |
| GET | `/api/users/<id>/` |
| PUT | `/api/users/<id>/update/` |
| DELETE | `/api/users/<id>/delete/` |

### 7.5 The standard CRUD pattern

Most modules use the same five endpoints. Replace `<name>` with the module path from the table below.

| Action | Method | Endpoint |
|--------|--------|----------|
| List all | GET | `/api/<name>/` |
| Create | POST | `/api/<name>/create/` |
| Get one | GET | `/api/<name>/<id>/` |
| Update | PUT | `/api/<name>/<id>/update/` |
| Delete | DELETE | `/api/<name>/<id>/delete/` |

| Module | `<name>` | Required body fields when creating |
|--------|----------|------------------------------------|
| HR profiles | `hr-profiles` | `user_id`, `department`, `designation` |
| Candidate profiles | `candidate-profiles` | `user_id`, `date_of_birth`, `gender`, `address` |
| Resumes | `resumes` | `candidate_id`, `file` (form-data) |
| Experience | `experiences` | `candidate_id`, `company_name`, `designation`, `start_date`, `end_date` |
| Candidate skills | `candidate-skills` | `candidate_id`, `skill_id` |
| Candidate qualifications | `candidate-qualifications` | `candidate_id`, `qualification_id` |
| Candidate languages | `candidate-languages` | `candidate_id`, `lang_id`, `proficiency_lvl` |
| Jobs | `jobs` | `hr_id`, `job_title`, `job_description`, `required_exp`, `minimum_score`, `due_date` |
| Job skills | `job-skills` | `job_id`, `skill_id` |
| Job qualifications | `job-qualifications` | `job_id`, `qualification_id` |
| Applications | `applications` | `candidate_id`, `job_id`, `resume_id` |
| Resume matching | `resume-matchings` | `application_id`, `skills_score`, `experience_score`, `qualification_score`, `total_score`, `status` |
| AI interviews | `ai-interviews` | `application_id`, `interview_mode`, `interview_round`, `video_path`, `overall_score`, `interview_status` |
| Questions | `questions` | `interview_id`, `question_text`, `answer_text`, `answer_score`, `time_taken` |
| Video analysis | `video-analyses` | `interview_id`, `eye_contact_score`, `dress_code`, `dress_score`, `confidence_score`, `overall_video_score` |
| Hiring results | `hiring-results` | `application_id`, `final_score`, `ranking`, `selection_status`, `remarks`, `decision_date` |

### 7.6 Master data (skills, qualifications, languages)

These three use the **same URL** with different methods:

| Method | Skills | Qualifications | Languages |
|--------|--------|----------------|-----------|
| GET (list) | `/api/skills/` | `/api/qualifications/` | `/api/languages/` |
| POST (create) | `/api/skills/` | `/api/qualifications/` | `/api/languages/` |
| GET (one) | `/api/skills/<id>/` | `/api/qualifications/<id>/` | `/api/languages/<id>/` |
| PUT (update) | `/api/skills/<id>/` | `/api/qualifications/<id>/` | `/api/languages/<id>/` |
| DELETE | `/api/skills/<id>/` | `/api/qualifications/<id>/` | `/api/languages/<id>/` |

Bodies:

```json
{ "skill_name": "Python" }
{ "qualification_name": "BSCS" }
{ "language_name": "English" }
```

### 7.7 Request body examples

**HR profile** - `POST /api/hr-profiles/create/`
```json
{ "user_id": 2, "department": "Human Resources", "designation": "HR Manager" }
```

**Candidate profile** - `POST /api/candidate-profiles/create/`
```json
{ "user_id": 1, "date_of_birth": "2000-05-15", "gender": "male", "address": "Karachi, Pakistan" }
```

**Resume upload** - `POST /api/resumes/create/` (use **form-data**, not JSON)
```
candidate_id: 1
file: <choose a PDF or DOCX file>
```

**Experience** - `POST /api/experiences/create/`
```json
{
  "candidate_id": 1,
  "company_name": "Google",
  "designation": "Software Engineer",
  "start_date": "2022-01-15",
  "end_date": "2024-06-30"
}
```

**Candidate language** - `POST /api/candidate-languages/create/`
```json
{ "candidate_id": 1, "lang_id": 1, "proficiency_lvl": "intermediate" }
```
Allowed levels: `basic`, `intermediate`, `fluent`, `native`

**Job** - `POST /api/jobs/create/`
```json
{
  "hr_id": 1,
  "job_title": "Python Developer",
  "job_description": "We need a Django developer.",
  "required_exp": 2.5,
  "minimum_score": 65.0,
  "due_date": "2026-12-31"
}
```

**Job skill / job qualification**
```json
{ "job_id": 1, "skill_id": 1 }
{ "job_id": 1, "qualification_id": 1 }
```

**Application** - `POST /api/applications/create/`
```json
{ "candidate_id": 1, "job_id": 1, "resume_id": 1 }
```

**Resume matching** - `POST /api/resume-matchings/create/`
```json
{
  "application_id": 1,
  "skills_score": 80.0,
  "experience_score": 75.0,
  "qualification_score": 85.0,
  "total_score": 80.0,
  "status": "completed"
}
```
Allowed status: `pending`, `completed`, `failed`

**AI interview** - `POST /api/ai-interviews/create/`
```json
{
  "application_id": 1,
  "interview_mode": "ai",
  "interview_round": "1st Round",
  "video_path": "/media/interviews/video.mp4",
  "overall_score": 0,
  "interview_status": "pending"
}
```
Allowed modes: `ai`, `human`, `video`
Allowed statuses: `pending`, `in_progress`, `completed`, `cancelled`
When the status becomes `completed`, `completed_at` is filled in automatically.

**Question** - `POST /api/questions/create/`
```json
{
  "interview_id": 1,
  "question_text": "What is Django?",
  "answer_text": null,
  "answer_score": 0,
  "time_taken": 0
}
```

Save the candidate's answer later with `PUT /api/questions/1/update/`:
```json
{
  "answer_text": "Django is a Python web framework.",
  "answer_score": 85.0,
  "time_taken": 45
}
```

**Video analysis** - `POST /api/video-analyses/create/`
```json
{
  "interview_id": 1,
  "eye_contact_score": 75.0,
  "dress_code": "formal",
  "dress_score": 80.0,
  "confidence_score": 70.0,
  "overall_video_score": 75.0
}
```

**Hiring result** - `POST /api/hiring-results/create/`
```json
{
  "application_id": 1,
  "final_score": 85.0,
  "ranking": 1,
  "selection_status": "shortlisted",
  "remarks": "Strong technical skills.",
  "decision_date": "2026-12-31"
}
```
Allowed decisions: `selected`, `shortlisted`, `rejected`, `on_hold`

### 7.8 AI endpoints (`/api/ai/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ai/generate-question/` | Generate an interview question |
| POST | `/api/ai/parse-cv/` | Parse a CV file you upload (form-data) |
| POST | `/api/ai/parse-cv/<resume_id>/` | Parse a resume already saved in the database (login required, must be your own resume) |

**The first AI call is slow (30 to 60 seconds)** because the models load into memory. After that it is fast.

Generate a question:

```json
POST /api/ai/generate-question/
{
  "job_title": "Python Developer",
  "job_description": "Django developer with 2+ years experience.",
  "required_experience": "2 years",
  "skills": "Python, Django, PostgreSQL",
  "question_type": "Scenario"
}
```

Response:

```json
{
  "success": true,
  "message": "Question generated",
  "data": { "question": "..." }
}
```

Parse a CV (form-data):

```
POST /api/ai/parse-cv/
file: <PDF or DOCX>
```

The response contains structured data such as personal info, skills, education, experience, projects, certifications and languages.

---

## 8. Recommended order to test the API

Some records depend on others, so create them in this order. Use the `id` returned by each step in the next one.

1. **Register** one candidate and one HR user (`/api/auth/register/`), then **login** (`/api/auth/login/`)
2. Check `/api/auth/me/` to confirm you are logged in
3. Add **skills**, **qualifications** and **languages** (master data)
4. Call `GET /api/candidate-profiles/` and `GET /api/hr-profiles/` to get your `candidate_id` and `hr_id`
5. Update the profiles with details (department, DOB, address...)
6. **Upload a resume** (`/api/resumes/create/`, form-data)
7. Add candidate **experience**, **skills**, **qualifications**, **languages**
8. HR creates a **job**, then adds **job skills** and **job qualifications**
9. Candidate creates an **application** (needs `candidate_id`, `job_id`, `resume_id`)
10. Add a **resume matching** for the application
11. Create an **AI interview**, then add **questions** (you can use `/api/ai/generate-question/`)
12. Update questions with answers and scores, add a **video analysis**
13. Finish with a **hiring result**

---

## 9. AI models

Models live in `backend/ai_models/` and are NOT trained again when you run the project. They are only loaded and used.

| Model | Folder | Used by | What it does |
|-------|--------|---------|--------------|
| NER (CV parser) | `ai_models/ner/` | `apps/ai_services/services/cv_parser.py` | Reads a CV and extracts name, email, skills, education, experience, etc. |
| Question generator | `ai_models/qs_model/` | `apps/ai_services/services/question_generator.py` | Creates interview questions from job details |
| spaCy `en_core_web_sm` | installed with `python -m spacy download` | CV parser | Extra language processing / fallback |

Good to know:

- Models are big, so the first request after starting the server is slow
- Models stay in memory after the first call, so later calls are quick
- The `ner/training/` folder contains the scripts used to train and export the CV model. You do not need them to run the backend
- The CV parser accepts **PDF** and **DOCX** files only

---

## 10. Notes for the frontend developer

You are building your own frontend, so here is what you need:

- **Base URL:** `http://127.0.0.1:8000`
- **Content type:** send JSON with `Content-Type: application/json`. For file uploads use `FormData`
- **Login uses cookies.** Add `credentials: 'include'` to every `fetch` call (or `withCredentials: true` in axios):

```javascript
// Login
const res = await fetch("http://127.0.0.1:8000/api/auth/login/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  credentials: "include",
  body: JSON.stringify({ email: "ali@example.com", password: "test12345" }),
});
const result = await res.json();
if (result.success) {
  console.log(result.data);
}
```

```javascript
// Upload a resume
const formData = new FormData();
formData.append("candidate_id", 1);
formData.append("file", fileInput.files[0]);

await fetch("http://127.0.0.1:8000/api/resumes/create/", {
  method: "POST",
  credentials: "include",
  body: formData,   // do NOT set Content-Type yourself for FormData
});
```

- Always check `result.success` first, then use `result.data`. On errors, show `result.message`
- If your frontend runs on `http://localhost:3000`, make sure it is allowed in the CORS settings (`config/settings.py`)
- Uploaded files are served from `/media/...`

---

## 11. Common problems and fixes

**1. `ModuleNotFoundError: No module named 'xyz'`**
Your virtual environment is probably not active, or packages are missing.
```bash
pip install -r requirements.txt
```
Make sure you see `(.venv)` in your terminal.

**2. `OSError: Can't find model 'en_core_web_sm'`**
```bash
python -m spacy download en_core_web_sm
```

**3. `FileNotFoundError` mentioning `ai_models/qs_model` or `ai_models/ner`**
The AI models are missing. Do Step 6 again and check the folder names exactly.

**4. CORS error in the browser**
In `config/settings.py` (development only):
```python
CORS_ALLOW_ALL_ORIGINS = True
```

**5. `401 Authentication required`**
You are not logged in, or your request is not sending the cookie. Login first and use `credentials: 'include'`.

**6. `409` duplicate error**
This is a database rule, not a bug (for example applying to the same job twice).

**7. First AI request takes very long**
Normal. The model loads into memory the first time. Wait up to a minute.

**8. `NOT NULL constraint failed` or strange migration errors**
Reset the local database (**this deletes all local data**):
```bash
# Windows
del db.sqlite3
# Mac / Linux
rm db.sqlite3

python manage.py makemigrations
python manage.py migrate
```
Then create the admin again (Step 8).

**9. PyTorch install is too slow or fails**
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**10. Port 8000 already in use**
Run on another port:
```bash
python manage.py runserver 8001
```

**11. `python` or `pip` is not recognized**
Python is not in your PATH. Reinstall Python and tick "Add Python to PATH", or try `py` instead of `python` on Windows.

---

## 12. Security notes

This project is for a final-year demo. Before using it for real:

- Set `DEBUG = False`
- Remove `CORS_ALLOW_ALL_ORIGINS = True` and list only your real frontend URL
- Use a strong `SECRET_KEY` stored in `.env`
- Change the default admin password
- Use HTTPS and a production server (gunicorn / uvicorn), not `runserver`
- Add `@login_required_json` and `@admin_required_json` (from `utils/decorators.py`) to every endpoint that should be protected
- Add rate limiting and file size / type checks for uploads
- Never commit `.env`, `db.sqlite3` with real data, or uploaded CVs

---

ok?