"""SQLAlchemy 모델 정의"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime,
    Numeric, ForeignKey, JSON, CheckConstraint, Index, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, Session
from sqlalchemy.sql import func

Base = declarative_base()


class Trade(Base):
    """매매 기록 모델"""
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 기본 정보
    stock_name = Column(String(100), nullable=False)
    stock_code = Column(String(20))
    trade_date = Column(Date, nullable=False)
    trade_type = Column(String(10), nullable=False)  # 'BUY' or 'SELL'

    # 거래 상세
    price = Column(Numeric(15, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Numeric(15, 2))

    # 매매 근거
    trade_reason = Column(Text, nullable=False)
    confidence_score = Column(Integer)  # 1-10

    # 연결 정보
    linked_trade_id = Column(Integer, ForeignKey('trades.id'))

    # 수익 정보 (매도시)
    profit_loss = Column(Numeric(15, 2))
    profit_rate = Column(Numeric(8, 4))

    # 메타데이터
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 관계
    linked_trade = relationship('Trade', remote_side=[id], backref='sell_trades')
    analysis_results = relationship('AnalysisResult', back_populates='trade', cascade='all, delete-orphan')

    __table_args__ = (
        CheckConstraint("trade_type IN ('BUY', 'SELL')", name='check_trade_type'),
        CheckConstraint('confidence_score >= 1 AND confidence_score <= 10', name='check_confidence'),
        Index('idx_trades_date', 'trade_date'),
        Index('idx_trades_stock', 'stock_name'),
        Index('idx_trades_type', 'trade_type'),
    )

    def __repr__(self):
        return f"<Trade(id={self.id}, stock={self.stock_name}, type={self.trade_type}, date={self.trade_date})>"

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'stock_name': self.stock_name,
            'stock_code': self.stock_code,
            'trade_date': self.trade_date.isoformat() if self.trade_date else None,
            'trade_type': self.trade_type,
            'price': float(self.price) if self.price else None,
            'quantity': self.quantity,
            'total_amount': float(self.total_amount) if self.total_amount else None,
            'trade_reason': self.trade_reason,
            'confidence_score': self.confidence_score,
            'linked_trade_id': self.linked_trade_id,
            'profit_loss': float(self.profit_loss) if self.profit_loss else None,
            'profit_rate': float(self.profit_rate) if self.profit_rate else None,
        }


class AnalysisResult(Base):
    """AI 분석 결과 모델"""
    __tablename__ = 'analysis_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(Integer, ForeignKey('trades.id', ondelete='CASCADE'), nullable=False)

    # AI 평가 점수
    total_score = Column(Integer)  # 0-100
    logic_score = Column(Integer)  # 0-40
    timing_score = Column(Integer)  # 0-30
    risk_management_score = Column(Integer)  # 0-20
    confidence_accuracy_score = Column(Integer)  # 0-10

    # 분석 내용
    ai_feedback = Column(Text)
    extracted_keywords = Column(JSON)
    market_context = Column(Text)

    # 패턴 분류
    trade_pattern = Column(String(50))
    weakness_category = Column(String(100))

    created_at = Column(DateTime, default=func.now())

    # 관계
    trade = relationship('Trade', back_populates='analysis_results')

    __table_args__ = (
        CheckConstraint('total_score >= 0 AND total_score <= 100', name='check_total_score'),
        Index('idx_analysis_trade', 'trade_id'),
    )

    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, trade_id={self.trade_id}, score={self.total_score})>"

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'trade_id': self.trade_id,
            'total_score': self.total_score,
            'logic_score': self.logic_score,
            'timing_score': self.timing_score,
            'risk_management_score': self.risk_management_score,
            'confidence_accuracy_score': self.confidence_accuracy_score,
            'ai_feedback': self.ai_feedback,
            'extracted_keywords': self.extracted_keywords,
            'market_context': self.market_context,
            'trade_pattern': self.trade_pattern,
            'weakness_category': self.weakness_category,
        }


class LearningTask(Base):
    """학습 과제 모델"""
    __tablename__ = 'learning_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 과제 정보
    task_title = Column(String(200), nullable=False)
    task_description = Column(Text)
    task_category = Column(String(50))  # 기술분석, 심리, 리스크관리 등
    priority = Column(Integer, default=1)  # 1-5

    # 연관 정보
    related_pattern = Column(String(50))
    trigger_analysis_ids = Column(JSON)

    # 상태
    status = Column(String(20), default='pending')  # pending, in_progress, completed
    completion_date = Column(Date)

    # 메타데이터
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('priority >= 1 AND priority <= 5', name='check_priority'),
        CheckConstraint("status IN ('pending', 'in_progress', 'completed')", name='check_status'),
        Index('idx_learning_status', 'status'),
    )

    def __repr__(self):
        return f"<LearningTask(id={self.id}, title={self.task_title}, status={self.status})>"

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'task_title': self.task_title,
            'task_description': self.task_description,
            'task_category': self.task_category,
            'priority': self.priority,
            'related_pattern': self.related_pattern,
            'status': self.status,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
        }


class MonthlyReport(Base):
    """월간 리포트 모델"""
    __tablename__ = 'monthly_reports'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 기간
    report_month = Column(Date, nullable=False, unique=True)

    # 기본 통계
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    win_rate = Column(Numeric(5, 2))

    # 손익 통계
    total_profit_loss = Column(Numeric(15, 2))
    average_profit = Column(Numeric(15, 2))
    average_loss = Column(Numeric(15, 2))
    profit_loss_ratio = Column(Numeric(8, 4))
    max_profit = Column(Numeric(15, 2))
    max_loss = Column(Numeric(15, 2))

    # 분석 결과
    best_trade_pattern = Column(String(50))
    worst_trade_pattern = Column(String(50))
    average_score = Column(Numeric(5, 2))

    # 상세 데이터
    pattern_analysis = Column(JSON)
    keyword_summary = Column(JSON)
    improvement_suggestions = Column(JSON)

    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index('idx_reports_month', 'report_month'),
    )

    def __repr__(self):
        return f"<MonthlyReport(id={self.id}, month={self.report_month})>"

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'report_month': self.report_month.isoformat() if self.report_month else None,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': float(self.win_rate) if self.win_rate else None,
            'total_profit_loss': float(self.total_profit_loss) if self.total_profit_loss else None,
            'profit_loss_ratio': float(self.profit_loss_ratio) if self.profit_loss_ratio else None,
            'best_trade_pattern': self.best_trade_pattern,
            'worst_trade_pattern': self.worst_trade_pattern,
            'average_score': float(self.average_score) if self.average_score else None,
        }
