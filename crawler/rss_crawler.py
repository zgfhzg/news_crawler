from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional

import feedparser
import httpx

from crawler.base import BaseCrawler
from models.news import NewsItem

# 주요 한국 언론사 RSS 피드 목록
DEFAULT_RSS_FEEDS: dict[str, str] = {
    "연합뉴스": "https://www.yna.co.kr/rss/news.xml",
    "KBS": "https://news.kbs.co.kr/rss/rss.do?cId=02",
    "MBC": "https://imnews.imbc.com/rss/news/news_00.xml",
    "SBS": "https://news.sbs.co.kr/news/SBSNewsRSS.do?pmd=F",
    "한겨레": "https://www.hani.co.kr/rss/",
    "조선일보": "https://www.chosun.com/arc/outboundfeeds/rss/",
}


class RSSCrawler(BaseCrawler):
    """RSS 피드 기반 뉴스 크롤러"""

    def __init__(
        self,
        feeds: Optional[dict[str, str]] = None,
        timeout: int = 10,
    ):
        super().__init__(source_name="rss")
        self.feeds = feeds or DEFAULT_RSS_FEEDS
        self.timeout = timeout

    async def fetch(self) -> list[NewsItem]:
        """등록된 모든 RSS 피드에서 뉴스를 수집"""
        all_items: list[NewsItem] = []

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for source, url in self.feeds.items():
                items = await self._fetch_feed(client, source, url)
                all_items.extend(items)

        # 게재 시간 기준 최신순 정렬 (timezone 정보 제거 후 비교)
        def sort_key(item):
            dt = item.published_at or datetime.min
            # timezone-aware → naive UTC로 변환
            if dt.tzinfo is not None:
                from datetime import timezone
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt

        all_items.sort(key=sort_key, reverse=True)
        return all_items

    async def _fetch_feed(
        self, client: httpx.AsyncClient, source: str, url: str
    ) -> list[NewsItem]:
        """단일 RSS 피드 URL에서 뉴스 아이템 파싱"""
        try:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            feed = feedparser.parse(response.text)

            items: list[NewsItem] = []
            for entry in feed.entries:
                item = self._parse_entry(entry, source)
                if item:
                    items.append(item)

            print(f"[RSS] {source}: {len(items)}건 수집")
            return items

        except Exception as e:
            print(f"[RSS] {source} 피드 수집 실패 ({url}): {e}")
            return []

    @staticmethod
    def _parse_entry(entry, source: str) -> Optional[NewsItem]:
        """feedparser entry 객체를 NewsItem으로 변환"""
        title = getattr(entry, "title", None)
        link = getattr(entry, "link", None)

        if not title or not link:
            return None

        # 게재 시간 파싱
        published_at = None
        if hasattr(entry, "published"):
            try:
                published_at = parsedate_to_datetime(entry.published)
            except Exception:
                pass

        # 요약문 추출
        summary = None
        if hasattr(entry, "summary"):
            summary = entry.summary[:300] if entry.summary else None

        return NewsItem(
            title=title.strip(),
            url=link.strip(),
            summary=summary,
            published_at=published_at,
            source=source,
        )

