from fastapi import FastAPI
from api.news_router import router as news_router

app = FastAPI(
    title="뉴스 수집 & 요약 API",
    description="한국 주요 언론사 뉴스를 수집하고 요약하는 API",
    version="0.1.0",
)

app.include_router(news_router)


@app.get("/", summary="헬스 체크")
async def root():
    return {"status": "ok", "message": "뉴스 크롤러 API가 실행 중입니다."}
