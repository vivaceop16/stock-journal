"""AI 분석 서비스"""

import json
import re
from typing import List, Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from database.models import Trade, AnalysisResult
from database.connection import db_manager, get_db_session
from config.settings import (
    ai_settings,
    SCORE_WEIGHTS,
    KEYWORD_CATEGORIES,
    WEAKNESS_PATTERNS
)

# OpenAI 라이브러리는 선택적 import
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class AIAnalyzer:
    """AI 기반 매매 분석 서비스"""

    def __init__(self):
        self._client = None

    @property
    def session(self) -> Session:
        """새 세션 반환 (조회용)"""
        return db_manager.get_session()

    @property
    def client(self):
        """OpenAI 클라이언트 (지연 초기화)"""
        if self._client is None and OPENAI_AVAILABLE and ai_settings.OPENAI_API_KEY:
            self._client = OpenAI(api_key=ai_settings.OPENAI_API_KEY)
        return self._client

    def analyze_trade(self, trade: Trade) -> AnalysisResult:
        """매매 분석 실행"""
        # 키워드 추출
        keywords = self.extract_keywords(trade.trade_reason)

        # 패턴 분류
        pattern = self.classify_pattern(trade, keywords)

        # 약점 분석
        weakness = self._identify_weakness(trade, keywords)

        # AI를 통한 상세 분석 (API 키가 있는 경우)
        if self.client:
            ai_analysis = self._get_ai_analysis(trade)
        else:
            ai_analysis = self._get_rule_based_analysis(trade, keywords, pattern)

        # 점수 계산
        scores = self._calculate_scores(trade, ai_analysis, keywords)

        # 분석 결과 저장 - 컨텍스트 매니저 사용
        with get_db_session() as session:
            # 기존 분석 결과가 있으면 삭제
            existing = session.query(AnalysisResult).filter(
                AnalysisResult.trade_id == trade.id
            ).first()
            if existing:
                session.delete(existing)
                session.commit()

            # 새 분석 결과 생성
            analysis = AnalysisResult(
                trade_id=trade.id,
                total_score=scores['total'],
                logic_score=scores['logic'],
                timing_score=scores['timing'],
                risk_management_score=scores['risk_management'],
                confidence_accuracy_score=scores['confidence_accuracy'],
                ai_feedback=ai_analysis.get('feedback', ''),
                extracted_keywords=keywords,
                market_context=ai_analysis.get('market_context', ''),
                trade_pattern=pattern,
                weakness_category=weakness
            )

            session.add(analysis)
            session.commit()

            # 결과를 딕셔너리로 변환하여 반환용 객체 생성
            result_data = {
                'id': analysis.id,
                'trade_id': analysis.trade_id,
                'total_score': analysis.total_score,
                'logic_score': analysis.logic_score,
                'timing_score': analysis.timing_score,
                'risk_management_score': analysis.risk_management_score,
                'confidence_accuracy_score': analysis.confidence_accuracy_score,
                'ai_feedback': analysis.ai_feedback,
                'extracted_keywords': analysis.extracted_keywords,
                'market_context': analysis.market_context,
                'trade_pattern': analysis.trade_pattern,
                'weakness_category': analysis.weakness_category
            }

        # 새 세션에서 분석 결과 다시 조회하여 반환
        return self.get_analysis_for_trade(trade.id)

    def extract_keywords(self, text: str) -> Dict[str, List[str]]:
        """텍스트에서 키워드 추출"""
        extracted = {}
        text_lower = text.lower()

        for category, keywords in KEYWORD_CATEGORIES.items():
            found = []
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    found.append(keyword)
            if found:
                extracted[category] = found

        return extracted

    def classify_pattern(self, trade: Trade, keywords: Dict[str, List[str]]) -> str:
        """매매 패턴 분류"""
        reason = trade.trade_reason.lower()

        # 충동매매 패턴
        if any(word in reason for word in ['급등', '추격', '빠르게', '놓칠까봐']):
            return '충동매매'

        # 기술분석 기반
        if '기술분석' in keywords or any(word in reason for word in ['차트', '이평', '지표']):
            return '기술분석_기반'

        # 펀더멘털 기반
        if '펀더멘털' in keywords or any(word in reason for word in ['실적', '재무', 'per', 'pbr']):
            return '펀더멘털_기반'

        # 뉴스/테마 기반
        if '뉴스/이벤트' in keywords or any(word in reason for word in ['뉴스', '테마', '정책']):
            return '뉴스_기반'

        # 심리적 매매
        if '심리/감정' in keywords:
            return '심리적_매매'

        return '복합_분석'

    def _identify_weakness(self, trade: Trade, keywords: Dict[str, List[str]]) -> Optional[str]:
        """약점 패턴 식별"""
        reason = trade.trade_reason.lower()

        # 각 약점 패턴 체크
        for pattern_name, pattern_info in WEAKNESS_PATTERNS.items():
            pattern_keywords = pattern_info['keywords']
            if any(kw.lower() in reason for kw in pattern_keywords):
                return pattern_name

        # 결과 기반 약점 분석 (매도 거래인 경우)
        if trade.trade_type == 'SELL' and trade.profit_rate is not None:
            # 높은 확신도 + 손실 = 과신 매매
            if trade.confidence_score and trade.confidence_score >= 8 and trade.profit_rate < 0:
                return '과신_매매'

            # 큰 손실 + 물타기 언급 없음 = 손절 실패 가능성
            if trade.profit_rate < -10:  # 10% 이상 손실
                return '손절_실패'

        return None

    def _get_ai_analysis(self, trade: Trade) -> Dict[str, Any]:
        """OpenAI API를 통한 상세 분석"""
        prompt = self._build_analysis_prompt(trade)

        try:
            response = self.client.chat.completions.create(
                model=ai_settings.MODEL_NAME,
                messages=[
                    {"role": "system", "content": "당신은 주식 매매 분석 전문가입니다. 사용자의 매매 기록을 분석하고 건설적인 피드백을 제공합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=ai_settings.MAX_TOKENS,
                temperature=ai_settings.TEMPERATURE
            )

            content = response.choices[0].message.content
            return self._parse_ai_response(content)

        except Exception as e:
            print(f"AI 분석 오류: {e}")
            return self._get_rule_based_analysis(trade, {}, '')

    def _build_analysis_prompt(self, trade: Trade) -> str:
        """AI 분석 프롬프트 생성"""
        trade_info = f"""
매매 정보:
- 종목: {trade.stock_name}
- 거래 유형: {'매수' if trade.trade_type == 'BUY' else '매도'}
- 거래일: {trade.trade_date}
- 가격: {trade.price:,}원
- 수량: {trade.quantity}주
- 매매 근거: {trade.trade_reason}
- 확신도: {trade.confidence_score}/10
"""

        if trade.trade_type == 'SELL' and trade.profit_rate is not None:
            trade_info += f"""
- 수익률: {trade.profit_rate:.2f}%
- 손익금: {trade.profit_loss:,}원
"""

        prompt = f"""{trade_info}

위 매매 기록을 분석해주세요. 다음 형식으로 응답해주세요:

1. 논리성 평가 (0-40점):
[매매 근거의 구체성, 논리적 일관성, 객관적 지표 활용 여부 평가]

2. 타이밍 평가 (0-30점):
[진입/청산 시점의 적절성 평가]

3. 리스크 관리 평가 (0-20점):
[손절/익절 계획, 포지션 사이즈 적절성 평가]

4. 시장 상황 분석:
[매매 시점의 시장 상황에 대한 분석]

5. 개선 제안:
[향후 매매에서 개선할 점]

6. 총평:
[전반적인 피드백]
"""
        return prompt

    def _parse_ai_response(self, content: str) -> Dict[str, Any]:
        """AI 응답 파싱"""
        # 간단한 파싱 로직
        result = {
            'feedback': content,
            'market_context': '',
            'scores': {
                'logic': 25,
                'timing': 20,
                'risk_management': 15
            }
        }

        # 점수 추출 시도
        logic_match = re.search(r'논리성.*?(\d+)', content)
        if logic_match:
            result['scores']['logic'] = min(int(logic_match.group(1)), 40)

        timing_match = re.search(r'타이밍.*?(\d+)', content)
        if timing_match:
            result['scores']['timing'] = min(int(timing_match.group(1)), 30)

        risk_match = re.search(r'리스크.*?(\d+)', content)
        if risk_match:
            result['scores']['risk_management'] = min(int(risk_match.group(1)), 20)

        # 시장 상황 추출
        market_match = re.search(r'시장 상황[^:]*:(.*?)(?=\d\.|개선|총평|$)', content, re.DOTALL)
        if market_match:
            result['market_context'] = market_match.group(1).strip()

        return result

    def _get_rule_based_analysis(
        self,
        trade: Trade,
        keywords: Dict[str, List[str]],
        pattern: str
    ) -> Dict[str, Any]:
        """규칙 기반 분석 (AI 없이)"""
        feedback_parts = []
        scores = {'logic': 20, 'timing': 15, 'risk_management': 10}

        # 근거 길이 체크
        reason_length = len(trade.trade_reason)
        if reason_length < 30:
            feedback_parts.append("매매 근거가 너무 짧습니다. 더 구체적인 근거를 기록해주세요.")
        elif reason_length >= 100:
            scores['logic'] += 10
            feedback_parts.append("상세한 매매 근거가 좋습니다.")

        # 키워드 기반 점수
        if '기술분석' in keywords:
            scores['logic'] += 5
            feedback_parts.append("기술적 분석 지표를 활용한 점이 좋습니다.")

        if '펀더멘털' in keywords:
            scores['logic'] += 5
            feedback_parts.append("펀더멘털 분석을 고려한 점이 좋습니다.")

        if '심리/감정' in keywords and any(w in trade.trade_reason.lower() for w in ['공포', '탐욕', 'fomo']):
            scores['logic'] -= 5
            feedback_parts.append("감정적 요소가 매매에 영향을 준 것 같습니다. 객관적 지표 중심으로 판단해보세요.")

        # 수익률 기반 타이밍 점수 (매도인 경우)
        if trade.trade_type == 'SELL' and trade.profit_rate is not None:
            profit_rate = float(trade.profit_rate)
            if profit_rate >= 10:
                scores['timing'] += 10
                feedback_parts.append(f"수익률 {profit_rate:.1f}%로 좋은 타이밍에 청산하셨습니다.")
            elif profit_rate >= 0:
                scores['timing'] += 5
                feedback_parts.append("수익으로 마무리하셨습니다.")
            elif profit_rate >= -5:
                feedback_parts.append("소폭 손실이지만 리스크 관리가 되었습니다.")
            else:
                scores['timing'] -= 5
                feedback_parts.append("손실이 크네요. 손절 규칙을 재검토해보세요.")

        # 확신도와 결과 비교
        if trade.confidence_score and trade.trade_type == 'SELL' and trade.profit_rate is not None:
            profit_rate = float(trade.profit_rate)
            if trade.confidence_score >= 8 and profit_rate < 0:
                feedback_parts.append("확신도가 높았지만 손실이 발생했습니다. 과신에 주의하세요.")
            elif trade.confidence_score <= 3 and profit_rate > 10:
                feedback_parts.append("확신도가 낮았는데 좋은 결과가 나왔네요. 분석 기준을 재점검해보세요.")

        return {
            'feedback': '\n'.join(feedback_parts) if feedback_parts else '분석을 위한 충분한 정보가 없습니다.',
            'market_context': '',
            'scores': scores
        }

    def _calculate_scores(
        self,
        trade: Trade,
        ai_analysis: Dict[str, Any],
        keywords: Dict[str, List[str]]
    ) -> Dict[str, int]:
        """최종 점수 계산"""
        scores = ai_analysis.get('scores', {})

        logic = min(scores.get('logic', 20), 40)
        timing = min(scores.get('timing', 15), 30)
        risk_management = min(scores.get('risk_management', 10), 20)

        # 확신도 정확성 점수 (매도인 경우)
        confidence_accuracy = 5  # 기본값
        if trade.confidence_score and trade.trade_type == 'SELL' and trade.profit_rate is not None:
            profit_rate = float(trade.profit_rate)
            # 높은 확신도 + 높은 수익 or 낮은 확신도 + 낮은 수익 = 좋은 점수
            if (trade.confidence_score >= 7 and profit_rate >= 5) or \
               (trade.confidence_score <= 4 and profit_rate <= 0):
                confidence_accuracy = 8
            elif (trade.confidence_score >= 7 and profit_rate < 0) or \
                 (trade.confidence_score <= 4 and profit_rate > 10):
                confidence_accuracy = 2

        total = logic + timing + risk_management + confidence_accuracy

        return {
            'total': total,
            'logic': logic,
            'timing': timing,
            'risk_management': risk_management,
            'confidence_accuracy': confidence_accuracy
        }

    def get_analysis_for_trade(self, trade_id: int) -> Optional[AnalysisResult]:
        """특정 매매의 분석 결과 조회"""
        session = db_manager.get_session()
        try:
            return session.query(AnalysisResult).filter(
                AnalysisResult.trade_id == trade_id
            ).first()
        finally:
            session.close()

    def get_low_score_analyses(self, threshold: int = 50) -> List[AnalysisResult]:
        """낮은 점수의 분석 결과 조회"""
        session = db_manager.get_session()
        try:
            return session.query(AnalysisResult).filter(
                AnalysisResult.total_score < threshold
            ).all()
        finally:
            session.close()
