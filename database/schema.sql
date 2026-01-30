-- 주식 매매일지 데이터베이스 스키마
-- SQLite 버전

-- 매매 기록 테이블
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 기본 정보
    stock_name VARCHAR(100) NOT NULL,
    stock_code VARCHAR(20),
    trade_date DATE NOT NULL,
    trade_type VARCHAR(10) NOT NULL CHECK(trade_type IN ('BUY', 'SELL')),

    -- 거래 상세
    price DECIMAL(15, 2) NOT NULL,
    quantity INTEGER NOT NULL,
    total_amount DECIMAL(15, 2),

    -- 매매 근거
    trade_reason TEXT NOT NULL,
    confidence_score INTEGER CHECK(confidence_score >= 1 AND confidence_score <= 10),

    -- 연결 정보
    linked_trade_id INTEGER,

    -- 수익 정보 (매도시)
    profit_loss DECIMAL(15, 2),
    profit_rate DECIMAL(8, 4),

    -- 메타데이터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (linked_trade_id) REFERENCES trades(id)
);

-- AI 분석 결과 테이블
CREATE TABLE IF NOT EXISTS analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id INTEGER NOT NULL,

    -- AI 평가 점수
    total_score INTEGER CHECK(total_score >= 0 AND total_score <= 100),
    logic_score INTEGER CHECK(logic_score >= 0 AND logic_score <= 40),
    timing_score INTEGER CHECK(timing_score >= 0 AND timing_score <= 30),
    risk_management_score INTEGER CHECK(risk_management_score >= 0 AND risk_management_score <= 20),
    confidence_accuracy_score INTEGER CHECK(confidence_accuracy_score >= 0 AND confidence_accuracy_score <= 10),

    -- 분석 내용
    ai_feedback TEXT,
    extracted_keywords JSON,
    market_context TEXT,

    -- 패턴 분류
    trade_pattern VARCHAR(50),
    weakness_category VARCHAR(100),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE CASCADE
);

-- 학습 과제 테이블
CREATE TABLE IF NOT EXISTS learning_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 과제 정보
    task_title VARCHAR(200) NOT NULL,
    task_description TEXT,
    task_category VARCHAR(50),
    priority INTEGER DEFAULT 1 CHECK(priority >= 1 AND priority <= 5),

    -- 연관 정보
    related_pattern VARCHAR(50),
    trigger_analysis_ids JSON,

    -- 상태
    status VARCHAR(20) DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'completed')),
    completion_date DATE,

    -- 메타데이터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 월간 리포트 테이블
CREATE TABLE IF NOT EXISTS monthly_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 기간
    report_month DATE NOT NULL,

    -- 기본 통계
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    win_rate DECIMAL(5, 2),

    -- 손익 통계
    total_profit_loss DECIMAL(15, 2),
    average_profit DECIMAL(15, 2),
    average_loss DECIMAL(15, 2),
    profit_loss_ratio DECIMAL(8, 4),
    max_profit DECIMAL(15, 2),
    max_loss DECIMAL(15, 2),

    -- 분석 결과
    best_trade_pattern VARCHAR(50),
    worst_trade_pattern VARCHAR(50),
    average_score DECIMAL(5, 2),

    -- 상세 데이터
    pattern_analysis JSON,
    keyword_summary JSON,
    improvement_suggestions JSON,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(report_month)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_trades_date ON trades(trade_date);
CREATE INDEX IF NOT EXISTS idx_trades_stock ON trades(stock_name);
CREATE INDEX IF NOT EXISTS idx_trades_type ON trades(trade_type);
CREATE INDEX IF NOT EXISTS idx_analysis_trade ON analysis_results(trade_id);
CREATE INDEX IF NOT EXISTS idx_learning_status ON learning_tasks(status);
CREATE INDEX IF NOT EXISTS idx_reports_month ON monthly_reports(report_month);

-- 트리거: trades 테이블 updated_at 자동 업데이트
CREATE TRIGGER IF NOT EXISTS update_trades_timestamp
AFTER UPDATE ON trades
BEGIN
    UPDATE trades SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 트리거: learning_tasks 테이블 updated_at 자동 업데이트
CREATE TRIGGER IF NOT EXISTS update_learning_tasks_timestamp
AFTER UPDATE ON learning_tasks
BEGIN
    UPDATE learning_tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
