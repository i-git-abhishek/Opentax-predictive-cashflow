# OpenTax Project: Local Setup & Git Guide

Welcome to the team! We are building the Cash Flow Predictive Provisioning system.
Please read this carefully and run the exact commands below to set up your local development environment.

## 1. Clone the Repository

Do not download the ZIP file. Use Git to clone the repository so you have access to the version history.
Open your terminal and run:

    git clone https://github.com/i-git-abhishek/Opentax-predictive-cashflow
    cd opentax-predictive-cashflow

## 2. Create Your Team Branch

Do NOT write code on the `main` branch. We are using a feature-branch workflow.
Run the command corresponding to your assigned team to create and switch to your isolated workspace:

    # Team 1 (Tally & Edge Integration):
    git checkout -b feature/tally-integration

    # Team 2 (FastAPI & Database):
    git checkout -b feature/database-ingestion

    # Team 3 (Twilio & Scheduler):
    git checkout -b feature/whatsapp-scheduler

## 3. Build Your Python Environment

We must isolate our Python packages so we don't break our global OS setups.
Navigate into the backend folder and create your virtual environment:

    cd backend
    python3 -m venv venv

Activate the virtual environment (you must do this every time you open a new terminal):

    # On Mac/Linux:
    source venv/bin/activate

    # On Windows (Command Prompt):
    venv\Scripts\activate

    # On Windows (Git Bash/PowerShell):
    source venv/Scripts/activate

## 4. Install Dependencies & Secrets

Now that your `(venv)` is active, install the shared project packages:

    pip install -r requirements.txt

Next, set up your local secrets file. This file is ignored by Git to keep API keys safe.
Copy the template to create your active `.env` file:

    # On Mac/Linux:
    cp .env.example .env

    # On Windows:
    copy .env.example .env

## 5. Daily Git Workflow (How to push code safely)

When you finish a feature, do not merge it directly into `main`. Follow this loop:

    1. Save your files.
    2. git add .
    3. git commit -m "feat: description of what you built"
    4. git push origin <your-branch-name>

Once pushed, go to the GitHub URL and open a "Pull Request" (PR) so the team lead can review and merge the code into `main`.

Whenever another team merges their code, update your local machine by running:
git pull origin main
