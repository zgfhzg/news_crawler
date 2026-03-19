from datetime import datetime
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import AsyncSessionLocal
from database.orm_models import NewsItemORM
from models.news import NewsItem


class NewsRepository:
    """뉴스 아이템 DB CRUD 레포지토리"""

    # ------------------------------------------------------------------ #
    #  내부 헬퍼
    # ------------------------------------------------------------------ #

    @staticmethod
    def _to_orm(item: NewsItem) -> NewsItemORM:
        return NewsItemORM(
            title=item.title,
            url=item.url,
            summary=item.summary,
            content=item.content,
            published_at=item.published_at,
            source=item.source,
            category=item.category,
            image_url=item.image_url,
        )

    @staticmethod
    def _to_pydantic(orm: NewsItemORM) -> NewsItem:
        return NewsItem(
            title=orm.title,
            url=orm.url,
            summary=orm.summary,
            content=orm.content,
            published_at=orm.published_at,
            source=orm.source,
            category=orm.category,
            image_url=orm.image_url,
        )

    # ------------------------------------------------------------------ #
    #  쓰기
    # ------------------------------------------------------------------ #

    async def upsert_many(self, items: list[NewsItem]) -> int:
        """URL 중복 시 업데이트, 신규 시 삽입. 실제 저장된 건수를 반환."""
        if not items:
            return 0

        rows = [
            {
                "title": item.title,
                "url": item.url,
                "summary": item.summary,
                "content": item.content,
                "published_at": item.published_at,
                "source": item.source,
                "category": item.category,
                "image_url": item.image_url,
                "created_at": datetime.now(),
            }
            for item in items
        ]

        async with AsyncSessionLocal() as session:
            async with session.begin():
                stmt = (
                    sqlite_insert(NewsItemORM)
                    .values(rows)
                    .on_conflict_do_update(
                        index_elements=["url"],
                        set_={
                            "title": sqlite_insert(NewsItemORM).excluded.title,
                            "summary": sqlite_insert(NewsItemORM).excluded.summary,
                            "content": sqlite_insert(NewsItemORM).excluded.content,
                            "published_at": sqlite_insert(NewsItemORM).excluded.published_at,
                            "source": sqlite_insert(NewsItemORM).excluded.source,
                            "category": sqlite_insert(NewsItemORM).excluded.category,
                            "image_url": sqlite_insert(NewsItemORM).excluded.image_url,
                        },
                    )
                )
                result = await session.execute(stmt)
                return result.rowcount

    # ------------------------------------------------------------------ #
    #  읽기
    # ------------------------------------------------------------------ #

    async def find_all(
        self,
        source: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[NewsItem]:
        """DB에서 뉴스 조회 (출처·카테고리 필터링, 페이지네이션 지원)"""
        async with AsyncSessionLocal() as session:
            stmt = select(NewsItemORM).order_by(NewsItemORM.published_at.desc().nullslast())

            if source:
                stmt = stmt.where(NewsItemORM.source.ilike(source))
            if category:
                stmt = stmt.where(NewsItemORM.category.ilike(f"%{category}%"))

            stmt = stmt.offset(offset).limit(limit)
            rows = await session.scalars(stmt)
            return [self._to_pydantic(row) for row in rows]

    async def count(
        self,
        source: Optional[str] = None,
        category: Optional[str] = None,
    ) -> int:
        """조건에 맞는 뉴스 총 개수 반환"""
        from sqlalchemy import func

        async with AsyncSessionLocal() as session:
            stmt = select(func.count()).select_from(NewsItemORM)
            if source:
                stmt = stmt.where(NewsItemORM.source.ilike(source))
            if category:
                stmt = stmt.where(NewsItemORM.category.ilike(f"%{category}%"))
            result = await session.scalar(stmt)
            return result or 0

    async def find_by_url(self, url: str) -> Optional[NewsItem]:
        """URL로 단건 조회"""
        async with AsyncSessionLocal() as session:
            row = await session.scalar(
                select(NewsItemORM).where(NewsItemORM.url == url)
            )
            return self._to_pydantic(row) if row else None

    # ------------------------------------------------------------------ #
    #  삭제
    # ------------------------------------------------------------------ #

    async def delete_by_source(self, source: str) -> int:
        """특정 출처의 뉴스를 모두 삭제. 삭제된 건수를 반환."""
        async with AsyncSessionLocal() as session:
            async with session.begin():
                result = await session.execute(
                    delete(NewsItemORM).where(NewsItemORM.source.ilike(source))
                )
                return result.rowcount


# 싱글톤 인스턴스
news_repository = NewsRepository()

