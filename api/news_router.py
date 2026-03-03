from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from models.news import NewsListResponse, CrawlResult
from services.news_service import news_service

router = APIRouter(prefix="/news", tags=["뉴스"])


@router.get("", response_model=NewsListResponse, summary="뉴스 목록 조회")
async def get_news(
    source: Optional[str] = Query(None, description="출처 필터 (예: naver, 연합뉴스)"),
    category: Optional[str] = Query(None, description="카테고리 필터 (예: 정치, 경제)"),
    limit: int = Query(50, ge=1, le=200, description="반환할 최대 뉴스 개수"),
):
    """캐시된 뉴스 목록을 반환합니다. 크롤링이 필요하면 /news/refresh를 먼저 호출하세요."""
    items = news_service.get_news(source=source, category=category, limit=limit)
    return NewsListResponse(total=len(items), source=source, items=items)


@router.post("/refresh", response_model=list[CrawlResult], summary="뉴스 수집 (크롤링 실행)")
async def refresh_news():
    """모든 크롤러를 실행하여 최신 뉴스를 수집합니다."""
    results = await news_service.crawl_all()
    if not any(r.success for r in results):
        raise HTTPException(status_code=500, detail="모든 크롤러 실패")
    return results


@router.get("/status", summary="크롤링 상태 조회")
async def get_status():
    """마지막 크롤링 시간 및 캐시 현황을 반환합니다."""
    return {
        "last_crawled_at": news_service.last_crawled_at,
        "cached_count": len(news_service.cached_news),
    }

