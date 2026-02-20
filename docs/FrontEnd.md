==================================================

1. Overview

==================================================

This document describes the fully implemented authentication and frontend styling stack used in this project.

This setup is NOT optional boilerplate.
It is a required, shared configuration that ensures consistent authentication behavior and frontend styling across all team members’ local environments.

The stack consists of:

Google OAuth via django-allauth
Django Sites framework
Centralized OAuth credentials
TailwindCSS utility framework
DaisyUI component system
Node-based Tailwind compilation pipeline

All frontend work and recommendation logic must assume this configuration.

==================================================

2. Setup for Google Ouath and TailwindCCS

==================================================
Follow MHW_API setup to begin:
Step 1  —  Clone & Environment

git clone <repository-url>
cd Capstone-Project/mysite
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate

🔐 Step 2 -  Get Google Ouath Running

2.1 Start the serve

We must first create a superuser. Run this command:
   python manage.py createsuperuser
Use deafult username for simplicty and make own password
Start your server: python manage.py runserver
Go to http://127.0.0.1:8000/admin
Log in with your local superuser account
    User:root
    Password:

2.2 Configure Django Sites

On the Admin sidebar, look for Sites > Sites.
Click the existing site (usually example.com).
Change the Domain name and Display name both to 127.0.0.1:8000.
Click Save.

2.3 Add Google Social Application

This is where you use my keys to connect your local app to my Google project:
In the Admin sidebar, go to Social Accounts > Social applications.
Click Add Social Application.
Fill in these exact details:
Provider: Google
Name: Google Login
Client id: [PASTE THE CLIENT ID I SENT YOU]
Secret key: [PASTE THE SECRET KEY I SENT YOU]
Crucial Step: In the Sites section at the bottom, select 127.0.0.1:8000 in the "Available sites" box and click the arrow to move it to the Chosen sites box.
Click Save.

🎨 Step 3 — TailwindCSS + DaisyUI Setup
3.1 Install Node dependencies

From the project root (mysite/):
   npm install
This installs:
   TailwindCSS
   Tailwind CLI
   DaisyUI
   PostCSS & Autoprefixer

3.2 Verify Tailwind input file

Make sure this file exists:
   static/css/main.css
It must contain:
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
⚠️ Do not edit output.css manually.

3.3 Build Tailwind (watch mode)

From the project root:
   node_modules/.bin/tailwindcss \
   -i ./static/css/main.css \
   -o ./static/css/output.css \
   --watch

You should see output similar to:
   tailwindcss v4.x.x
   🌼 daisyUI x.x.x
   Done in XXXms
Leave this running during development.


▶️ Step 4 — Run the App

Open two terminals:
Terminal 1 — Tailwind
   node_modules/.bin/tailwindcss \
   -i ./static/css/main.css \
   -o ./static/css/output.css \
   --watch
Terminal 2 — Django
   python manage.py runserver

NOTE: output.css being red in the editor is normal (generated file)

==================================================

END OF DOCUMENT

==================================================