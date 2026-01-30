"""데이터베이스 연결 관리"""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base

# 데이터베이스 경로
DB_PATH = os.environ.get('DATABASE_URL', 'sqlite:///./data/trading_journal.db')


def get_engine():
    """SQLAlchemy 엔진 생성"""
    return create_engine(
        DB_PATH,
        connect_args={"check_same_thread": False} if 'sqlite' in DB_PATH else {},
        echo=False
    )


def init_db():
    """데이터베이스 초기화 (테이블 생성)"""
    # data 디렉토리 생성
    os.makedirs('./data', exist_ok=True)

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    return engine


def get_session_factory():
    """세션 팩토리 생성"""
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session():
    """데이터베이스 세션 컨텍스트 매니저"""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


class DatabaseManager:
    """데이터베이스 매니저 클래스"""

    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self):
        """데이터베이스 초기화"""
        if self._engine is None:
            self._engine = init_db()
            self._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine
            )

    def get_session(self) -> Session:
        """새 세션 반환"""
        if self._session_factory is None:
            self.initialize()
        return self._session_factory()

    @contextmanager
    def session_scope(self):
        """세션 스코프 컨텍스트 매니저"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()
