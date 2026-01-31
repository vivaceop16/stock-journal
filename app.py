"""
주식 매매일지 웹 앱 - 메인 애플리케이션
"""

import streamlit as st
from database import init_db
from styles import (
    apply_toss_style, toss_card, summary_card, data_table_header, data_table_row
)

# 페이지 설정
st.set_page_config(
    page_title="Home",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
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
    st.markdown("""
    <div style="padding: 16px 8px 24px 8px; border-bottom: 1px solid #E5E8EB; margin-bottom: 16px;">
        <h2 style="font-size: 18px; font-weight: 700; color: #191F28; margin: 0;">📈 매매일지</h2>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="padding: 0 8px;">
        <p style="font-size: 12px; color: #8B95A1; margin-bottom: 8px;">설정</p>
    </div>
    """, unsafe_allow_html=True)

    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = ''

    api_key = st.text_input(
        "OpenAI API Key",
        value=st.session_state.openai_api_key,
        type="password",
        help="AI 분석에 필요합니다"
    )

    if api_key != st.session_state.openai_api_key:
        st.session_state.openai_api_key = api_key
        import os
        os.environ['OPENAI_API_KEY'] = api_key

# 메인 콘텐츠
st.markdown("""
<div style="padding: 10px 0 20px 0;">
    <h1 style="font-size: 26px; font-weight: 700; color: #191F28; margin: 0;">
        대시보드
    </h1>
    <p style="font-size: 14px; color: #8B95A1; margin-top: 6px;">
        나의 투자 현황을 한눈에 확인하세요
    </p>
</div>
""", unsafe_allow_html=True)

# 서비스 초기화 및 데이터 로드
try:
    from services import TradeService
    from datetime import date

    trade_service = TradeService()

    # 전체 데이터 가져오기
    all_trades = trade_service.list_trades(limit=1000)

    # 이번 달 데이터 계산
    today = date.today()
    first_day = today.replace(day=1)
    month_trades = [t for t in all_trades if t.trade_date >= first_day]

    # 통계 계산
    # 총 구매액 (매수 건만)
    buy_trades = [t for t in all_trades if t.trade_type == "BUY"]
    total_invested = sum(float(t.price) * t.quantity for t in buy_trades)

    # 실현 손익 (완료된 매매)
    completed = [t for t in all_trades if t.profit_rate is not None]
    total_profit = sum(float(t.profit_loss or 0) for t in completed)

    # 수익률 계산
    profit_rate = (total_profit / total_invested * 100) if total_invested > 0 else 0

    # 승률
    win_trades = [t for t in completed if t.profit_loss and t.profit_loss > 0]
    win_rate = (len(win_trades) / len(completed) * 100) if completed else 0

    # 상단 요약 카드
    st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        summary_card("💰", f"{total_invested:,.0f}원", "총 구매액", "blue")

    with col2:
        profit_type = "positive" if total_profit > 0 else "negative" if total_profit < 0 else "neutral"
        profit_sign = "+" if total_profit > 0 else ""
        summary_card("📊", f"{profit_sign}{total_profit:,.0f}원", "실현 손익", "red" if total_profit >= 0 else "blue", profit_type)

    with col3:
        rate_type = "positive" if profit_rate > 0 else "negative" if profit_rate < 0 else "neutral"
        rate_sign = "+" if profit_rate > 0 else ""
        summary_card("📈", f"{rate_sign}{profit_rate:.2f}%", "총 수익률", "green", rate_type)

    with col4:
        summary_card("🎯", f"{win_rate:.1f}%", "승률", "blue")

    # 최근 거래 테이블
    st.markdown("<div style='height: 32px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <h2 style="font-size: 18px; font-weight: 700; color: #191F28; margin: 0;">최근 거래</h2>
        <span style="font-size: 13px; color: #8B95A1;">전체 {0}건</span>
    </div>
    """.format(len(all_trades)), unsafe_allow_html=True)

    recent_trades = trade_service.list_trades(limit=10)

    if recent_trades:
        # 테이블 시작
        st.markdown('<div class="data-table">', unsafe_allow_html=True)
        data_table_header()

        for trade in recent_trades:
            trade_type = "buy" if trade.trade_type == "BUY" else "sell"

            # 수익률/손익 표시
            if trade.profit_rate is not None:
                rate = float(trade.profit_rate)
                profit_loss = float(trade.profit_loss or 0)
                rate_sign = "+" if rate > 0 else ""
                profit_str = f"{rate_sign}{profit_loss:,.0f}원"
                profit_type = "positive" if rate > 0 else "negative"
            else:
                profit_str = "-"
                profit_type = "neutral"

            data_table_row(
                stock_name=trade.stock_name,
                trade_date=str(trade.trade_date),
                price=f"{float(trade.price):,.0f}원",
                quantity=f"{trade.quantity}주",
                profit=profit_str,
                trade_type=trade_type,
                profit_type=profit_type
            )

        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="toss-card" style="text-align: center; padding: 60px 20px;">
            <div style="font-size: 48px; margin-bottom: 16px;">📝</div>
            <div style="font-size: 16px; color: #191F28; font-weight: 600; margin-bottom: 8px;">
                아직 매매 기록이 없어요
            </div>
            <div style="font-size: 14px; color: #8B95A1;">
                왼쪽 메뉴에서 '매매입력'을 눌러 첫 거래를 기록해보세요
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 이번 달 요약
    st.markdown("<div style='height: 32px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <h2 style="font-size: 18px; font-weight: 700; color: #191F28; margin-bottom: 16px;">이번 달 요약</h2>
    """, unsafe_allow_html=True)

    month_col1, month_col2, month_col3 = st.columns(3)

    month_completed = [t for t in month_trades if t.profit_rate is not None]
    month_profit = sum(float(t.profit_loss or 0) for t in month_completed)
    month_win = [t for t in month_completed if t.profit_loss and t.profit_loss > 0]
    month_win_rate = (len(month_win) / len(month_completed) * 100) if month_completed else 0

    with month_col1:
        profit_type = "positive" if month_profit > 0 else "negative" if month_profit < 0 else "neutral"
        profit_sign = "+" if month_profit > 0 else ""
        toss_card("이번 달 수익", f"{profit_sign}{month_profit:,.0f}원", profit_type)

    with month_col2:
        toss_card("거래 횟수", f"{len(month_trades)}건")

    with month_col3:
        rate_type = "positive" if month_win_rate >= 50 else "negative"
        toss_card("승률", f"{month_win_rate:.1f}%", rate_type if month_completed else "neutral")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")

# 푸터
st.markdown("""
<div style="text-align: center; padding: 40px 0 20px 0; color: #8B95A1; font-size: 13px;">
    꾸준한 기록이 실력이 됩니다
</div>
""", unsafe_allow_html=True)
