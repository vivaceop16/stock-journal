# 주식 매매일지 웹 앱 아키텍처

## 1. 시스템 개요

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Streamlit Frontend                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ 매매입력 │ │ 매매목록 │ │ AI분석  │ │ 학습가이드│ │월간리포트│  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
└───────┼────────────┼────────────┼────────────┼────────────┼────────┘
        │            │            │            │            │
        ▼            ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Business Logic Layer                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │
│  │ TradeService │ │ AIAnalyzer   │ │ ReportService│                 │
│  └──────────────┘ └──────────────┘ └──────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Data Access Layer                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                      SQLite Database                          │   │
│  │  (trades, analysis_results, learning_tasks, monthly_reports)  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      External Services                               │
│  ┌──────────────┐ ┌──────────────┐                                  │
│  │ OpenAI API   │ │ 주가 데이터   │                                  │
│  │ (GPT-4)      │ │ (Optional)   │                                  │
│  └──────────────┘ └──────────────┘                                  │
└─────────────────────────────────────────────────────────────────────┘
```

## 2. 데이터베이스 스키마

### 2.1 trades (매매 기록)
```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 기본 정보
    stock_name VARCHAR(100) NOT NULL,          -- 종목명
    stock_code VARCHAR(20),                     -- 종목코드 (선택)
    trade_date DATE NOT NULL,                   -- 거래일
    trade_type VARCHAR(10) NOT NULL,            -- 'BUY' 또는 'SELL'

    -- 거래 상세
    price DECIMAL(15, 2) NOT NULL,              -- 거래가격
    quantity INTEGER NOT NULL,                  -- 수량
    total_amount DECIMAL(15, 2),                -- 총 거래금액

    -- 매매 근거
    trade_reason TEXT NOT NULL,                 -- 매수/매도 근거
    confidence_score INTEGER CHECK(             -- 확신도 (1-10)
        confidence_score >= 1 AND confidence_score <= 10
    ),

    -- 연결 정보 (매도시 어떤 매수와 연결되는지)
    linked_trade_id INTEGER,                    -- 연결된 매수 거래 ID

    -- 수익 정보 (매도 거래에만 해당)
    profit_loss DECIMAL(15, 2),                 -- 손익금액
    profit_rate DECIMAL(8, 4),                  -- 수익률 (%)

    -- 메타데이터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (linked_trade_id) REFERENCES trades(id)
);
```

### 2.2 analysis_results (AI 분석 결과)
```sql
CREATE TABLE analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id INTEGER NOT NULL,

    -- AI 평가 점수
    total_score INTEGER CHECK(                  -- 종합 점수 (0-100)
        total_score >= 0 AND total_score <= 100
    ),
    logic_score INTEGER,                        -- 논리성 점수
    timing_score INTEGER,                       -- 타이밍 점수
    risk_management_score INTEGER,              -- 리스크 관리 점수

    -- 분석 내용
    ai_feedback TEXT,                           -- AI 피드백
    extracted_keywords JSON,                    -- 추출된 키워드
    market_context TEXT,                        -- 시장 상황 분석

    -- 패턴 분류
    trade_pattern VARCHAR(50),                  -- 매매 패턴 분류
    weakness_category VARCHAR(100),             -- 약점 카테고리

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (trade_id) REFERENCES trades(id)
);
```

### 2.3 learning_tasks (학습 과제)
```sql
CREATE TABLE learning_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 과제 정보
    task_title VARCHAR(200) NOT NULL,           -- 과제 제목
    task_description TEXT,                       -- 과제 설명
    task_category VARCHAR(50),                   -- 카테고리 (기술분석, 심리, 리스크관리 등)
    priority INTEGER DEFAULT 1,                  -- 우선순위 (1-5)

    -- 연관 정보
    related_pattern VARCHAR(50),                 -- 관련 매매 패턴
    trigger_analysis_ids JSON,                   -- 이 과제를 생성하게 한 분석 ID들

    -- 상태
    status VARCHAR(20) DEFAULT 'pending',        -- pending, in_progress, completed
    completion_date DATE,

    -- 메타데이터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.4 monthly_reports (월간 리포트)
