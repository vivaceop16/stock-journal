"""데이터베이스 연결 관리"""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base

# Streamlit secrets에서 데이터베이스 URL 가져오기
def get_database_url():
    # Streamlit Cloud 환경
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'DATABASE_URL' in st.secrets:
            return st.secrets['DATABASE_URL']
    except:
        pass

    # 환경 변수 또는 기본값 (로컬 개발용)
    return os.environ.get('DATABASE_URL', 'sqlite:///./data/trading_journal.db')

DB_PATH = get_database_url()


def get_engine():
    """SQLAlchemy 엔진 생성"""
    db_url = get_database_url()
    connect_args = {}

    if 'sqlite' in db_url:
        connect_args = {"check_same_thread": False}

    return create_engine(
        db_url,
        connect_args=connect_args,
        echo=False,
        pool_pre_ping=True  # 연결 상태 확인
    )


def init_db():
    """데이터베이스 초기화 (테이블 생성)"""
    db_url = get_database_url()

    # SQLite인 경우에만 data 디렉토리 생성
    if 'sqlite' in db_url:
        os.makedirs('./data', exist_ok=True)

    engine = get_engine()
    # PostgreSQL(Supabase)은 테이블이 이미 생성되어 있음
    if 'sqlite' in db_url:
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
