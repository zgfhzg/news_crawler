from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    """개별 뉴스 아이템 데이터 모델"""

    title: str = Field(..., description="뉴스 제목")
    url: str = Field(..., description="뉴스 원문 URL")
    summary: Optional[str] = Field(None, description="뉴스 요약 또는 발췌문")
    content: Optional[str] = Field(None, description="뉴스 본문 전체 내용")
    published_at: Optional[datetime] = Field(None, description="뉴스 게재 시간")
    source: str = Field(..., description="뉴스 출처 (예: naver, rss, yna)")
    category: Optional[str] = Field(None, description="뉴스 카테고리 (예: 정치, 경제, 사회)")
    image_url: Optional[str] = Field(None, description="뉴스 대표 이미지 URL")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NewsListResponse(BaseModel):
    """뉴스 목록 응답 모델"""

    total: int = Field(..., description="수집된 뉴스 총 개수")
    source: Optional[str] = Field(None, description="필터된 뉴스 출처")
    items: list[NewsItem] = Field(..., description="뉴스 아이템 목록")


class CrawlResult(BaseModel):
    """크롤링 결과 메타 정보 모델"""

    source: str = Field(..., description="크롤링한 출처")
    crawled_at: datetime = Field(default_factory=datetime.now, description="크롤링 수행 시간")
    count: int = Field(..., description="수집된 뉴스 개수")
    success: bool = Field(..., description="크롤링 성공 여부")
    error_message: Optional[str] = Field(None, description="실패 시 에러 메시지")