```sql
CREATE TABLE monthly_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 기간
    report_month DATE NOT NULL,                  -- 리포트 월 (YYYY-MM-01 형식)

    -- 기본 통계
    total_trades INTEGER,                        -- 총 거래 수
    winning_trades INTEGER,                      -- 수익 거래 수
    losing_trades INTEGER,                       -- 손실 거래 수
    win_rate DECIMAL(5, 2),                      -- 승률 (%)

    -- 손익 통계
    total_profit_loss DECIMAL(15, 2),           -- 총 손익
    average_profit DECIMAL(15, 2),              -- 평균 수익
    average_loss DECIMAL(15, 2),                -- 평균 손실
    profit_loss_ratio DECIMAL(8, 4),            -- 손익비
    max_profit DECIMAL(15, 2),                  -- 최대 수익
    max_loss DECIMAL(15, 2),                    -- 최대 손실

    -- 분석 결과
    best_trade_pattern VARCHAR(50),              -- 최고 수익 매매 유형
    worst_trade_pattern VARCHAR(50),             -- 최저 수익 매매 유형
    average_score DECIMAL(5, 2),                -- 평균 AI 점수

    -- 상세 데이터 (JSON)
    pattern_analysis JSON,                       -- 패턴별 분석
    keyword_summary JSON,                        -- 키워드 요약
    improvement_suggestions JSON,                -- 개선 제안

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(report_month)
);
```

### 2.5 인덱스
```sql
-- 자주 조회되는 컬럼에 인덱스 생성
CREATE INDEX idx_trades_date ON trades(trade_date);
CREATE INDEX idx_trades_stock ON trades(stock_name);
CREATE INDEX idx_trades_type ON trades(trade_type);
CREATE INDEX idx_analysis_trade ON analysis_results(trade_id);
CREATE INDEX idx_learning_status ON learning_tasks(status);
CREATE INDEX idx_reports_month ON monthly_reports(report_month);
```

## 3. 핵심 모듈 구조

### 3.1 Trade Service (매매 관리)
```python
class TradeService:
    def create_trade(trade_data: dict) -> Trade
    def get_trade(trade_id: int) -> Trade
    def list_trades(filters: dict) -> List[Trade]
    def link_sell_to_buy(sell_id: int, buy_id: int) -> None
    def calculate_profit(sell_trade: Trade) -> dict
```

### 3.2 AI Analyzer (AI 분석)
```python
class AIAnalyzer:
    def analyze_trade(trade: Trade) -> AnalysisResult
    def extract_keywords(text: str) -> List[str]
    def evaluate_logic(reason: str, result: dict) -> int
    def classify_pattern(trade: Trade) -> str
    def generate_feedback(analysis: AnalysisResult) -> str
```

### 3.3 Learning Guide (학습 가이드)
```python
class LearningGuide:
    def analyze_weaknesses(analyses: List[AnalysisResult]) -> List[str]
    def generate_tasks(weaknesses: List[str]) -> List[LearningTask]
    def prioritize_tasks(tasks: List[LearningTask]) -> List[LearningTask]
    def get_recommended_resources(category: str) -> List[str]
```

### 3.4 Report Service (리포트 생성)
```python
class ReportService:
    def generate_monthly_report(year: int, month: int) -> MonthlyReport
    def calculate_statistics(trades: List[Trade]) -> dict
    def analyze_patterns(trades: List[Trade]) -> dict
    def create_dashboard_data(report: MonthlyReport) -> dict
```

## 4. AI 분석 로직

### 4.1 매매 점수 산출 기준 (0-100점)

| 항목 | 배점 | 평가 기준 |
|------|------|-----------|
| 논리성 (Logic) | 40점 | 매매 근거의 구체성, 일관성, 객관적 지표 활용 |
| 타이밍 (Timing) | 30점 | 실제 수익률과 진입/청산 시점 적절성 |
| 리스크 관리 (Risk) | 20점 | 손절/익절 계획, 포지션 사이즈 |
| 확신도 정확성 | 10점 | 본인 확신도와 실제 결과의 상관관계 |

### 4.2 키워드 추출 카테고리

