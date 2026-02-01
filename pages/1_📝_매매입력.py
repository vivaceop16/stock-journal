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
    saved_count = st.session_state.get('saved_count', 1)
    st.success(f"✅ {saved_count}건의 매매가 저장되었습니다!")
    del st.session_state['trade_saved']
    if 'saved_count' in st.session_state:
        del st.session_state['saved_count']

# 폼 리셋을 위한 카운터
if 'form_key' not in st.session_state:
    st.session_state.form_key = 0

# 거래 항목 리스트 (여러 가격/수량 입력용) - 기본 3개
if 'trade_entries' not in st.session_state or len(st.session_state.trade_entries) < 3:
    st.session_state.trade_entries = [{'price': 0, 'quantity': 0}, {'price': 0, 'quantity': 0}, {'price': 0, 'quantity': 0}]

# 기존 종목명 목록 가져오기
existing_stocks = trade_service.get_stock_names()

# 기본 정보
st.markdown('<p style="font-weight: 600; color: #191F28; margin-bottom: 16px;">기본 정보</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    # 종목명/종목코드 통합 입력
    if existing_stocks:
        stock_options = ["➕ 새 종목 입력"] + existing_stocks
        selected_stock = st.selectbox(
            "종목명/종목코드 *",
            options=stock_options,
            index=0,
            key=f"stock_select_{st.session_state.form_key}"
        )
        if selected_stock == "➕ 새 종목 입력":
            stock_input = st.text_input(
                "종목명 또는 종목코드",
                placeholder="예: 삼성전자 또는 005930",
                label_visibility="collapsed",
                key=f"stock_input_{st.session_state.form_key}"
            )
        else:
            stock_input = selected_stock
    else:
        stock_input = st.text_input(
            "종목명/종목코드 *",
            placeholder="예: 삼성전자 또는 005930",
            key=f"stock_input_{st.session_state.form_key}"
        )

with col2:
    trade_date = st.date_input(
        "거래일 *",
        value=date.today(),
        key=f"trade_date_{st.session_state.form_key}"
    )

# 거래 유형
trade_type = st.radio(
    "거래유형 *",
    options=["BUY", "SELL"],
    format_func=lambda x: "🔵 매수" if x == "BUY" else "🔴 매도",
    horizontal=True,
    key=f"trade_type_{st.session_state.form_key}"
)

# 거래 상세
st.markdown('<p style="font-weight: 600; color: #191F28; margin: 24px 0 16px 0;">거래 상세</p>', unsafe_allow_html=True)

# 각 거래 항목 입력
entry_prices = []
entry_quantities = []
total_amount = 0

for i, entry in enumerate(st.session_state.trade_entries):
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        price = st.number_input(
            f"거래가격 (원)",
            min_value=0,
            step=100,
            key=f"price_{i}_{st.session_state.form_key}",
            label_visibility="visible" if i == 0 else "collapsed"
        )
        entry_prices.append(price)
    with col2:
        quantity = st.number_input(
            f"수량 (주)",
            min_value=0,
            step=1,
            key=f"quantity_{i}_{st.session_state.form_key}",
            label_visibility="visible" if i == 0 else "collapsed"
        )
        entry_quantities.append(quantity)
    with col3:
        if price > 0 and quantity > 0:
            subtotal = price * quantity
            total_amount += subtotal
            st.markdown(f"<div style='padding-top: {'28px' if i == 0 else '8px'}; color: #6B7684; font-size: 14px;'>{subtotal:,.0f}원</div>", unsafe_allow_html=True)

# 거래 추가/삭제 버튼 (작게, 붙여서)
btn_col1, btn_col2, btn_col3 = st.columns([0.15, 0.15, 0.7])
with btn_col1:
    if st.button("➕ 추가", key=f"add_entry_{st.session_state.form_key}"):
        st.session_state.trade_entries.append({'price': 0, 'quantity': 0})
        st.rerun()
with btn_col2:
    if len(st.session_state.trade_entries) > 1:
        if st.button("➖ 삭제", key=f"remove_entry_{st.session_state.form_key}"):
            st.session_state.trade_entries.pop()
            st.rerun()

# 총 거래금액 표시
if total_amount > 0:
    entry_count = len([p for i, p in enumerate(entry_prices) if p > 0 and entry_quantities[i] > 0])
    st.markdown(f"""
    <div style="background: #F8F9FA; border-radius: 8px; padding: 12px 16px; margin: 8px 0;">
        <span style="color: #8B95A1; font-size: 13px;">총 거래금액 ({entry_count}건)</span>
        <span style="color: #191F28; font-weight: 700; font-size: 18px; margin-left: 12px;">{total_amount:,.0f}원</span>
    </div>
    """, unsafe_allow_html=True)

# 영어는 대문자로 변환, 종목명 결정
stock_name = stock_input.upper() if stock_input and stock_input.isascii() else stock_input

# 매도인 경우 자동 연결 정보 표시
if trade_type == "SELL" and stock_name and entry_prices[0] > 0:
    unlinked_buys = trade_service.get_unlinked_buys(stock_name)

    if unlinked_buys:
        oldest_buy = unlinked_buys[0]
        profit_rate = ((entry_prices[0] - float(oldest_buy.price)) / float(oldest_buy.price)) * 100
        profit_loss = (entry_prices[0] - float(oldest_buy.price)) * entry_quantities[0]

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
    label_visibility="collapsed",
    key=f"trade_reason_{st.session_state.form_key}"
)

