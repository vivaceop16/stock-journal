"""
매매 입력 페이지
"""

import streamlit as st
from datetime import date
from decimal import Decimal

from database import init_db
from services import TradeService
from styles import apply_toss_style

# 페이지 설정
st.set_page_config(page_title="매매 입력", page_icon="📝", layout="wide")

# 토스 스타일 적용
apply_toss_style()

# 데이터베이스 초기화
init_db()

# 서비스 초기화
trade_service = TradeService()

# 헤더
st.markdown("""
<div style="padding: 20px 0 24px 0;">
    <h1 style="font-size: 24px; font-weight: 700; color: #191F28; margin: 0;">
        매매 입력
    </h1>
    <p style="font-size: 14px; color: #8B95A1; margin-top: 6px;">
        새로운 거래를 기록해요
    </p>
</div>
""", unsafe_allow_html=True)

# 저장 성공 메시지 표시
if st.session_state.get('trade_saved'):
    st.success("✅ 매매가 저장되었습니다!")
    del st.session_state['trade_saved']

# 폼 리셋을 위한 카운터
if 'form_key' not in st.session_state:
    st.session_state.form_key = 0

# 입력 폼 (key가 변경되면 폼이 리셋됨)
with st.form(f"trade_form_{st.session_state.form_key}"):
    # 기본 정보
    st.markdown('<p style="font-weight: 600; color: #191F28; margin-bottom: 16px;">기본 정보</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        stock_name = st.text_input(
            "종목명 *",
            placeholder="예: 삼성전자"
        )

    with col2:
        trade_date = st.date_input(
            "거래일 *",
            value=date.today()
        )

    # 거래 유형 - 라디오 버튼
    st.markdown('<p style="font-weight: 600; color: #191F28; margin: 24px 0 12px 0;">거래 유형 *</p>', unsafe_allow_html=True)
    trade_type = st.radio(
        "거래 유형",
        options=["BUY", "SELL"],
        format_func=lambda x: "🔵 매수" if x == "BUY" else "🔴 매도",
        horizontal=True,
        label_visibility="collapsed"
    )

    # 거래 상세
    st.markdown('<p style="font-weight: 600; color: #191F28; margin: 24px 0 16px 0;">거래 상세</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        price = st.number_input(
            "거래가격 (원) *",
            min_value=0,
            step=100
        )

    with col2:
        quantity = st.number_input(
            "수량 (주) *",
            min_value=1,
            step=1
        )

    with col3:
        stock_code = st.text_input(
            "종목코드 (선택)",
            placeholder="예: 005930"
        )

    # 총 거래금액 표시
    if price > 0 and quantity > 0:
        total = price * quantity
        st.markdown(f"""
        <div style="background: #F8F9FA; border-radius: 8px; padding: 12px 16px; margin: 8px 0;">
            <span style="color: #8B95A1; font-size: 13px;">총 거래금액</span>
            <span style="color: #191F28; font-weight: 700; font-size: 18px; margin-left: 12px;">{total:,.0f}원</span>
        </div>
        """, unsafe_allow_html=True)

    # 매도인 경우 자동 연결 정보 표시
    if trade_type == "SELL" and stock_name and price > 0:
        unlinked_buys = trade_service.get_unlinked_buys(stock_name)

        if unlinked_buys:
            # 가장 오래된 매수 건 (자동 연결 대상)
            oldest_buy = unlinked_buys[0]
            profit_rate = ((price - float(oldest_buy.price)) / float(oldest_buy.price)) * 100
            profit_loss = (price - float(oldest_buy.price)) * quantity

            color = "#F04452" if profit_rate >= 0 else "#3182F6"
            sign = "+" if profit_rate >= 0 else ""
            st.markdown(f"""
            <div style="background: {'#FFF5F5' if profit_rate >= 0 else '#F0F6FF'}; border-radius: 8px; padding: 12px 16px; margin: 8px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="color: #8B95A1; font-size: 12px; margin-bottom: 4px;">자동 연결 매수</div>
                        <div style="color: #191F28; font-size: 14px; font-weight: 600;">{oldest_buy.trade_date} · {float(oldest_buy.price):,.0f}원 × {oldest_buy.quantity}주</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: #8B95A1; font-size: 12px; margin-bottom: 4px;">예상 수익</div>
                        <div style="color: {color}; font-weight: 700; font-size: 16px;">{sign}{profit_rate:.2f}% ({profit_loss:+,.0f}원)</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #F7F8FA; border-radius: 8px; padding: 12px 16px; margin: 8px 0;">
                <span style="color: #8B95A1; font-size: 13px;">💡 연결 가능한 매수 기록이 없어 단독 매도로 기록됩니다</span>
            </div>
            """, unsafe_allow_html=True)

    # 매매 근거
    st.markdown('<p style="font-weight: 600; color: #191F28; margin: 24px 0 16px 0;">매매 근거</p>', unsafe_allow_html=True)

    trade_reason = st.text_area(
        "매매 근거 *",
        height=120,
        placeholder="이 매매를 결정한 이유를 작성해주세요",
        label_visibility="collapsed"
    )

    # 확신도 - 라디오 버튼
    st.markdown('<p style="font-weight: 600; color: #191F28; margin: 24px 0 12px 0;">매매 확신도 *</p>', unsafe_allow_html=True)
    confidence_score = st.radio(
        "확신도",
        options=[1, 2, 3, 4, 5],
        format_func=lambda x: ["⚪ 매우 낮음", "🔵 낮음", "🟢 보통", "🟡 높음", "🔴 매우 높음"][x-1],
        horizontal=True,
        index=2,
        label_visibility="collapsed"
    )

    st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

    submitted = st.form_submit_button("저장하기", use_container_width=True, type="primary")

    if submitted:
        errors = []
        if not stock_name:
            errors.append("종목명을 입력해주세요")
        if price <= 0:
            errors.append("거래가격을 입력해주세요")
        if quantity <= 0:
            errors.append("수량을 입력해주세요")
        if not trade_reason:
            errors.append("매매 근거를 입력해주세요")

        if errors:
            for error in errors:
                st.error(f"❌ {error}")
        else:
            try:
                score_mapping = {1: 2, 2: 4, 3: 5, 4: 7, 5: 9}
                mapped_score = score_mapping[confidence_score]

                # 매도인 경우 자동으로 가장 오래된 미연결 매수와 연결
                linked_trade_id = None
                if trade_type == "SELL":
                    unlinked_buys = trade_service.get_unlinked_buys(stock_name)
                    if unlinked_buys:
                        linked_trade_id = unlinked_buys[0].id  # 가장 오래된 매수

                trade_data = {
                    'stock_name': stock_name,
                    'stock_code': stock_code if stock_code else None,
                    'trade_date': trade_date,
                    'trade_type': trade_type,
                    'price': price,
                    'quantity': quantity,
                    'trade_reason': trade_reason,
                    'confidence_score': mapped_score,
                    'linked_trade_id': linked_trade_id
                }

                trade = trade_service.create_trade(trade_data)
                st.session_state['trade_saved'] = True
                st.session_state.form_key += 1  # 폼 리셋
                st.rerun()

            except Exception as e:
                st.error(f"저장 중 오류가 발생했습니다: {e}")
