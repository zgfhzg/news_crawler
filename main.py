from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.news_router import router as news_router
from database.connection import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 DB 테이블 생성"""
    await init_db()
    print("[DB] SQLite 테이블 초기화 완료 (news.db)")
    yield


app = FastAPI(
    title="뉴스 수집 & 요약 API",
    description="한국 주요 언론사 뉴스를 수집하고 요약하는 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(news_router)


@app.get("/", summary="헬스 체크")
async def root():
    return {"status": "ok", "message": "뉴스 크롤러 API가 실행 중입니다."}
