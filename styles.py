"""토스 스타일 UI 컴포넌트 - v2"""

import streamlit as st

__all__ = [
    'apply_toss_style',
    'toss_card',
    'toss_list_item',
    'toss_section_title',
    'toss_badge',
    'summary_card',
    'status_badge',
    'data_table_header',
    'data_table_row',
]

# 토스 스타일 CSS
TOSS_CSS = """
<style>
    /* 전체 배경 */
    .stApp {
        background-color: #F7F8FA;
    }

    /* 카드 스타일 */
    .toss-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        border: 1px solid #F2F3F5;
    }

    .toss-card-title {
        font-size: 14px;
        color: #8B95A1;
        margin-bottom: 8px;
        font-weight: 500;
    }

    .toss-card-value {
        font-size: 28px;
        font-weight: 700;
        color: #191F28;
        line-height: 1.3;
    }

    .toss-card-value.positive {
        color: #F04452;
    }

    .toss-card-value.negative {
        color: #3182F6;
    }

    /* 요약 카드 (상단 대시보드용) */
    .summary-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        border: 1px solid #E5E8EB;
    }

    .summary-card-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 12px auto;
        font-size: 24px;
    }

    .summary-card-icon.blue {
        background: #E8F3FF;
    }

    .summary-card-icon.red {
        background: #FFEFEF;
    }

    .summary-card-icon.green {
        background: #E8F8F0;
    }

    .summary-card-value {
        font-size: 20px;
        font-weight: 700;
        color: #191F28;
        margin-bottom: 4px;
        word-break: keep-all;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .summary-card-value.positive {
        color: #F04452;
    }

    .summary-card-value.negative {
        color: #3182F6;
    }

    /* 반응형 - 작은 화면에서 폰트 크기 조정 */
    @media (max-width: 1200px) {
        .summary-card-value {
            font-size: 18px;
        }
    }

    .summary-card-label {
        font-size: 13px;
        color: #8B95A1;
        font-weight: 500;
    }

    /* 리스트 아이템 */
    .toss-list-item {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid #F2F3F5;
    }

    .toss-list-left {
        display: flex;
        flex-direction: column;
    }

    .toss-list-title {
        font-size: 16px;
        font-weight: 600;
        color: #191F28;
        margin-bottom: 4px;
    }

    .toss-list-subtitle {
        font-size: 13px;
        color: #8B95A1;
    }

    .toss-list-right {
        text-align: right;
    }

    .toss-list-amount {
        font-size: 16px;
        font-weight: 600;
        color: #191F28;
    }

    .toss-list-amount.positive {
        color: #F04452;
    }

    .toss-list-amount.negative {
        color: #3182F6;
    }

    .toss-list-change {
        font-size: 13px;
        color: #8B95A1;
    }

    /* 테이블 스타일 */
    .data-table {
        width: 100%;
        background: #FFFFFF;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }

    .data-table-header {
        display: grid;
        grid-template-columns: 1.5fr 1fr 1fr 1fr 1fr 0.8fr;
        padding: 14px 20px;
        background: #F8F9FA;
        border-bottom: 1px solid #E5E8EB;
        font-size: 13px;
        font-weight: 600;
        color: #6B7684;
    }

    .data-table-row {
        display: grid;
        grid-template-columns: 1.5fr 1fr 1fr 1fr 1fr 0.8fr;
        padding: 16px 20px;
        border-bottom: 1px solid #F2F3F5;
        align-items: center;
        transition: background 0.15s ease;
    }

    .data-table-row:hover {
        background: #F8F9FA;
    }

    .data-table-row:last-child {
        border-bottom: none;
    }

    .table-stock-name {
        font-weight: 600;
        color: #191F28;
    }

    .table-date {
        color: #6B7684;
        font-size: 14px;
    }

    .table-price {
        font-weight: 500;
        color: #191F28;
    }

    .table-quantity {
        color: #6B7684;
    }

    .table-profit {
        font-weight: 600;
    }

    .table-profit.positive {
        color: #F04452;
    }

    .table-profit.negative {
        color: #3182F6;
    }

    /* 상태 뱃지 */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
    }

    .status-badge.buy {
        background: #E8F3FF;
        color: #3182F6;
    }

    .status-badge.sell {
        background: #FFEFEF;
        color: #F04452;
    }

    .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
    }

    .status-dot.buy {
        background: #3182F6;
    }

    .status-dot.sell {
        background: #F04452;
    }

    /* 섹션 타이틀 */
    .toss-section-title {
        font-size: 20px;
        font-weight: 700;
        color: #191F28;
        margin: 24px 0 16px 0;
    }

    /* 뱃지 */
    .toss-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }

    .toss-badge.buy {
        background: #E8F3FF;
        color: #3182F6;
    }

    .toss-badge.sell {
        background: #FFEFEF;
        color: #F04452;
    }

    /* 버튼 스타일 개선 */
    .stButton > button {
        border-radius: 12px;
        font-weight: 600;
        padding: 12px 24px;
        border: none;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(49, 130, 246, 0.3);
    }

    /* 입력 필드 - 테두리 없음, 흰색 배경 */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 12px;
        border: none !important;
        padding: 12px 16px;
        background: #FFFFFF !important;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border: none !important;
        box-shadow: none !important;
        background: #FFFFFF !important;
    }

    /* 셀렉트박스 - 테두리 없음, 흰색 배경 */
    .stSelectbox > div > div,
    [data-baseweb="select"] > div {
        border: none !important;
        background: #FFFFFF !important;
        border-radius: 12px !important;
    }

    [data-baseweb="select"] > div:focus-within {
        border: none !important;
        box-shadow: none !important;
        background: #FFFFFF !important;
    }

    /* 날짜 입력 - 테두리 없음, 흰색 배경 */
    .stDateInput > div > div > input {
        border: none !important;
        background: #FFFFFF !important;
        border-radius: 12px !important;
        padding: 12px 16px;
    }

    .stDateInput > div > div {
        border: none !important;
        background: #FFFFFF !important;
        border-radius: 12px !important;
    }

    /* 라디오 버튼 컨테이너 */
    .stRadio > div {
        background: transparent !important;
    }

    /* 메트릭 카드 */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }

    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid #E5E8EB;
    }

    /* 사이드바 토글 버튼 숨기기 */
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        font-size: 14px;
    }

    /* ===== LNB 애니메이션 완전 제거 ===== */
    /* 모든 사이드바 내부 요소에서 transition 제거 */
    [data-testid="stSidebar"] *,
    [data-testid="stSidebarNav"] *,
    [data-testid="stSidebarNav"] *::before,
    [data-testid="stSidebarNav"] *::after {
        transition: none !important;
        animation: none !important;
        -webkit-transition: none !important;
        -moz-transition: none !important;
        -o-transition: none !important;
    }

    /* Streamlit 사이드바 네비게이션 - 전체 스타일 */
    [data-testid="stSidebarNav"] {
        padding: 0 !important;
        background: transparent !important;
    }

    [data-testid="stSidebarNav"] ul {
        padding: 0 8px !important;
    }

    /* 모든 li 항목 고정 높이 */
    [data-testid="stSidebarNav"] li {
        margin: 2px 0 !important;
        height: 44px !important;
        min-height: 44px !important;
        max-height: 44px !important;
        overflow: hidden !important;
    }

    /* li 내부의 모든 div 고정 높이 */
    [data-testid="stSidebarNav"] li > div,
    [data-testid="stSidebarNav"] li > div > div,
    [data-testid="stSidebarNav"] li div {
        height: 44px !important;
        min-height: 44px !important;
        max-height: 44px !important;
        overflow: hidden !important;
        border-radius: 10px !important;
    }

    /* 일반 상태 (선택 안됨) */
    [data-testid="stSidebarNav"] li a {
        padding: 12px 16px !important;
        border-radius: 10px !important;
        color: #6B7684 !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        text-decoration: none !important;
        background: transparent !important;
        height: 44px !important;
        min-height: 44px !important;
        max-height: 44px !important;
        display: flex !important;
        align-items: center !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }

    [data-testid="stSidebarNav"] li a:hover {
        background: #F2F4F6 !important;
        color: #191F28 !important;
    }

    /* 선택된 상태 - 파란색 강조 */
    [data-testid="stSidebarNav"] li a[aria-current="page"],
    [data-testid="stSidebarNav"] li a[aria-selected="true"],
    [data-testid="stSidebarNav"] li[aria-selected="true"] a {
        background: #E8F3FF !important;
        color: #3182F6 !important;
        font-weight: 600 !important;
        border-left: 3px solid #3182F6 !important;
    }

    /* 메인 컨텐츠 상단 여백 - Home 텍스트와 라인 맞춤 */
    .main .block-container {
        padding-top: 1rem !important;
    }

    [data-testid="stAppViewBlockContainer"] {
        padding-top: 1rem !important;
    }

    /* 메인 헤더 영역 위치 조정 */
    .main .block-container > div:first-child {
        margin-top: 0 !important;
    }

    /* 아이콘 스타일 - 파일명에 이모지 포함 */
    [data-testid="stSidebarNav"] li a span {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }

    /* 첫번째 메뉴(app)를 Home으로 표시 */
    [data-testid="stSidebarNav"] li:first-child a span {
        font-size: 0 !important;
    }

    [data-testid="stSidebarNav"] li:first-child a span::before {
        content: "🏠 Home";
        font-size: 14px !important;
    }

    /* 사이드바 헤더 영역 */
    .sidebar-header {
        padding: 20px 16px;
        border-bottom: 1px solid #E5E8EB;
        margin-bottom: 8px;
    }

    .sidebar-header h2 {
        font-size: 18px;
        font-weight: 700;
        color: #191F28;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* 사이드바 섹션 라벨 */
    .sidebar-section-label {
        font-size: 11px;
        font-weight: 600;
        color: #8B95A1;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 16px 16px 8px 16px;
    }

    /* Expander 스타일 */
    .streamlit-expanderHeader {
        background: #FFFFFF;
        border-radius: 12px;
        border: 1px solid #F2F3F5;
    }

    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
    }

    /* 숨기기: Streamlit 기본 요소 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 반응형 */
    @media (max-width: 768px) {
        .toss-card-value {
            font-size: 24px;
        }
        .summary-card-value {
            font-size: 20px;
        }
        .data-table-header,
        .data-table-row {
            grid-template-columns: 1fr 1fr 1fr;
            font-size: 12px;
        }
    }
</style>
"""

