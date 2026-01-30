"""토스 스타일 UI 컴포넌트"""

import streamlit as st

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

    /* 입력 필드 */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 12px;
        border: 1px solid #E5E8EB;
        padding: 12px 16px;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #3182F6;
        box-shadow: 0 0 0 3px rgba(49, 130, 246, 0.1);
    }

    /* 메트릭 카드 */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }

    /* 사이드바 */
    [data-testid="stSidebar"] {
        background: #FFFFFF;
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
