from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class NewsItemORM(Base):
    """뉴스 아이템 ORM 모델 (news_items 테이블)"""

    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False, comment="뉴스 제목")
    url: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False, index=True, comment="뉴스 원문 URL")
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="뉴스 요약 또는 발췌문")
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="뉴스 본문 전체 내용")
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="뉴스 게재 시간")
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="뉴스 출처")
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True, comment="뉴스 카테고리")
    image_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True, comment="뉴스 대표 이미지 URL")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False, comment="DB 저장 시간"
    )

    def __repr__(self) -> str:
        return f"<NewsItemORM id={self.id} source={self.source!r} title={self.title[:30]!r}>"