def apply_toss_style():
    """토스 스타일 CSS 적용"""
    st.markdown(TOSS_CSS, unsafe_allow_html=True)

def toss_card(title: str, value: str, value_type: str = "neutral"):
    """토스 스타일 카드 컴포넌트

    Args:
        title: 카드 제목
        value: 표시할 값
        value_type: "positive", "negative", "neutral"
    """
    value_class = value_type if value_type in ["positive", "negative"] else ""

    st.markdown(f"""
    <div class="toss-card">
        <div class="toss-card-title">{title}</div>
        <div class="toss-card-value {value_class}">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def toss_list_item(title: str, subtitle: str, amount: str, change: str = "", amount_type: str = "neutral"):
    """토스 스타일 리스트 아이템

    Args:
        title: 메인 제목
        subtitle: 서브 텍스트
        amount: 금액
        change: 변동률
        amount_type: "positive", "negative", "neutral"
    """
    amount_class = amount_type if amount_type in ["positive", "negative"] else ""

    st.markdown(f"""
    <div class="toss-list-item">
        <div class="toss-list-left">
            <div class="toss-list-title">{title}</div>
            <div class="toss-list-subtitle">{subtitle}</div>
        </div>
        <div class="toss-list-right">
            <div class="toss-list-amount {amount_class}">{amount}</div>
            <div class="toss-list-change">{change}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def toss_section_title(title: str):
    """토스 스타일 섹션 타이틀"""
    st.markdown(f'<div class="toss-section-title">{title}</div>', unsafe_allow_html=True)

def toss_badge(text: str, badge_type: str = "buy"):
    """토스 스타일 뱃지

    Args:
        text: 뱃지 텍스트
        badge_type: "buy" 또는 "sell"
    """
    return f'<span class="toss-badge {badge_type}">{text}</span>'


def summary_card(icon: str, value: str, label: str, icon_color: str = "blue", value_type: str = "neutral"):
    """상단 요약 카드

    Args:
        icon: 이모지 아이콘
        value: 표시할 값
        label: 라벨
        icon_color: "blue", "red", "green"
        value_type: "positive", "negative", "neutral"
    """
    value_class = value_type if value_type in ["positive", "negative"] else ""

    st.markdown(f"""
    <div class="summary-card">
        <div class="summary-card-icon {icon_color}">{icon}</div>
        <div class="summary-card-value {value_class}">{value}</div>
        <div class="summary-card-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def status_badge(text: str, badge_type: str = "buy"):
    """상태 뱃지 (점 포함)

    Args:
        text: 뱃지 텍스트
        badge_type: "buy" 또는 "sell"
    """
    return f'''<span class="status-badge {badge_type}">
        <span class="status-dot {badge_type}"></span>
        {text}
    </span>'''


def data_table_header():
    """테이블 헤더"""
    st.markdown("""
    <div class="data-table-header">
        <div>종목명</div>
        <div>거래일</div>
        <div>거래가</div>
        <div>수량</div>
        <div>손익</div>
        <div>유형</div>
    </div>
    """, unsafe_allow_html=True)


def data_table_row(stock_name: str, trade_date: str, price: str, quantity: str,
                   profit: str, trade_type: str, profit_type: str = "neutral"):
    """테이블 행

    Args:
        stock_name: 종목명
        trade_date: 거래일
        price: 거래가
        quantity: 수량
        profit: 손익
        trade_type: "buy" 또는 "sell"
        profit_type: "positive", "negative", "neutral"
    """
    profit_class = profit_type if profit_type in ["positive", "negative"] else ""
    badge = status_badge("매수" if trade_type == "buy" else "매도", trade_type)

    st.markdown(f"""
    <div class="data-table-row">
        <div class="table-stock-name">{stock_name}</div>
        <div class="table-date">{trade_date}</div>
        <div class="table-price">{price}</div>
        <div class="table-quantity">{quantity}</div>
        <div class="table-profit {profit_class}">{profit}</div>
        <div>{badge}</div>
    </div>
    """, unsafe_allow_html=True)
