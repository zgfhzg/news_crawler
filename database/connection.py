from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# SQLite DB 파일 경로 (프로젝트 루트에 news.db 생성)
DATABASE_URL = "sqlite+aiosqlite:///./news.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,           # SQL 쿼리 로그 출력 여부
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """모든 ORM 모델의 기반 클래스"""
    pass


async def init_db() -> None:
    """앱 시작 시 테이블 생성"""
    # models 모듈을 임포트해야 Base.metadata에 테이블이 등록됨
    from database.orm_models import NewsItemORM  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

