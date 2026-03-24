from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    # Pool sizing para equipos de escasos recursos:
    # - pool_size: conexiones persistentes (bajo para ahorrar RAM)
    # - max_overflow: conexiones temporales extras en picos
    # - pool_recycle: reciclar conexiones cada 30min para evitar leaks
    # - pool_pre_ping: verificar que la conexión está viva antes de usarla
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
