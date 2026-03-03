from abc import ABC, abstractmethod
from models.news import NewsItem


class BaseCrawler(ABC):
    """모든 뉴스 크롤러의 추상 기반 클래스"""

    def __init__(self, source_name: str):
        self.source_name = source_name

    @abstractmethod
    async def fetch(self) -> list[NewsItem]:
        """뉴스 목록을 수집하여 반환하는 추상 메서드"""
        pass

    async def fetch_safe(self) -> list[NewsItem]:
        """예외 처리를 포함한 안전한 fetch 래퍼"""
        try:
            return await self.fetch()
        except Exception as e:
            print(f"[{self.source_name}] 크롤링 실패: {e}")
            return []