# 확신도
st.markdown('<p style="font-weight: 600; color: #191F28; margin: 24px 0 12px 0;">매매 확신도</p>', unsafe_allow_html=True)
confidence_score = st.radio(
    "확신도",
    options=[1, 2, 3, 4, 5],
    format_func=lambda x: ["⚪ 매우 낮음", "🔵 낮음", "🟢 보통", "🟡 높음", "🔴 매우 높음"][x-1],
    horizontal=True,
    index=2,
    label_visibility="collapsed",
    key=f"confidence_{st.session_state.form_key}"
)

st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

# 저장 버튼
if st.button("저장하기", use_container_width=True, type="primary", key=f"submit_{st.session_state.form_key}"):
    errors = []
    if not stock_name:
        errors.append("종목명을 입력해주세요")

    # 유효한 거래 항목 확인 (가격 > 0, 수량 > 0)
    valid_entries = [(p, q) for p, q in zip(entry_prices, entry_quantities) if p > 0 and q > 0]
    if not valid_entries:
        errors.append("거래가격과 수량을 입력해주세요")
    if not trade_reason:
        errors.append("매매 근거를 입력해주세요")

    if errors:
        for error in errors:
            st.error(f"❌ {error}")
    else:
        try:
            score_mapping = {1: 2, 2: 4, 3: 5, 4: 7, 5: 9}
            mapped_score = score_mapping[confidence_score]

            saved_count = 0
            for price, quantity in valid_entries:
                # 매도인 경우 자동으로 가장 오래된 미연결 매수와 연결
                linked_trade_id = None
                if trade_type == "SELL":
                    unlinked_buys = trade_service.get_unlinked_buys(stock_name)
                    if unlinked_buys:
                        linked_trade_id = unlinked_buys[0].id

                trade_data = {
                    'stock_name': stock_name,
                    'stock_code': None,  # 종목코드는 종목명에 통합
                    'trade_date': trade_date,
                    'trade_type': trade_type,
                    'price': price,
                    'quantity': quantity,
                    'trade_reason': trade_reason,
                    'confidence_score': mapped_score,
                    'linked_trade_id': linked_trade_id
                }

                trade_service.create_trade(trade_data)
                saved_count += 1

            st.session_state['trade_saved'] = True
            st.session_state['saved_count'] = saved_count
            st.session_state.form_key += 1
            st.session_state.trade_entries = [{'price': 0, 'quantity': 0}, {'price': 0, 'quantity': 0}, {'price': 0, 'quantity': 0}]  # 리셋
            st.rerun()

        except Exception as e:
            st.error(f"저장 중 오류가 발생했습니다: {e}")
