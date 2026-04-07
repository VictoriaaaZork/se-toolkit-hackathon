# QuestForge V2

A web app that helps students build study habits with small, structured quests.

## Demo
- Screenshot 1: goal creation + first quest generation
- ![Overview](images/demo-1-overview.png)
- Screenshot 2: quest completion + next quest generation
- ![Create goal](images/demo-2-create-goal.png)
- Screenshot 3: difficulty-based quests in history
- ![Goals list](images/demo-2-goals-list.png)

## Product context

### End users
- Students preparing for exams and coursework.

### Problem that my product solves
- Students have vague study goals and struggle with consistency.
- They need clear, short, actionable tasks.

### My solution
- User enters a study goal.
- System generates one concrete 2040 minute quest.
- User marks quest as completed and generates next quests.
- Difficulty levels and non-repeating logic improve study progression.

## Features

### Implemented
- Create goal
- Generate first quest
- Generate next quest
- Mark quest as completed
- Difficulty selection (easy/medium/hard)
- Non-repeating quest generation
- FastAPI + SQLite + plain HTML/CSS/JS

### Not yet implemented
- Authentication
- Multi-user support
- Notifications/reminders
- Progress analytics dashboard

## Usage
1. Enter a study goal.
2. Choose difficulty.
3. Click **Create quest**.
4. Complete quest.
5. Generate next quest with selected difficulty.

## Deployment

### VM OS
- Ubuntu 24.04

### What should be installed
- git
- python3
- python3-venv
- python3-pip

### Step-by-step deployment
```bash
git clone https://github.com/VictoriaaaZork/se-toolkit-hackathon.git
cd se-toolkit-hackathon

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# set OPENAI_API_KEY / OPENAI_MODEL / OPENAI_BASE_URL

uvicorn main:app --host 0.0.0.0 --port 8000
