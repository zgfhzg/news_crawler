from datetime import datetime
from typing import Optional

from crawler.base import BaseCrawler
from crawler.rss_crawler import RSSCrawler
from crawler.naver_crawler import NaverNewsCrawler
from database.repository import news_repository
from models.news import NewsItem, CrawlResult


class NewsService:
    """뉴스 수집 및 관리 서비스"""

    def __init__(self):
        self._cache: list[NewsItem] = []
        self._last_crawled_at: Optional[datetime] = None

        # 기본 크롤러 등록
        self._crawlers: list[BaseCrawler] = [
            RSSCrawler(),
            NaverNewsCrawler(max_pages=1),
        ]

    @property
    def cached_news(self) -> list[NewsItem]:
        return self._cache

    @property
    def last_crawled_at(self) -> Optional[datetime]:
        return self._last_crawled_at

    async def crawl_all(self) -> list[CrawlResult]:
        """등록된 모든 크롤러를 실행하고 결과를 캐시에 저장"""
        results: list[CrawlResult] = []
        new_items: list[NewsItem] = []

        for crawler in self._crawlers:
            try:
                items = await crawler.fetch_safe()
                new_items.extend(items)
                results.append(
                    CrawlResult(
                        source=crawler.source_name,
                        count=len(items),
                        success=True,
                    )
                )
            except Exception as e:
                results.append(
                    CrawlResult(
                        source=crawler.source_name,
                        count=0,
                        success=False,
                        error_message=str(e),
                    )
                )

        # 중복 URL 제거 후 캐시 업데이트
        self._cache = self._deduplicate(new_items)
        self._last_crawled_at = datetime.now()

        # DB에 저장 (중복 URL은 upsert로 처리)
        saved_count = await news_repository.upsert_many(self._cache)
        print(f"[NewsService] DB 저장 완료: {saved_count}건")

        return results

    async def get_news(
        self,
        source: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[NewsItem]:
        """DB에서 뉴스 조회 (출처/카테고리 필터링, 페이지네이션 지원)"""
        return await news_repository.find_all(
            source=source,
            category=category,
            limit=limit,
            offset=offset,
        )

    async def count_news(
        self,
        source: Optional[str] = None,
        category: Optional[str] = None,
    ) -> int:
        """DB에서 뉴스 총 개수 조회"""
        return await news_repository.count(source=source, category=category)

    @staticmethod
    def _deduplicate(items: list[NewsItem]) -> list[NewsItem]:
        """URL 기준 중복 뉴스 제거"""
        seen_urls: set[str] = set()
        unique_items: list[NewsItem] = []
        for item in items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique_items.append(item)
        return unique_items


# 싱글톤 인스턴스
news_service = NewsService()

