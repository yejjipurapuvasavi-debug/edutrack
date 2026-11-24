# EduTrack — Student Marks Management System

A Flask + SQLite academic dashboard prototype with Admin, Faculty and Student roles.

## Run locally (Windows / VS Code)

1. Install Python 3.10 or newer.
2. Open this folder in VS Code.
3. Open Terminal and run:

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py app.py
```

4. Open http://127.0.0.1:5000

## Local presentation accounts

These local-only credentials are provided for testing. They are not displayed on the sign-in page.

| Role | Account ID | Password |
|---|---|---|
| Admin | admin | Admin@123 |
| Faculty | faculty | Faculty@123 |
| Student | 25KD1A05X8 | Student@123 |
| Student | 25KD1A05X4 | Student@123 |

Change these credentials and `SECRET_KEY` before any public deployment. This is a classroom prototype, not a production-ready student information system.

## Initial records
Two CSE-F students are seeded in `edutrack.db` on first run:
- 25KD1A05X8 — V. Bhuvana Kruthi
- 25KD1A05X4 — V. Gayathri

Marks and attendance are stored in SQLite. Faculty/Admin can update marks and attendance. Students can view only their own record. Admin can add student records and view the mark-change activity log.

## Notes / next build phase
- The supplied attendance percentages (95%, 85%) are stored as the latest overall attendance. Period-level entries can be added from the student record page.
- The supplied Mid 1 / Mid 2 marks are stored out of 150.
- Semester trend graphs should only show semester data after records for each semester have been entered. This starter visualizes the current assessment set and does not fabricate past semester marks.
- Expand the academic setup tables, faculty-to-section assignments, result approval/publication workflow, semester-specific result history and per-subject attendance before production use.
- Use synthetic data for public demonstrations; protect real student information and deploy with HTTPS, secure secrets, CSRF protection, backups and institution-approved access controls.
