import csv
from datetime import datetime
import os
import json
from collections import Counter

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from sqlmodel import Field, Session, SQLModel, create_engine, select

# 환경 변수 로드 (로컬 테스트용)
load_dotenv()

app = FastAPI()

# 경로 설정 (Vercel 배포 환경 대응)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(CURRENT_DIR, "templates"))

# questions.json 로드
json_path = os.path.join(CURRENT_DIR, "questions.json")
with open(json_path, "r", encoding="utf-8") as f:
    questions = json.load(f)["questions"]

# 1. 데이터베이스 모델 정의
class UserResult(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_name: str
    phone_number: str
    persona: str
    traits: str
    created_at: datetime = Field(default_factory=datetime.now)

# 2. 엔진 설정
postgres_url = os.getenv("POSTGRES_URL")

if postgres_url:
    # postgres:// -> postgresql:// 변경 (SQLAlchemy 호환성)
    if postgres_url.startswith("postgres://"):
        postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)
    
    # 파라미터 정제
    if "&supa=" in postgres_url:
        postgres_url = postgres_url.split("&supa=")[0]
    elif "?supa=" in postgres_url:
        postgres_url = postgres_url.split("?supa=")[0]

# DB 엔진 생성
engine = create_engine(postgres_url) if postgres_url else None

def create_db_and_tables():
    if engine:
        SQLModel.metadata.create_all(engine)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # 수정: request=request를 별도 인자로 전달
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/question/{q_id}", response_class=HTMLResponse)
async def get_question(
    request: Request, 
    q_id: int, 
    accumulated_traits: str = Form(default="")
):
    if q_id > 10:
        return templates.TemplateResponse(
            request=request, 
            name="contact.html", 
            context={"accumulated_traits": accumulated_traits}
        )
    
    question = next((q for q in questions if q["id"] == q_id), None)
    return templates.TemplateResponse(
        request=request, 
        name="question.html", 
        context={
            "question": question, 
            "next_id": q_id + 1, 
            "accumulated_traits": accumulated_traits
        }
    )

@app.post("/result", response_class=HTMLResponse)
async def calculate_result(
    request: Request, 
    user_name: str = Form(...), 
    phone_number: str = Form(...), 
    accumulated_traits: str = Form(...)
):
    traits_list = [t.strip() for t in accumulated_traits.split(",") if t.strip()]
    most_common_trait = Counter(traits_list).most_common(1)[0][0] if traits_list else "Acoustic"
    
    if any(kw in most_common_trait for kw in ["Lo-fi", "Ambient", "Minimal", "Calm"]):
        persona = "방 안의 작은 섬, 새벽 2시의 로파이(Lo-fi)"
        message = "세상과의 연결을 잠시 늦추고, 오롯이 나만의 주파수에 집중하는 시간입니다. 조용히 당신의 빈 방을 채워줄 몽환적인 플레이리스트를 준비했어요."
        playlist = [
            {"artist": "새소년 (SE SO NEON)", "title": "파도"},
            {"artist": "mellodaze", "title": "elation station"},
            {"artist": "Jinsang", "title": "Bliss"}
        ]
        
    elif any(kw in most_common_trait for kw in ["City Pop", "Dream Pop", "R&B", "Soul", "Relaxed"]):
        persona = "낭만을 잃지 않는 관찰자, 해 질 녘의 시티팝(City Pop)"
        message = "일상을 영화로 만들고 싶은 기분 좋은 공허함, 세련된 낭만을 더해줄 음악을 건넵니다. 복잡한 머릿속을 기분 좋게 환기해 줄 거예요."
        playlist = [
            {"artist": "유키카 (YUKIKA)", "title": "네온 (NEON)"},
            {"artist": "녹두", "title": "Say My Name"},
            {"artist": "키키", "title": "To Me From Me"}
        ]
        
    elif any(kw in most_common_trait for kw in ["Acoustic", "Indie", "Folk", "Warm", "Safe"]):
        persona = "작지만 단단한 세계, 오후 3시의 어쿠스틱(Acoustic)"
        message = "거창하지 않아도 괜찮아요. 당신의 담백하고 다정한 일상을 조용히 응원하는 따뜻한 선율을 들어보세요."
        playlist = [
            {"artist": "너드커넥션", "title": "그대만 있다면"},
            {"artist": "겸 (GYE0M)", "title": "단춘"},
            {"artist": "리도어 (Redoor)", "title": "영원은 그렇듯"}
        ]
        
    elif any(kw in most_common_trait for kw in ["Rock", "Synthwave", "EDM", "Dance", "Punk", "Alternative", "Intense", "Energetic"]):
        persona = "엑셀을 밟고 싶은 밤, 자정의 하이웨이 록(Rock/Synthwave)"
        message = "가슴속에 뜨거운 엔진을 품고 계시네요! 답답한 현실의 창문을 열고 시원하게 달려 나갈 수 있는 강렬한 비트를 처방해 드립니다."
        playlist = [
            {"artist": "한로로", "title": "사랑하게 될 거야"},
            {"artist": "김민석 (멜로망스)", "title": "사랑의 언어 (Love Language)"},
            {"artist": "QWER", "title": "눈물참기"}
        ]
        
    elif any(kw in most_common_trait for kw in ["Jazz", "Groove", "Chill", "Elegant", "Melancholic"]):
        persona = "나만의 속도를 걷는 유목민, 비 오는 날의 재즈(Jazz)"
        message = "정해진 박자에 얽매일 필요 없죠. 예측 불가능해서 더 매력적인 당신의 인생처럼, 자유롭고 유연한 재즈 선율을 선물합니다."
        playlist = [
            {"artist": "Wang OK", "title": "Before spring ends"},
            {"artist": "Paul", "title": "Sleeping Beauty(하트시그널 삽입곡)"},
            {"artist": "선우정아", "title": "고양이 (Feat. 아이유)"}
        ]
        
    else: 
        persona = "다음 챕터를 준비하는 주인공, 영화 같은 웅장함(Cinematic OST)"
        message = "당신 인생의 새로운 시즌이 막 시작되려 하네요. 이 거대한 전환점의 오프닝을 화려하게 장식해 줄 벅찬 멜로디를 들어보세요."
        playlist = [
            {"artist": "웬디 (WENDY)", "title": "Daydream (이 사랑 통역 되나요? OST)"},
            {"artist": "Don Toliver", "title": "Lose My Mind (F1 OST)"},
            {"artist": "HUNTR/X", "title": "Golden"}
        ]
        
    # DB 저장
    if engine:
        new_user = UserResult(
            user_name=user_name, 
            phone_number=phone_number, 
            persona=persona, 
            traits=accumulated_traits
        )
        with Session(engine) as session:
            session.add(new_user)
            session.commit()

    return templates.TemplateResponse(
        request=request, 
        name="result.html", 
        context={
            "persona": persona, 
            "message": message, 
            "user_name": user_name, 
            "phone_number": phone_number, 
            "playlist": playlist
        }
    )

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    if not engine:
        return "Database not configured."
        
    with Session(engine) as session:
        statement = select(UserResult).order_by(UserResult.id.desc())
        users = session.exec(statement).all()

    return templates.TemplateResponse(
        request=request, 
        name="admin.html", 
        context={"users": users}
    )