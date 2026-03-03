from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from crawler.base import BaseCrawler
from models.news import NewsItem

NAVER_NEWS_CATEGORIES: dict[str, str] = {
    "정치": "100",
    "경제": "101",
    "사회": "102",
    "생활문화": "103",
    "세계": "104",
    "IT과학": "105",
}

NAVER_NEWS_URL = "https://news.naver.com/main/list.naver"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


class NaverNewsCrawler(BaseCrawler):
    """네이버 뉴스 크롤러 (HTML 스크래핑)"""

    def __init__(
        self,
        categories: Optional[list[str]] = None,
        max_pages: int = 1,
        timeout: int = 10,
    ):
        super().__init__(source_name="naver")
        # 카테고리 미지정 시 전체 카테고리 수집
        self.target_categories = categories or list(NAVER_NEWS_CATEGORIES.keys())
        self.max_pages = max_pages
        self.timeout = timeout

    async def fetch(self) -> list[NewsItem]:
        """지정된 카테고리에서 네이버 뉴스 수집"""
        all_items: list[NewsItem] = []

        async with httpx.AsyncClient(headers=HEADERS, timeout=self.timeout) as client:
            for category_name in self.target_categories:
                category_id = NAVER_NEWS_CATEGORIES.get(category_name)
                if not category_id:
                    continue
                for page in range(1, self.max_pages + 1):
                    items = await self._fetch_page(client, category_name, category_id, page)
                    all_items.extend(items)

        return all_items

    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        category_name: str,
        category_id: str,
        page: int,
    ) -> list[NewsItem]:
        """네이버 뉴스 카테고리 페이지 스크래핑"""
        params = {"sid1": category_id, "page": page}
        try:
            response = await client.get(NAVER_NEWS_URL, params=params, follow_redirects=True)
            response.raise_for_status()
            items = self._parse_news_list(response.text, category_name)
            print(f"[Naver] {category_name} {page}페이지: {len(items)}건 수집")
            return items

        except Exception as e:
            print(f"[Naver] {category_name} {page}페이지 수집 실패: {e}")
            return []

    @staticmethod
    def _parse_news_list(html: str, category: str) -> list[NewsItem]:
        """HTML에서 뉴스 목록 파싱"""
        soup = BeautifulSoup(html, "html.parser")
        items: list[NewsItem] = []

        # 네이버 뉴스 목록 영역
        list_body = soup.select_one("ul.type06_headline") or soup.select_one("ul.type06")
        if not list_body:
            return items

        for li in list_body.find_all("li"):
            dl = li.find("dl")
            if not dl:
                continue

            # 제목 및 URL
            title_tag = dl.find("dt", class_=lambda c: c != "photo" if c else True)
            a_tag = title_tag.find("a") if title_tag else None
            if not a_tag:
                continue

            title = a_tag.get_text(strip=True)
            url = a_tag.get("href", "")
            if not title or not url:
                continue

            # 요약문
            summary_tag = dl.find("dd", class_="txt_useless")
            summary = summary_tag.get_text(strip=True)[:300] if summary_tag else None

            items.append(
                NewsItem(
                    title=title,
                    url=url,
                    summary=summary,
                    published_at=datetime.now(),  # 정확한 시간은 상세 페이지에서 추출 가능
                    source="naver",
                    category=category,
                )
            )

        return items