- **기술적 분석**: 이동평균선, RSI, MACD, 볼린저밴드, 거래량, 지지/저항
- **펀더멘털**: 실적, PER, PBR, 배당, 성장성, 뉴스
- **심리/감정**: 공포, 탐욕, FOMO, 손절, 물타기
- **시장상황**: 상승장, 하락장, 박스권, 테마주, 섹터

### 4.3 약점 패턴 분류

| 패턴 | 설명 | 추천 학습 |
|------|------|-----------|
| 충동매매 | 근거 없이 급등주 추격 | 심리 제어, 매매 원칙 |
| 손절 실패 | 손절선 무시, 물타기 | 리스크 관리, 손절 훈련 |
| 과신 매매 | 높은 확신도 + 낮은 수익률 | 겸손, 확률적 사고 |
| 기술분석 부재 | 차트 분석 없는 매매 | 기술적 분석 기초 |
| 뉴스 추종 | 뉴스에만 의존한 매매 | 펀더멘털 분석 |

## 5. 프로젝트 파일 구조

```
stock-trading-journal/
│
├── app.py                      # Streamlit 메인 앱
├── requirements.txt            # 의존성 패키지
├── .env                        # 환경변수 (API 키 등)
│
├── config/
│   └── settings.py             # 설정 파일
│
├── database/
│   ├── __init__.py
│   ├── connection.py           # DB 연결 관리
│   ├── models.py               # SQLAlchemy 모델
│   └── schema.sql              # 스키마 SQL
│
├── services/
│   ├── __init__.py
│   ├── trade_service.py        # 매매 관리 서비스
│   ├── ai_analyzer.py          # AI 분석 서비스
│   ├── learning_guide.py       # 학습 가이드 서비스
│   └── report_service.py       # 리포트 서비스
│
├── pages/
│   ├── 1_📝_매매입력.py         # 매매 기록 입력
│   ├── 2_📊_매매목록.py         # 매매 기록 조회
│   ├── 3_🤖_AI분석.py           # AI 분석 결과
│   ├── 4_📚_학습가이드.py       # 학습 과제
│   └── 5_📈_월간리포트.py       # 월간 대시보드
│
├── components/
│   ├── __init__.py
│   ├── charts.py               # 차트 컴포넌트
│   ├── forms.py                # 입력 폼 컴포넌트
│   └── cards.py                # 카드 UI 컴포넌트
│
├── utils/
│   ├── __init__.py
│   ├── helpers.py              # 유틸리티 함수
│   └── constants.py            # 상수 정의
│
└── docs/
    └── architecture.md         # 이 문서
```

## 6. 주요 화면 구성

### 6.1 매매 입력 화면
- 종목명 (자동완성)
- 날짜 선택
- 매수/매도 선택
- 가격, 수량 입력
- 매매 근거 텍스트 (최소 50자 권장)
- 확신도 슬라이더 (1-10)
- 매도시 연결할 매수 건 선택

### 6.2 AI 분석 화면
- 선택한 매매의 상세 정보
- AI 종합 점수 (게이지 차트)
- 항목별 점수 (레이더 차트)
- 추출된 키워드 (태그 클라우드)
- AI 피드백 텍스트
- 유사 패턴 과거 매매 비교

### 6.3 월간 리포트 대시보드
- 승률 추이 (라인 차트)
- 손익 현황 (바 차트)
- 매매 유형별 성과 (파이 차트)
- 주요 지표 카드 (KPI)
- 월별 비교 테이블

## 7. 기술 스택

| 구분 | 기술 |
|------|------|
| Frontend | Streamlit |
| Backend | Python 3.10+ |
| Database | SQLite (개발) / PostgreSQL (운영) |
| ORM | SQLAlchemy |
| AI | OpenAI GPT-4 API |
| Charts | Plotly, Altair |
| Data | Pandas, NumPy |

## 8. 확장 계획

1. **사용자 인증**: Streamlit Auth 또는 별도 인증 시스템
2. **주가 데이터 연동**: yfinance, KRX API 연동
3. **백테스트**: 과거 매매 패턴 시뮬레이션
4. **알림 시스템**: 학습 리마인더, 월간 리포트 알림
5. **소셜 기능**: 매매 일지 공유, 커뮤니티
