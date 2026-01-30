"""
주식 매매일지 웹 앱 - 메인 애플리케이션
"""

import streamlit as st
from database import init_db, db_manager
from styles import apply_toss_style, toss_card, toss_list_item, toss_section_title, toss_badge

# 페이지 설정
st.set_page_config(
    page_title="주식 매매일지",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 토스 스타일 적용
apply_toss_style()

# 데이터베이스 초기화
@st.cache_resource
def initialize_database():
    init_db()
    return True

initialize_database()

# 사이드바 - API 키 설정
with st.sidebar:
    st.markdown("### ⚙️ 설정")

    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = ''

    api_key = st.text_input(
        "OpenAI API Key",
        value=st.session_state.openai_api_key,
        type="password",
        help="AI 분석 및 이미지 인식에 필요합니다"
    )

    if api_key != st.session_state.openai_api_key:
        st.session_state.openai_api_key = api_key
        import os
        os.environ['OPENAI_API_KEY'] = api_key

# 헤더
st.markdown("""
<div style="padding: 20px 0 10px 0;">
    <h1 style="font-size: 28px; font-weight: 700; color: #191F28; margin: 0;">
        내 투자 일지
    </h1>
    <p style="font-size: 15px; color: #8B95A1; margin-top: 8px;">
        매매를 기록하고, 실력을 키워요
    </p>
</div>
""", unsafe_allow_html=True)

# 서비스 초기화 및 데이터 로드
try:
    from services import TradeService
    from datetime import date, timedelta
    from decimal import Decimal

    trade_service = TradeService()

    # 이번 달 데이터 계산
    today = date.today()
    first_day = today.replace(day=1)
    all_trades = trade_service.list_trades(limit=1000)
    month_trades = [t for t in all_trades if t.trade_date >= first_day]

    # 완료된 매매 (수익률 있는 것)
    completed = [t for t in month_trades if t.profit_rate is not None]

    # 통계 계산
    total_profit = sum(float(t.profit_loss or 0) for t in completed)
    win_trades = [t for t in completed if t.profit_loss and t.profit_loss > 0]
    win_rate = (len(win_trades) / len(completed) * 100) if completed else 0

    # 요약 카드
    st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        profit_type = "positive" if total_profit > 0 else "negative" if total_profit < 0 else "neutral"
        profit_sign = "+" if total_profit > 0 else ""
        toss_card("이번 달 수익", f"{profit_sign}{total_profit:,.0f}원", profit_type)

    with col2:
        toss_card("거래 횟수", f"{len(month_trades)}건")

    with col3:
        rate_type = "positive" if win_rate >= 50 else "negative"
        toss_card("승률", f"{win_rate:.1f}%", rate_type if completed else "neutral")

    # 최근 거래
    toss_section_title("최근 거래")

    recent_trades = trade_service.list_trades(limit=5)

    if recent_trades:
        for trade in recent_trades:
            trade_type = "buy" if trade.trade_type == "BUY" else "sell"
            trade_type_kr = "매수" if trade.trade_type == "BUY" else "매도"
            badge = toss_badge(trade_type_kr, trade_type)

            # 수익률 표시
            if trade.profit_rate is not None:
                rate = float(trade.profit_rate)
                rate_sign = "+" if rate > 0 else ""
                change = f"{rate_sign}{rate:.2f}%"
                amount_type = "positive" if rate > 0 else "negative"
            else:
                change = ""
                amount_type = "neutral"

            toss_list_item(
                title=f"{badge} {trade.stock_name}",
                subtitle=f"{trade.trade_date} · {trade.quantity}주",
                amount=f"{float(trade.price):,.0f}원",
                change=change,
                amount_type=amount_type
            )
    else:
        st.markdown("""
        <div class="toss-card" style="text-align: center; padding: 40px;">
            <div style="font-size: 48px; margin-bottom: 16px;">📝</div>
            <div style="font-size: 16px; color: #191F28; font-weight: 600; margin-bottom: 8px;">
                아직 매매 기록이 없어요
            </div>
            <div style="font-size: 14px; color: #8B95A1;">
                왼쪽 메뉴에서 '매매입력'을 눌러 첫 거래를 기록해보세요
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 빠른 메뉴
    toss_section_title("바로가기")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="toss-card" style="cursor: pointer;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 24px;">📝</div>
                <div>
                    <div style="font-weight: 600; color: #191F28;">매매 입력</div>
                    <div style="font-size: 13px; color: #8B95A1;">새 거래 기록하기</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="toss-card" style="cursor: pointer;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 24px;">🤖</div>
                <div>
                    <div style="font-weight: 600; color: #191F28;">AI 분석</div>
                    <div style="font-size: 13px; color: #8B95A1;">매매 점수 확인</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="toss-card" style="cursor: pointer;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 24px;">📊</div>
                <div>
                    <div style="font-weight: 600; color: #191F28;">매매 목록</div>
                    <div style="font-size: 13px; color: #8B95A1;">전체 기록 보기</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="toss-card" style="cursor: pointer;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 24px;">📈</div>
                <div>
                    <div style="font-weight: 600; color: #191F28;">월간 리포트</div>
                    <div style="font-size: 13px; color: #8B95A1;">성과 분석</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")

# 푸터
st.markdown("""
<div style="text-align: center; padding: 40px 0 20px 0; color: #8B95A1; font-size: 13px;">
    꾸준한 기록이 실력이 됩니다
</div>
""", unsafe_allow_html=True)
