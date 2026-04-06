import os
from datetime import datetime
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = f"sqlite:///{BASE_DIR / 'questforge.db'}"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").strip() or None


class Base(DeclarativeBase):
    pass


class QuestStatus(str, Enum):
    pending = "pending"
    completed = "completed"


class QuestDifficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    quests: Mapped[list["Quest"]] = relationship(
        back_populates="goal", cascade="all, delete-orphan", order_by="Quest.created_at"
    )


class Quest(Base):
    __tablename__ = "quests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    difficulty: Mapped[QuestDifficulty] = mapped_column(
        SAEnum(QuestDifficulty), default=QuestDifficulty.medium, nullable=False
    )
    status: Mapped[QuestStatus] = mapped_column(SAEnum(QuestStatus), default=QuestStatus.pending, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    goal: Mapped[Goal] = relationship(back_populates="quests")


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class StartRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    difficulty: QuestDifficulty = QuestDifficulty.medium


class NextQuestRequest(BaseModel):
    difficulty: QuestDifficulty = QuestDifficulty.medium


class QuestOut(BaseModel):
    id: int
    goal_id: int
    text: str
    difficulty: QuestDifficulty
    status: QuestStatus
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class GoalOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    quests: list[QuestOut]

    class Config:
        from_attributes = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def fallback_quest(goal_title: str, difficulty: QuestDifficulty, step_no: int) -> str:
    templates = {
        QuestDifficulty.easy: "20 минут: повторите ключевые термины по теме '{goal}' и составьте 8 карточек Q/A.",
        QuestDifficulty.medium: "30 минут: решите 3 практические задачи по теме '{goal}', затем 5 минут зафиксируйте ошибки.",
        QuestDifficulty.hard: "40 минут: разберите сложную подтему в '{goal}', решите 2 задачи повышенной сложности и запишите разбор.",
    }
    return f"[{difficulty.value.upper()} #{step_no}] " + templates[difficulty].format(goal=goal_title)


def generate_quest(goal_title: str, difficulty: QuestDifficulty, recent_quests: list[str]) -> str:
    step_no = len(recent_quests) + 1
    if not OPENAI_API_KEY:
        return fallback_quest(goal_title, difficulty, step_no)

    difficulty_rules = {
        QuestDifficulty.easy: "aim for basic understanding and low complexity",
        QuestDifficulty.medium: "aim for moderate difficulty with practical problem-solving",
        QuestDifficulty.hard: "aim for advanced challenge and deeper reasoning",
    }
    avoid_list = "\n".join(f"- {q}" for q in recent_quests[-5:]) or "- None"
    prompt = (
        "Generate exactly ONE practical study task. Return only task text, no extra explanation. "
        "Task duration must be 20-40 minutes and crystal-clear. "
        f"Difficulty: {difficulty.value} ({difficulty_rules[difficulty]}). "
        "Do NOT repeat or closely paraphrase any of these recent quests:\n"
        f"{avoid_list}\n"
        f"Study goal: {goal_title}"
    )

    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    try:
        response = client.responses.create(model=OPENAI_MODEL, input=prompt, temperature=0.7)
        text = (response.output_text or "").strip()
    except Exception:
        try:
            completion = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You create concise study tasks."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
            text = (completion.choices[0].message.content or "").strip()
        except Exception:
            return fallback_quest(goal_title, difficulty, step_no)

    if not text:
        return fallback_quest(goal_title, difficulty, step_no)

    normalized_recent = {q.strip().lower() for q in recent_quests}
    if text.strip().lower() in normalized_recent:
        return fallback_quest(goal_title, difficulty, step_no)

    return text


app = FastAPI(title="QuestForge V2")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/start", response_model=GoalOut)
def start_goal(payload: StartRequest, db: Session = Depends(get_db)):
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")

    goal = Goal(title=title)
    db.add(goal)
    db.flush()

    quest_text = generate_quest(goal.title, payload.difficulty, [])
    quest = Quest(
        goal_id=goal.id,
        text=quest_text,
        difficulty=payload.difficulty,
        status=QuestStatus.pending,
    )
    db.add(quest)
    db.commit()
    db.refresh(goal)
    return goal


@app.get("/api/goals", response_model=list[GoalOut])
def list_goals(db: Session = Depends(get_db)):
    return db.query(Goal).order_by(Goal.created_at.desc()).all()


@app.post("/api/goals/{goal_id}/next-quest", response_model=QuestOut)
def next_quest(goal_id: int, payload: NextQuestRequest, db: Session = Depends(get_db)):
    goal = db.get(Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    recent_quests = [q.text for q in goal.quests]
    quest_text = generate_quest(goal.title, payload.difficulty, recent_quests)
    quest = Quest(
        goal_id=goal.id,
        text=quest_text,
        difficulty=payload.difficulty,
        status=QuestStatus.pending,
    )
    db.add(quest)
    db.commit()
    db.refresh(quest)
    return quest


@app.patch("/api/quests/{quest_id}/complete", response_model=QuestOut)
def complete_quest(quest_id: int, db: Session = Depends(get_db)):
    quest = db.get(Quest, quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    quest.status = QuestStatus.completed
    quest.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(quest)
    return quest
