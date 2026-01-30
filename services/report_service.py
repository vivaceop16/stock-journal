"""리포트 서비스"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal
from collections import Counter, defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from database.models import Trade, AnalysisResult, MonthlyReport
from database.connection import db_manager


class ReportService:
    """월간 리포트 생성 서비스"""

    def __init__(self, session: Optional[Session] = None):
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            return db_manager.get_session()
        return self._session

    def generate_monthly_report(self, year: int, month: int) -> MonthlyReport:
        """월간 리포트 생성"""
        # 기간 설정
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        # 해당 월의 완료된 매도 거래 조회
        completed_sells = self.session.query(Trade).filter(
            and_(
                Trade.trade_type == 'SELL',
                Trade.linked_trade_id.isnot(None),
                Trade.trade_date >= start_date,
                Trade.trade_date < end_date
            )
        ).all()

        # 통계 계산
        stats = self._calculate_statistics(completed_sells)

        # 패턴 분석
        pattern_analysis = self._analyze_patterns(completed_sells)

        # 키워드 요약
        keyword_summary = self._summarize_keywords(completed_sells)

        # 개선 제안 생성
        improvement_suggestions = self._generate_suggestions(stats, pattern_analysis)

        # 기존 리포트 확인 (있으면 업데이트)
        report_month = date(year, month, 1)
        existing_report = self.session.query(MonthlyReport).filter(
            MonthlyReport.report_month == report_month
        ).first()

        if existing_report:
            report = existing_report
        else:
            report = MonthlyReport(report_month=report_month)
            self.session.add(report)

        # 리포트 데이터 설정
        report.total_trades = stats['total_trades']
        report.winning_trades = stats['winning_trades']
        report.losing_trades = stats['losing_trades']
        report.win_rate = stats['win_rate']
        report.total_profit_loss = stats['total_profit_loss']
        report.average_profit = stats['average_profit']
        report.average_loss = stats['average_loss']
        report.profit_loss_ratio = stats['profit_loss_ratio']
        report.max_profit = stats['max_profit']
        report.max_loss = stats['max_loss']
        report.best_trade_pattern = pattern_analysis.get('best_pattern')
        report.worst_trade_pattern = pattern_analysis.get('worst_pattern')
        report.average_score = stats['average_score']
        report.pattern_analysis = pattern_analysis
        report.keyword_summary = keyword_summary
        report.improvement_suggestions = improvement_suggestions

        self.session.commit()
        self.session.refresh(report)
        return report

    def _calculate_statistics(self, trades: List[Trade]) -> Dict[str, Any]:
        """매매 통계 계산"""
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': Decimal('0'),
                'total_profit_loss': Decimal('0'),
                'average_profit': Decimal('0'),
                'average_loss': Decimal('0'),
                'profit_loss_ratio': Decimal('0'),
                'max_profit': Decimal('0'),
                'max_loss': Decimal('0'),
                'average_score': Decimal('0')
            }

        total = len(trades)
        profits = [t.profit_loss for t in trades if t.profit_loss and t.profit_loss > 0]
        losses = [t.profit_loss for t in trades if t.profit_loss and t.profit_loss < 0]

        winning = len(profits)
        losing = len(losses)

        total_profit_loss = sum(t.profit_loss or Decimal('0') for t in trades)
        average_profit = sum(profits) / len(profits) if profits else Decimal('0')
        average_loss = sum(losses) / len(losses) if losses else Decimal('0')

        # 손익비 계산 (평균 수익 / 평균 손실의 절대값)
        if average_loss != 0:
            profit_loss_ratio = abs(average_profit / average_loss)
        else:
            profit_loss_ratio = Decimal('0')

        # 최대 수익/손실
        max_profit = max(profits) if profits else Decimal('0')
        max_loss = min(losses) if losses else Decimal('0')

        # 평균 AI 점수
        trade_ids = [t.id for t in trades]
        analyses = self.session.query(AnalysisResult).filter(
            AnalysisResult.trade_id.in_(trade_ids)
        ).all()
        scores = [a.total_score for a in analyses if a.total_score]
        average_score = sum(scores) / len(scores) if scores else Decimal('0')

        return {
            'total_trades': total,
            'winning_trades': winning,
            'losing_trades': losing,
            'win_rate': Decimal(str(winning / total * 100)) if total > 0 else Decimal('0'),
            'total_profit_loss': total_profit_loss,
            'average_profit': average_profit,
            'average_loss': average_loss,
            'profit_loss_ratio': profit_loss_ratio,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'average_score': Decimal(str(average_score))
        }

    def _analyze_patterns(self, trades: List[Trade]) -> Dict[str, Any]:
        """패턴별 성과 분석"""
        if not trades:
            return {}

        trade_ids = [t.id for t in trades]
        analyses = self.session.query(AnalysisResult).filter(
            AnalysisResult.trade_id.in_(trade_ids)
        ).all()

        # 패턴별 데이터 집계
        pattern_data = defaultdict(lambda: {'trades': [], 'profits': []})

        analysis_map = {a.trade_id: a for a in analyses}
        for trade in trades:
            analysis = analysis_map.get(trade.id)
            pattern = analysis.trade_pattern if analysis else '미분류'
            pattern_data[pattern]['trades'].append(trade)
            if trade.profit_loss:
                pattern_data[pattern]['profits'].append(float(trade.profit_loss))

        # 패턴별 통계
        pattern_stats = {}
        for pattern, data in pattern_data.items():
            profits = data['profits']
            pattern_stats[pattern] = {
                'count': len(data['trades']),
                'total_profit': sum(profits),
                'average_profit': sum(profits) / len(profits) if profits else 0,
                'win_rate': len([p for p in profits if p > 0]) / len(profits) * 100 if profits else 0
            }

        # 최고/최저 패턴 찾기
        best_pattern = max(pattern_stats.items(), key=lambda x: x[1]['total_profit'])[0] if pattern_stats else None
        worst_pattern = min(pattern_stats.items(), key=lambda x: x[1]['total_profit'])[0] if pattern_stats else None

        return {
            'pattern_stats': pattern_stats,
            'best_pattern': best_pattern,
            'worst_pattern': worst_pattern
        }

    def _summarize_keywords(self, trades: List[Trade]) -> Dict[str, Any]:
        """키워드 요약"""
        trade_ids = [t.id for t in trades]
        analyses = self.session.query(AnalysisResult).filter(
            AnalysisResult.trade_id.in_(trade_ids)
        ).all()

        # 전체 키워드 집계
        all_keywords = Counter()
        winning_keywords = Counter()
        losing_keywords = Counter()

        analysis_map = {a.trade_id: a for a in analyses}
        for trade in trades:
            analysis = analysis_map.get(trade.id)
            if not analysis or not analysis.extracted_keywords:
                continue

            keywords = analysis.extracted_keywords
            for category, kw_list in keywords.items():
                for kw in kw_list:
                    all_keywords[kw] += 1
                    if trade.profit_loss and trade.profit_loss > 0:
                        winning_keywords[kw] += 1
                    elif trade.profit_loss and trade.profit_loss < 0:
                        losing_keywords[kw] += 1

        return {
            'top_keywords': dict(all_keywords.most_common(10)),
            'winning_keywords': dict(winning_keywords.most_common(5)),
            'losing_keywords': dict(losing_keywords.most_common(5))
        }

    def _generate_suggestions(
        self,
        stats: Dict[str, Any],
        pattern_analysis: Dict[str, Any]
    ) -> List[str]:
        """개선 제안 생성"""
        suggestions = []

        # 승률 기반 제안
        win_rate = float(stats.get('win_rate', 0))
        if win_rate < 40:
            suggestions.append("승률이 낮습니다. 진입 조건을 더 엄격하게 설정해보세요.")
        elif win_rate > 60:
            suggestions.append("승률이 양호합니다. 현재 전략을 유지하세요.")

        # 손익비 기반 제안
        pl_ratio = float(stats.get('profit_loss_ratio', 0))
        if pl_ratio < 1:
            suggestions.append("손익비가 1 미만입니다. 손절을 더 빨리 하거나 익절을 늘려보세요.")
        elif pl_ratio > 2:
            suggestions.append("손익비가 우수합니다. 리스크 관리가 잘 되고 있습니다.")

        # 패턴 기반 제안
        pattern_stats = pattern_analysis.get('pattern_stats', {})
        worst_pattern = pattern_analysis.get('worst_pattern')
        if worst_pattern and pattern_stats.get(worst_pattern, {}).get('total_profit', 0) < 0:
            suggestions.append(f"'{worst_pattern}' 패턴의 성과가 저조합니다. 이 유형의 매매를 줄여보세요.")

        # 거래 횟수 기반 제안
        total_trades = stats.get('total_trades', 0)
        if total_trades > 20:
            suggestions.append("거래 횟수가 많습니다. 더 신중하게 기회를 선별해보세요.")
        elif total_trades < 5:
            suggestions.append("거래 데이터가 적어 정확한 분석이 어렵습니다.")

        return suggestions if suggestions else ["현재 성과가 양호합니다. 꾸준히 기록을 이어가세요."]

    def get_report(self, year: int, month: int) -> Optional[MonthlyReport]:
        """특정 월 리포트 조회"""
        report_month = date(year, month, 1)
        return self.session.query(MonthlyReport).filter(
            MonthlyReport.report_month == report_month
        ).first()

    def get_recent_reports(self, limit: int = 6) -> List[MonthlyReport]:
        """최근 리포트 조회"""
        return self.session.query(MonthlyReport).order_by(
            MonthlyReport.report_month.desc()
        ).limit(limit).all()

    def get_dashboard_data(self, report: MonthlyReport) -> Dict[str, Any]:
        """대시보드용 데이터 생성"""
        return {
            'summary': {
                'period': report.report_month.strftime('%Y년 %m월'),
                'total_trades': report.total_trades or 0,
                'win_rate': float(report.win_rate or 0),
                'profit_loss_ratio': float(report.profit_loss_ratio or 0),
                'total_profit_loss': float(report.total_profit_loss or 0),
                'average_score': float(report.average_score or 0)
            },
            'breakdown': {
                'winning_trades': report.winning_trades or 0,
                'losing_trades': report.losing_trades or 0,
                'average_profit': float(report.average_profit or 0),
                'average_loss': float(report.average_loss or 0),
                'max_profit': float(report.max_profit or 0),
                'max_loss': float(report.max_loss or 0)
            },
            'patterns': {
                'best': report.best_trade_pattern,
                'worst': report.worst_trade_pattern,
                'analysis': report.pattern_analysis or {}
            },
            'keywords': report.keyword_summary or {},
            'suggestions': report.improvement_suggestions or []
        }

    def get_trend_data(self, months: int = 6) -> List[Dict[str, Any]]:
        """월별 추이 데이터"""
        reports = self.get_recent_reports(months)

        trend = []
        for report in reversed(reports):  # 오래된 순서로
            trend.append({
                'month': report.report_month.strftime('%Y-%m'),
                'win_rate': float(report.win_rate or 0),
                'profit_loss_ratio': float(report.profit_loss_ratio or 0),
                'total_profit_loss': float(report.total_profit_loss or 0),
                'average_score': float(report.average_score or 0),
                'total_trades': report.total_trades or 0
            })

        return trend
