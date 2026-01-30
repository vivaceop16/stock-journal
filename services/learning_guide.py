"""학습 가이드 서비스"""

from typing import List, Dict, Any, Optional
from datetime import date
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.models import AnalysisResult, LearningTask, Trade
from database.connection import db_manager
from config.settings import WEAKNESS_PATTERNS, LEARNING_CATEGORIES


class LearningGuide:
    """개인화된 학습 가이드 서비스"""

    def __init__(self, session: Optional[Session] = None):
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            return db_manager.get_session()
        return self._session

    def analyze_weaknesses(self, analyses: List[AnalysisResult]) -> Dict[str, Any]:
        """약점 패턴 분석"""
        if not analyses:
            return {'patterns': {}, 'categories': {}, 'summary': '분석할 데이터가 없습니다.'}

        # 약점 패턴 카운트
        pattern_counts = Counter()
        weakness_counts = Counter()

        for analysis in analyses:
            if analysis.trade_pattern:
                pattern_counts[analysis.trade_pattern] += 1
            if analysis.weakness_category:
                weakness_counts[analysis.weakness_category] += 1

        # 낮은 점수 항목 분석
        low_logic = sum(1 for a in analyses if a.logic_score and a.logic_score < 20)
        low_timing = sum(1 for a in analyses if a.timing_score and a.timing_score < 15)
        low_risk = sum(1 for a in analyses if a.risk_management_score and a.risk_management_score < 10)

        # 카테고리별 약점
        category_issues = {}
        if low_logic > len(analyses) * 0.3:
            category_issues['논리성'] = '매매 근거가 불충분한 경우가 많습니다.'
        if low_timing > len(analyses) * 0.3:
            category_issues['타이밍'] = '진입/청산 타이밍 개선이 필요합니다.'
        if low_risk > len(analyses) * 0.3:
            category_issues['리스크관리'] = '손절/익절 규칙 수립이 필요합니다.'

        # 요약 생성
        summary_parts = []
        if weakness_counts:
            top_weakness = weakness_counts.most_common(1)[0]
            summary_parts.append(f"가장 빈번한 약점: {top_weakness[0]} ({top_weakness[1]}회)")

        if category_issues:
            summary_parts.append(f"개선 필요 영역: {', '.join(category_issues.keys())}")

        return {
            'patterns': dict(pattern_counts),
            'weaknesses': dict(weakness_counts),
            'categories': category_issues,
            'score_distribution': {
                'low_logic': low_logic,
                'low_timing': low_timing,
                'low_risk': low_risk
            },
            'summary': ' | '.join(summary_parts) if summary_parts else '전반적으로 양호합니다.'
        }

    def generate_tasks(self, weakness_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """약점 기반 학습 과제 생성"""
        tasks = []
        weaknesses = weakness_analysis.get('weaknesses', {})
        categories = weakness_analysis.get('categories', {})

        # 약점 패턴 기반 과제
        for weakness, count in weaknesses.items():
            if weakness in WEAKNESS_PATTERNS:
                pattern_info = WEAKNESS_PATTERNS[weakness]
                for learning_task in pattern_info['learning_tasks']:
                    tasks.append({
                        'task_title': learning_task,
                        'task_description': f"{pattern_info['description']}에 대응하기 위한 학습입니다.",
                        'task_category': self._get_category_for_task(learning_task),
                        'priority': min(count, 5),
                        'related_pattern': weakness
                    })

        # 카테고리별 약점 기반 과제
        for category, issue in categories.items():
            if category == '논리성':
                tasks.append({
                    'task_title': '매매 체크리스트 작성',
                    'task_description': '매매 전 확인해야 할 항목들을 정리합니다.',
                    'task_category': '기술분석',
                    'priority': 4,
                    'related_pattern': None
                })
            elif category == '타이밍':
                tasks.append({
                    'task_title': '진입/청산 규칙 수립',
                    'task_description': '명확한 진입/청산 기준을 설정합니다.',
                    'task_category': '기술분석',
                    'priority': 4,
                    'related_pattern': None
                })
            elif category == '리스크관리':
                tasks.append({
                    'task_title': '자금 관리 계획 수립',
                    'task_description': '포지션 사이즈와 손절 규칙을 정립합니다.',
                    'task_category': '리스크관리',
                    'priority': 5,
                    'related_pattern': None
                })

        # 중복 제거 및 우선순위 정렬
        seen_titles = set()
        unique_tasks = []
        for task in tasks:
            if task['task_title'] not in seen_titles:
                seen_titles.add(task['task_title'])
                unique_tasks.append(task)

        return sorted(unique_tasks, key=lambda x: x['priority'], reverse=True)

    def _get_category_for_task(self, task_title: str) -> str:
        """과제 제목에서 카테고리 추론"""
        title_lower = task_title.lower()

        if any(w in title_lower for w in ['차트', '지표', '분석', '패턴']):
            return '기술분석'
        elif any(w in title_lower for w in ['심리', '감정', '원칙', '인내']):
            return '심리'
        elif any(w in title_lower for w in ['손절', '리스크', '자금', '포지션']):
            return '리스크관리'
        elif any(w in title_lower for w in ['재무', '실적', '기업', '가치']):
            return '펀더멘털'
        else:
            return '심리'

    def create_learning_task(self, task_data: Dict[str, Any]) -> LearningTask:
        """학습 과제 생성"""
        task = LearningTask(
            task_title=task_data['task_title'],
            task_description=task_data.get('task_description'),
            task_category=task_data.get('task_category'),
            priority=task_data.get('priority', 1),
            related_pattern=task_data.get('related_pattern'),
            trigger_analysis_ids=task_data.get('trigger_analysis_ids'),
            status='pending'
        )

        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def get_pending_tasks(self) -> List[LearningTask]:
        """대기 중인 과제 조회"""
        return self.session.query(LearningTask).filter(
            LearningTask.status.in_(['pending', 'in_progress'])
        ).order_by(desc(LearningTask.priority), LearningTask.created_at).all()

    def get_tasks_by_category(self, category: str) -> List[LearningTask]:
        """카테고리별 과제 조회"""
        return self.session.query(LearningTask).filter(
            LearningTask.task_category == category
        ).order_by(desc(LearningTask.priority)).all()

    def update_task_status(self, task_id: int, status: str) -> Optional[LearningTask]:
        """과제 상태 업데이트"""
        task = self.session.query(LearningTask).filter(LearningTask.id == task_id).first()
        if task:
            task.status = status
            if status == 'completed':
                task.completion_date = date.today()
            self.session.commit()
            return task
        return None

    def get_recommended_resources(self, category: str) -> List[str]:
        """카테고리별 추천 학습 자료"""
        if category in LEARNING_CATEGORIES:
            return LEARNING_CATEGORIES[category]['resources']
        return []

    def get_learning_summary(self) -> Dict[str, Any]:
        """학습 현황 요약"""
        all_tasks = self.session.query(LearningTask).all()

        if not all_tasks:
            return {
                'total': 0,
                'completed': 0,
                'in_progress': 0,
                'pending': 0,
                'completion_rate': 0,
                'by_category': {}
            }

        status_counts = Counter(t.status for t in all_tasks)
        category_counts = Counter(t.task_category for t in all_tasks)

        completed = status_counts.get('completed', 0)
        total = len(all_tasks)

        return {
            'total': total,
            'completed': completed,
            'in_progress': status_counts.get('in_progress', 0),
            'pending': status_counts.get('pending', 0),
            'completion_rate': (completed / total * 100) if total > 0 else 0,
            'by_category': dict(category_counts)
        }

    def auto_generate_tasks_from_analyses(self) -> List[LearningTask]:
        """최근 분석 결과를 기반으로 자동 과제 생성"""
        # 낮은 점수의 최근 분석 조회
        recent_analyses = self.session.query(AnalysisResult).filter(
            AnalysisResult.total_score < 60
        ).order_by(desc(AnalysisResult.created_at)).limit(10).all()

        if not recent_analyses:
            return []

        # 약점 분석
        weakness_analysis = self.analyze_weaknesses(recent_analyses)

        # 과제 생성
        task_data_list = self.generate_tasks(weakness_analysis)

        # 기존 과제와 중복 체크
        existing_titles = set(
            t.task_title for t in self.session.query(LearningTask).filter(
                LearningTask.status != 'completed'
            ).all()
        )

        created_tasks = []
        for task_data in task_data_list:
            if task_data['task_title'] not in existing_titles:
                task_data['trigger_analysis_ids'] = [a.id for a in recent_analyses[:3]]
                task = self.create_learning_task(task_data)
                created_tasks.append(task)

        return created_tasks
