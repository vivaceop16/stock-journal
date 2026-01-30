"""애플리케이션 설정"""

import os
from dataclasses import dataclass
from typing import List


@dataclass
class AppSettings:
    """앱 설정"""
    APP_NAME: str = "주식 매매일지"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False


@dataclass
class DatabaseSettings:
    """데이터베이스 설정"""
    DATABASE_URL: str = os.environ.get('DATABASE_URL', 'sqlite:///./data/trading_journal.db')


@dataclass
class AISettings:
    """AI 관련 설정"""
    OPENAI_API_KEY: str = os.environ.get('OPENAI_API_KEY', '')
    MODEL_NAME: str = "gpt-4"
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.3


# 매매 점수 가중치
SCORE_WEIGHTS = {
    'logic': 40,          # 논리성 (40점)
    'timing': 30,         # 타이밍 (30점)
    'risk_management': 20, # 리스크 관리 (20점)
    'confidence_accuracy': 10  # 확신도 정확성 (10점)
}

# 키워드 카테고리
KEYWORD_CATEGORIES = {
    '기술분석': [
        '이동평균선', '이평선', 'MA', '골든크로스', '데드크로스',
        'RSI', 'MACD', '볼린저밴드', '거래량', '지지선', '저항선',
        '추세선', '캔들', '패턴', '눌림목', '돌파', '이격도'
    ],
    '펀더멘털': [
        '실적', '매출', '영업이익', 'PER', 'PBR', 'ROE', 'ROA',
        '배당', '성장성', '재무제표', '공시', 'IR', '컨센서스'
    ],
    '뉴스/이벤트': [
        '뉴스', '공시', '테마', '정책', '금리', '환율',
        '수급', '외국인', '기관', '신고가', '상한가'
    ],
    '심리/감정': [
        '공포', '탐욕', 'FOMO', '조급', '확신', '불안',
        '손절', '물타기', '추격매수', '패닉', '희망'
    ],
    '시장상황': [
        '상승장', '하락장', '박스권', '횡보', '변동성',
        '조정', '반등', '추세', '사이클', '섹터'
    ]
}

# 약점 패턴 정의
WEAKNESS_PATTERNS = {
    '충동매매': {
        'description': '명확한 근거 없이 급등주를 추격하거나 감정적으로 매매',
        'keywords': ['급등', '추격', 'FOMO', '감정', '충동'],
        'learning_tasks': ['매매 원칙 수립', '심리 제어 훈련', '체크리스트 활용']
    },
    '손절_실패': {
        'description': '미리 정한 손절선을 지키지 않거나 물타기로 손실 확대',
        'keywords': ['손절', '물타기', '버티기', '존버', '평단'],
        'learning_tasks': ['손절 규칙 훈련', '리스크 관리', '포지션 사이징']
    },
    '과신_매매': {
        'description': '높은 확신도를 가졌으나 실제 결과가 좋지 않은 패턴',
        'keywords': ['확신', '자신감', '올인'],
        'learning_tasks': ['겸손한 사고', '확률적 접근', '분산 투자']
    },
    '기술분석_부재': {
        'description': '차트나 기술적 지표 분석 없이 매매',
        'keywords': ['감', '촉', '느낌', '소문'],
        'learning_tasks': ['기술적 분석 기초', '차트 패턴 학습', '지표 활용법']
    },
    '뉴스_추종': {
        'description': '뉴스나 테마에만 의존하여 펀더멘털 분석 없이 매매',
        'keywords': ['뉴스', '테마', '소문', '카더라'],
        'learning_tasks': ['펀더멘털 분석', '기업 분석 방법', '정보 검증']
    },
    '오버트레이딩': {
        'description': '과도하게 잦은 매매로 수수료 손실 및 판단력 저하',
        'keywords': ['빈번', '자주', '계속', '반복'],
        'learning_tasks': ['매매 횟수 제한', '기회 선별', '인내심 훈련']
    }
}

# 학습 과제 카테고리
LEARNING_CATEGORIES = {
    '기술분석': {
        'description': '차트 분석 및 기술적 지표 활용',
        'resources': [
            '이동평균선의 원리와 활용',
            'RSI, MACD 해석법',
            '지지/저항선 찾기',
            '캔들 패턴 분석'
        ]
    },
    '심리': {
        'description': '매매 심리 제어 및 감정 관리',
        'resources': [
            '투자 심리학 기초',
            'FOMO와 공포 극복',
            '일관된 매매 원칙 수립',
            '감정 일기 작성'
        ]
    },
    '리스크관리': {
        'description': '손실 제어 및 자금 관리',
        'resources': [
            '손절 규칙 설정',
            '포지션 사이징',
            '분산 투자 전략',
            '리스크/리워드 비율'
        ]
    },
    '펀더멘털': {
        'description': '기업 분석 및 가치 평가',
        'resources': [
            '재무제표 읽기',
            'PER, PBR 해석',
            '산업 분석 방법',
            '기업 가치 평가'
        ]
    }
}

# 설정 인스턴스
app_settings = AppSettings()
db_settings = DatabaseSettings()
ai_settings = AISettings()
