# student_manager

╔══════════════════════════════════════════════════════════╗
║       STUDENT MANAGEMENT SYSTEM — Setup Guide            ║
╚══════════════════════════════════════════════════════════╝

REQUIREMENTS
────────────
  • Python 3.8+  (https://python.org)
  • XAMPP        (https://apachefriends.org)
  • mysql-connector-python package

STEP 1 — Install the MySQL connector
──────────────────────────────────────
  Open Command Prompt and run:

    pip install mysql-connector-python
    python -m pip install mysql-connector-python

STEP 2 — Start XAMPP
──────────────────────
  1. Open XAMPP Control Panel
  2. Start "MySQL" (Apache is NOT needed)

STEP 3 — Create the Database (2 options)
──────────────────────────────────────────
  Option A (Auto): Just run the Python app — it creates the
                   database and table automatically!

  Option B (Manual): Open phpMyAdmin → Import → select student_db.sql

STEP 4 — Run the App
──────────────────────
  Double-click student_manager.py
  OR run in terminal:

    python student_manager.py

FEATURES
────────
  ✅ Add students (ID, Name, Email, Course, Year Level)
  ✅ Delete selected student with confirmation
  ✅ Live search by name / ID / course
  ✅ Stats dashboard (total students, courses, year levels)
  ✅ Alternating row colors for readability
  ✅ Auto-creates database on first launch

DATABASE CONFIG (edit in student_manager.py line ~22)
──────────────────────────────────────────────────────
  host:     localhost
  user:     root
  password: (empty — default XAMPP)
  database: student_management
