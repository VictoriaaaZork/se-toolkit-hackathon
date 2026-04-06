# QuestForge V2

A web app that helps students build study habits with small, structured quests.

## Demo
- Screenshot 1: goal creation + first quest
- Screenshot 2: complete quest + generate next quest
- Screenshot 3: difficulty-based quests in history

## Product context

### End users
- Students preparing for exams and coursework.

### Problem
- Students have vague study goals and struggle with consistency.

### Solution
- Convert a big study goal into one concrete 2040 minute quest, let the user complete it, and generate the next one.

## Features

### Implemented
- Create a study goal
- Generate first quest
- Mark quest completed
- Generate next quest
- Difficulty selection: easy / medium / hard
- Non-repeating quest generation logic
- FastAPI backend + SQLite DB + web client (HTML/CSS/JS)

### Not yet implemented
- Authentication
- Multi-user support
- Progress analytics dashboard
- Reminder notifications

## Usage
1. Open the web app.
2. Enter a study goal.
3. Select difficulty.
4. Click **Create quest**.
5. Click **Complete** when done.
6. Select difficulty and click **Generate next quest**.

## Deployment

### VM OS
- Ubuntu 24.04

### What to install
- python3
- python3-venv
- python3-pip
- git

### Step-by-step deployment
```bash
git clone https://github.com/VictoriaaaZork/se-toolkit-hackathon.git
cd se-toolkit-hackathon

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# set OPENAI_API_KEY / OPENAI_MODEL / OPENAI_BASE_URL in .env

uvicorn main:app --host 0.0.0.0 --port 8000
